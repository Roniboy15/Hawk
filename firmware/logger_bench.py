"""Explizite Bodenmessungen fuer CH3 und Flash, ohne IMU/Servoausgabe.

run_channel(): CH3-Rohpulse bis Ctrl+C, PIO danach schliessen und JSON sichern.
run_storage(): neue begrenzte Testdateien schreiben, flush/sync/close mitmessen,
Inhalt zuruecklesen, JSON sichern. Keine alten Dateien loeschen/ueberschreiben.
run_ram(): Probe-Puffer vor grossen Modulimports reservieren, danach denselben
Modulumfang/Reserve pruefen. Keine Hardware, JSON erst nach Pufferfreigabe.
Import startet nichts. Nie parallel mit app/bench_test/sensor_test ausfuehren.
Dies ist KEIN Fluglogger und seine Messung keine garantierte Echtzeitgrenze.
"""
import json
import gc
import os
import sys
import time
import config as cfg
from diagnostics import TimingStats
from ram_buffer import RecordBuffer

_running = False


def _settings():
    if cfg.AUTO_START is not False:
        raise ValueError('Logger-Bodenmessung braucht AUTO_START=False')
    s = dict(cfg.LOGGER_BENCH)
    for name, low, high in (('channel_pin', 0, 29), ('poll_us', 1000, 50000),
                            ('console_hz', 1, 10), ('case_bytes', 4096, 262144),
                            ('reserve_bytes', 32768, 1048576),
                            ('ram_record_bytes', 64, 512), ('ram_log_hz', 1, 10),
                            ('ram_target_seconds', 1, 3600), ('ram_event_records', 2, 256),
                            ('ram_reserve_bytes', 32768, 131072),
                            ('ram_records_per_block', 1, 64)):
        value = s[name]
        if type(value) is not int or not low <= value <= high:
            raise ValueError('Ungueltige LOGGER_BENCH-Einstellung: '+name)
    if s['ram_record_bytes'] * s['ram_records_per_block'] > 4096:
        raise ValueError('RAM-Probe erlaubt hoechstens 4096 Bytes pro Block')
    blocks = s['block_sizes']
    if (not isinstance(blocks, (tuple, list)) or not 1 <= len(blocks) <= 4 or
            len(set(blocks)) != len(blocks) or
            any(type(n) is not int or not 256 <= n <= 4096 or
                s['case_bytes'] % n for n in blocks)):
        raise ValueError('Ungueltige Flash-Testbloecke')
    pins = {cfg.SENSOR['sda'], cfg.SENSOR['scl'], cfg.GPS['tx'], cfg.GPS['rx'],
            cfg.BAROMETER['sda'], cfg.BAROMETER['scl'], 16}
    pins.update(s['pin'] for s in cfg.RECEIVER.values())
    pins.update(s['pin'] for s in cfg.SERVOS.values())
    if s['channel_pin'] in pins:
        raise ValueError('CH3-Testpin kollidiert mit bisheriger Hardware')
    return s


def _free_bytes(fs):
    value = fs.statvfs('.')
    return (value[1] or value[0]) * min(value[3], value[4])


def _stem(prefix, stamp, suffixes, fs):
    for index in range(10000):
        stem = '%s_%d_%d' % (prefix, stamp, index)
        occupied = False
        for suffix in suffixes:
            try:
                fs.stat(stem+suffix)
                occupied = True
            except OSError as error:
                if error.args[0] != 2:
                    raise
        if not occupied:
            return stem
    raise OSError('Keine freie Logger-Testlaufnummer')


def _metadata(kind, settings):
    return {'schema': 1, 'test_version': settings['version'], 'test': kind,
            'purpose': 'ground_logger_benchmark_no_pwm', 'control_loop_timing': False,
            'flight_timing_qualified': False, 'configuration': settings,
            # 0.1.0 hat diese Schwellen noch nicht mitgespeichert.
            'timing_thresholds': {'period_us': cfg.LOOP_US, 'deadline_us': cfg.MAX_LOOP_US},
            'runtime': {'version': sys.version,
                        'machine': getattr(sys.implementation, '_machine', '')}}


def _save_report(path, report, fs, open_file):
    with open_file(path, 'w') as file:
        json.dump(report, file)
    if hasattr(fs, 'sync'):
        fs.sync()


def _measure(stats, name, clock, action):
    started = clock.ticks_us()
    try:
        return action()
    finally:
        stats[name].add(clock.ticks_diff(clock.ticks_us(), started))


def _storage_run(settings, clock, fs, open_file):
    free = _free_bytes(fs)
    # Reserve fuer Dateisystem/JSON/Code, nicht einfach bis ENOSPC fuellen.
    needed = settings['case_bytes'] * len(settings['block_sizes'])
    if free < needed + settings['reserve_bytes']:
        raise ValueError('Zu wenig freier Flash fuer Testdateien plus Reserve')
    suffixes = ['_%d.bin' % n for n in settings['block_sizes']] + ['.json']
    stem = _stem('logger_storage', clock.ticks_ms(), suffixes, fs)
    report = _metadata('storage', settings)
    report.update(free_before_bytes=free, planned_data_bytes=needed,
                  sync_supported=hasattr(fs, 'sync'), cases=[], stop_reason='complete',
                  report_file=stem+'.json')
    print('Nur Boden/Servos aus: Flash-Test schreibt', needed, 'Bytes in neue Dateien')
    for size in settings['block_sizes']:
        stats = {name: TimingStats(cfg.LOOP_US, cfg.MAX_LOOP_US)
                 for name in ('open', 'write', 'flush', 'sync', 'cycle', 'close', 'sync_after_close')}
        case = {'file': stem+'_%d.bin' % size, 'block_bytes': size,
                'written_bytes': 0, 'completed_cycles': 0, 'verified': False, 'errors': []}
        report['cases'].append(case)
        file = None
        payload = bytes(n % 256 for n in range(size))
        try:
            file = _measure(stats, 'open', clock, lambda: open_file(case['file'], 'wb'))
            while case['written_bytes'] < settings['case_bytes']:
                begin = clock.ticks_us()
                try:
                    count = _measure(stats, 'write', clock, lambda: file.write(payload))
                    if count != size:
                        raise OSError('Unvollstaendiger Testdatei-Write')
                    case['written_bytes'] += count
                    _measure(stats, 'flush', clock, file.flush)
                    if hasattr(fs, 'sync'):
                        _measure(stats, 'sync', clock, fs.sync)
                    case['completed_cycles'] += 1
                finally:
                    stats['cycle'].add(clock.ticks_diff(clock.ticks_us(), begin))
        except KeyboardInterrupt:
            report['stop_reason'] = 'keyboard_interrupt'
        except Exception as error:
            case['errors'].append(type(error).__name__+': '+str(error)[:160])
            report['stop_reason'] = 'error'
        finally:
            if file is not None:
                try:
                    _measure(stats, 'close', clock, file.close)
                    if hasattr(fs, 'sync'):
                        _measure(stats, 'sync_after_close', clock, fs.sync)
                except BaseException as error:
                    case['errors'].append('close/sync: '+type(error).__name__+': '+str(error)[:160])
                    report['stop_reason'] = 'error'
            case['timing'] = {name: value.report() for name, value in stats.items()}
        if report['stop_reason'] == 'complete':
            try:
                with open_file(case['file'], 'rb') as check:
                    for _ in range(settings['case_bytes'] // size):
                        if check.read(size) != payload:
                            raise OSError('Testdatei stimmt beim Zuruecklesen nicht')
                    if check.read(1):
                        raise OSError('Unerwartete Restbytes in Testdatei')
                case['verified'] = True
            except KeyboardInterrupt:
                report['stop_reason'] = 'keyboard_interrupt'
            except Exception as error:
                case['errors'].append('verify: '+type(error).__name__+': '+str(error)[:160])
                report['stop_reason'] = 'error'
        if report['stop_reason'] != 'complete':
            break
    report['free_after_data_bytes'] = _free_bytes(fs)
    _save_report(report['report_file'], report, fs, open_file)
    print('Flash-Test beendet:', report['stop_reason'], '| Bericht:', report['report_file'])
    for case in report['cases']:
        print('Block', case['block_bytes'], 'verified=', case['verified'],
              'cycle max_us=', case['timing']['cycle']['max_us'],
              'close max_us=', case['timing']['close']['max_us'])
    return report


def run_storage():
    """Begrenzter Flashversuch, nie im Flug oder parallel zur Steuerung."""
    global _running
    settings = _settings()
    if _running:
        raise RuntimeError('Logger-Bodenmessung laeuft bereits')
    _running = True
    try:
        return _storage_run(settings, time, os, open)
    finally:
        _running = False


def _probe_records(buffer):
    # Alle Recordgrenzen mit unterschiedlichen Markern beschreiben, dann erst
    # zuruecklesen: deckt falsche Offsets/ueberlappende Slots zwischen Bloecken ab.
    # Kein finaler Flugencoder; nur zwei Testbytes je budgetiertem Record.
    for index in range(buffer.capacity):
        block, offset = buffer.slot(index)
        block[offset] = index % 256
        block[offset + buffer.record_bytes - 1] = (index // 256) % 256
    for index in range(buffer.capacity):
        block, offset = buffer.slot(index)
        if (block[offset] != index % 256 or
                block[offset + buffer.record_bytes - 1] != (index // 256) % 256):
            raise RuntimeError('RAM-Probeinhalt stimmt nicht')
    # Lokale Blockreferenzen verschwinden mit Rueckkehr, vor release/GC/Export.


def _ram_run(settings, clock, fs, open_file, memory, allocate=bytearray, heap_info=None,
             prepare=None):
    stem = _stem('logger_ram', clock.ticks_ms(), ('.json',), fs)
    samples = (settings['ram_target_seconds'] * settings['ram_log_hz'] +
               settings['ram_event_records'])
    needed = samples * settings['ram_record_bytes']
    reserve = settings['ram_reserve_bytes']
    per_block = settings['ram_records_per_block']
    report = _metadata('ram', settings)
    report.update(report_file=stem+'.json', status='insufficient_ram',
                  allocation_ok=False, record_format_implemented=False,
                  final_control_objects_allocated=False,
                  target_samples=samples, requested_bytes=needed, reserve_bytes=reserve,
                  storage_strategy='record_aligned_blocks', content_verified=False,
                  block_count=(samples + per_block - 1) // per_block,
                  max_block_bytes=min(samples, per_block) * settings['ram_record_bytes'],
                  # block_count ist das ZIEL, diese Zaehler der echte Fortschritt.
                  allocated_blocks=0, allocated_payload_bytes=0,
                  last_block_request_bytes=0, allocator_failed=False,
                  free_at_allocator_failure_bytes=None, error=None,
                  heap_info_available=heap_info is not None,
                  allocation_order='buffer_before_runtime_imports',
                  runtime_modules_imported=False,
                  runtime_modules_preloaded=[name for name in
                      ('app', 'gps', 'ms5611', 'sensor_test', 'recording') if name in sys.modules])
    def measured_allocate(size):
        report['last_block_request_bytes'] = size
        try:
            block = allocate(size)
        except MemoryError:
            # Vor RecordBuffer-Cleanup messen: sonst waeren Teilbloecke bereits
            # freigegeben und der entscheidende Speicherzustand verloren.
            report['allocator_failed'] = True
            report['free_at_allocator_failure_bytes'] = memory.mem_free()
            if heap_info is not None:
                print('L3 Heap BEIM Block-Allokationsfehler:')
                heap_info()
            raise
        report['allocated_blocks'] += 1
        report['allocated_payload_bytes'] += size
        return block
    memory.collect()
    if heap_info is not None:
        # mem_info() druckt die Heapzusammenfassung, ohne Datei oder Hardware.
        # Konsolenausgabe mit sichern; Rueckgabewert ist kein Messdatensatz.
        print('L3 Heap VOR Zielpuffer:')
        heap_info()
    free = memory.mem_free()
    report['free_before_bytes'] = free
    # Ausgangswert jetzt VOR den grossen Imports, nicht mit 0.1.3 vergleichen.
    # Keine Kapazitaetszusage aus diesem Zwischenstand ableiten.
    report['estimated_capacity_samples'] = max(0, (free-reserve)//settings['ram_record_bytes'])
    report['capacity_estimate_stage'] = 'before_runtime_imports'
    buffer = None
    phase = 'allocate'
    try:
        if free >= needed + reserve:
            try:
                # L3 0.1.3 scheitert am 36. Block trotz 79552 B Gesamtfreiraum.
                # Dauerpuffer deshalb frueh anlegen, bevor Import/Compiler den
                # Heap weiter fragmentieren. Spaeter dieselben Module laden;
                # erst danach Inhalt und verbleibende Reserve beurteilen.
                buffer = RecordBuffer(samples, settings['ram_record_bytes'], per_block,
                                      measured_allocate)
                phase = 'runtime_imports'
                if prepare is not None:
                    prepare()
                    report['runtime_modules_imported'] = True
                memory.collect()
                phase = 'verify'
                _probe_records(buffer)
                report['content_verified'] = True
                # Kurzlebige Slot-Tupel aus der Inhaltsprobe zaehlen nicht als
                # dauerhaft belegter Speicher; echte Bloecke bleiben referenziert.
                memory.collect()
                report['free_after_allocation_bytes'] = memory.mem_free()
                report['allocation_ok'] = True
                report['status'] = ('fits_preliminary' if report['free_after_allocation_bytes'] >= reserve
                                    else 'insufficient_reserve')
            except MemoryError as error:
                report['status'] = ('runtime_import_failed' if phase == 'runtime_imports' else
                                    'allocation_failed' if phase == 'allocate' else 'verification_failed')
                report['failure_phase'] = phase
                report['failure_location'] = ('block_allocator' if report['allocator_failed']
                                              else 'runtime_imports' if phase == 'runtime_imports'
                                              else 'buffer_setup_or_probe_runtime')
                report['error'] = str(error)[:160]
                # Die Quellzeile hilft insbesondere bei Fehlern vor dem ersten
                # Block (Klasse/Liste/Aufruf). Nur im separaten Bodenversuch.
                if hasattr(sys, 'print_exception'):
                    sys.print_exception(error)
            except KeyboardInterrupt:
                report['status'] = 'keyboard_interrupt'
                report['failure_phase'] = phase
            except Exception as error:
                report['status'] = 'runtime_import_failed' if phase == 'runtime_imports' else 'probe_failed'
                report['failure_phase'] = phase
                report['error'] = type(error).__name__ + ': ' + str(error)[:160]
    finally:
        if buffer is not None:
            buffer.release()
        buffer = None
        memory.collect()
    report['free_after_release_bytes'] = memory.mem_free()
    # Erst jetzt Flash: dies ist ein eigenstaendiger Bodenversuch ohne PWM.
    _save_report(report['report_file'], report, fs, open_file)
    print('RAM-Probe:', report['status'], '| vorher frei:', free,
          '| Puffer:', needed, '| Reserve:', reserve)
    print('Bloecke:', report['block_count'], '| groesster Block:', report['max_block_bytes'],
          '| nach Allokation frei:', report.get('free_after_allocation_bytes'))
    print('Modulumfang nach Puffer geladen:', report['runtime_modules_imported'],
          '| vorher bereits geladen:', report['runtime_modules_preloaded'])
    print('Tatsaechlich angelegt:', report['allocated_blocks'], 'Bloecke,',
          report['allocated_payload_bytes'], 'Nutzbytes | Fehler:', report['error'])
    print('RAM-Bericht gespeichert:', report['report_file'])
    return report


def _import_logger_modules():
    # Gleicher Modulumfang wie in 0.1.3, jetzt bei gehaltenem Puffer. Auch der
    # temporaere Compilerbedarf muss passen; kein I2C-/PIO-/PWM-Objekt entsteht.
    import app
    import gps
    import ms5611
    import sensor_test
    import recording


def run_ram():
    """L3: Soft-Reboot, USB allein/BEC aus. Reserviert vor grossen Modulimports."""
    global _running
    settings = _settings()
    if _running:
        raise RuntimeError('Logger-Bodenmessung laeuft bereits')
    _running = True
    try:
        from micropython import mem_info
        return _ram_run(settings, time, os, open, gc, heap_info=mem_info,
                        prepare=_import_logger_modules)
    finally:
        _running = False


def _receiver(settings):
    # Erst beim expliziten CH3-Test Hardware laden. Ein einzelner PIO-Eingang;
    # Receiver startet weder PWM noch IMU. Niemals gleichzeitig mit app benutzen.
    from receiver import Receiver
    return Receiver({'record': {'pin': settings['channel_pin']}}, ('record',),
                    cfg.RX_TIMEOUT_MS, max_poll_ms=(cfg.MAX_LOOP_US+999)//1000)


def _channel_run(settings, clock, fs, open_file, factory):
    stem = _stem('logger_channel', clock.ticks_ms(), ('.json',), fs)
    report = _metadata('channel', settings)
    report.update(pulse_min_us=None, pulse_max_us=None, pulse_last_us=None,
                  fresh_frames=0, report_file=stem+'.json', shutdown_ok=False)
    rx = None
    previous_sequence, printed = 0, None
    try:
        rx = factory(settings)
        print('CH3-Rohpulse an GP%d; Knueppel unten/oben halten, Ctrl+C beendet.' % settings['channel_pin'])
        while True:
            now = clock.ticks_ms()
            rx.poll(now)
            channel = rx.channels['record']
            fresh = rx.fresh('record', now)
            pulse = channel['pulse']
            if fresh and channel['sequence'] != previous_sequence:
                previous_sequence = channel['sequence']
                report['fresh_frames'] += 1
                report['pulse_last_us'] = pulse
                report['pulse_min_us'] = pulse if report['pulse_min_us'] is None else min(report['pulse_min_us'], pulse)
                report['pulse_max_us'] = pulse if report['pulse_max_us'] is None else max(report['pulse_max_us'], pulse)
            if printed is None or clock.ticks_diff(now, printed) >= 1000 // settings['console_hz']:
                print('CH3 pulse_us=', pulse if fresh else None,
                      'min/max=', report['pulse_min_us'], report['pulse_max_us'])
                printed = now
            clock.sleep_us(settings['poll_us'])
    except KeyboardInterrupt:
        report['stop_reason'] = 'keyboard_interrupt'
    finally:
        if rx is not None:
            rx.close()  # Bei unbestaetigtem PIO-Stop kein Flashexport.
            report['shutdown_ok'] = True
    _save_report(report['report_file'], report, fs, open_file)
    print('CH3-Test gespeichert:', report['report_file'])
    return report


def run_channel():
    """Empfaenger versorgt, alle Servos stromlos; Ende manuell mit Ctrl+C."""
    global _running
    settings = _settings()
    if _running:
        raise RuntimeError('Logger-Bodenmessung laeuft bereits')
    _running = True
    try:
        return _channel_run(settings, time, os, open, _receiver)
    finally:
        _running = False
