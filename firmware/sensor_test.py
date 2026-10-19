"""Expliziter GPS-/MS5611-Test ohne Receiver, PWM oder Flugregler.

run('gps'/'baro'/'both') wird vom Betreiber in der Thonny-Shell gestartet.
RAM-Ring und Laufstatistik werden erst nach Stop/Ende exportiert. Das ist
ein Funktionstest mit begrenztem Logrest, noch kein kompletter Fluglogger.
Beim blossen Import entstehen weder Hardwareobjekte noch Dateien.
"""
import json
import math
import os
import sys
import config as cfg
from diagnostics import TimingStats
from gps import GPS
from logger import RingLog
from ms5611 import MS5611, relative_altitude

_running = False


class SensorLog(RingLog):
    HEADER = ('ms,gps_valid,gga_valid,rmc_valid,utc,date,lat_deg,lon_deg,'
              'gps_alt_msl_m,ground_speed_ms,course_true_deg,course_usable,'
              'fix_quality,satellites,hdop,gga_age_ms,rmc_age_ms,baro_valid,'
              'pressure_pa,temperature_c,relative_height_m,baro_age_ms,d1,d2,period_us\n')


def validate_settings(profile, duration_s, save):
    """Vor Pin-/Bus-Konstruktion pruefen, insbesondere bestehende Steuerpins."""
    if profile not in ('gps', 'baro', 'both'):
        raise ValueError('Profil muss gps, baro oder both sein')
    if cfg.AUTO_START is not False:
        raise ValueError('Fuer Sensortests AUTO_START=False verwenden')
    if type(duration_s) not in (int, float) or not math.isfinite(duration_s) or not 1 <= duration_s <= 3600:
        raise ValueError('Testdauer muss 1..3600 Sekunden sein')
    if type(save) is not bool:
        raise ValueError('save muss True/False sein')
    def integer(value, low, high):
        if type(value) is not int or not low <= value <= high:
            raise ValueError('Ungueltige Sensor-Testkonfiguration')
    settings = cfg.SENSOR_TEST
    integer(settings['loop_us'], 1000, 100000)
    integer(settings['capacity'], 1, 500)
    integer(settings['log_hz'], 1, min(20, 1000000 // settings['loop_us']))
    integer(settings['console_hz'], 1, settings['log_hz'])
    integer(settings['reference_samples'], 1, 100)
    integer(settings['reference_warmup_ms'], 0, 60000)
    reserved = set((cfg.SENSOR['sda'], cfg.SENSOR['scl']))
    reserved.update(v['pin'] for v in cfg.RECEIVER.values())
    reserved.update(v['pin'] for v in cfg.SERVOS.values())
    pins = []
    if profile in ('gps', 'both'):
        settings = cfg.GPS
        integer(settings['uart'], 0, 1)
        integer(settings['baudrate'], 4800, 115200)
        integer(settings['max_read'], 1, 1024)
        integer(settings['rxbuf'], settings['max_read'], 8192)
        integer(settings['stale_ms'], 100, 10000)
        integer(settings['max_poll_ms'], 1, settings['stale_ms'] - 1)
        value = settings['course_min_speed_ms']
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise ValueError('Ungueltige GPS-Kursschwelle')
        pins.extend((settings['tx'], settings['rx']))
        pairs = (((0, 1), (12, 13), (16, 17), (28, 29)),
                 ((4, 5), (8, 9), (20, 21), (24, 25)))
        if (settings['tx'], settings['rx']) not in pairs[settings['uart']]:
            raise ValueError('GPS-Pins passen nicht zum RP2040-UART')
    if profile in ('baro', 'both'):
        settings = cfg.BAROMETER
        integer(settings['i2c'], 0, 1)
        integer(settings['freq'], 10000, 100000)
        integer(settings['sample_ms'], 20, 1000)
        integer(settings['sda'], 0, 29)
        integer(settings['scl'], 0, 29)
        if settings['address'] is not None and settings['address'] not in (0x76, 0x77):
            raise ValueError('Ungueltige Barometeradresse')
        pins.extend((settings['sda'], settings['scl']))
        if (settings['sda'] % 4 != settings['i2c'] * 2 or
                settings['scl'] != settings['sda'] + 1):
            raise ValueError('Barometerpins passen nicht zum RP2040-I2C-Bus')
        if settings['i2c'] == 0:
            raise ValueError('IMU nutzt I2C0; separaten I2C1 verwenden')
    for pin in pins:
        integer(pin, 0, 29)
        if pin in reserved or pin == 16:
            raise ValueError('Sensorpin kollidiert mit Steuerung/IMU/Board-LED')
    if len(set(pins)) != len(pins):
        raise ValueError('Neue Sensorpins duerfen sich nicht ueberlappen')


def _devices(profile, clock, resources):
    from machine import Pin, UART, I2C
    gps = baro = uart = None
    if profile in ('gps', 'both'):
        s = cfg.GPS
        uart = UART(s['uart'], baudrate=s['baudrate'], tx=Pin(s['tx']), rx=Pin(s['rx']),
                    bits=8, parity=None, stop=1, timeout=0, timeout_char=0,
                    rxbuf=s['rxbuf'])
        # Besitzer sofort registrieren: auch bei spaeterem PROM-/Startfehler schliessen.
        resources['uart'] = uart
        gps = GPS(uart, clock.ticks_diff, stale_ms=s['stale_ms'],
                  max_read=s['max_read'], rxbuf=s['rxbuf'], max_poll_ms=s['max_poll_ms'],
                  course_min_speed_ms=s['course_min_speed_ms'])
    if profile in ('baro', 'both'):
        s = cfg.BAROMETER
        bus = I2C(s['i2c'], sda=Pin(s['sda']), scl=Pin(s['scl']),
                  freq=s['freq'], timeout=10000)
        baro = MS5611(bus, address=s['address'], sample_ms=s['sample_ms'],
                      sleep_ms=clock.sleep_ms, ticks_diff=clock.ticks_diff,
                      ticks_ms=clock.ticks_ms)
    return gps, baro, uart


def _format(value, decimals=2):
    if value is None:
        return ''
    if type(value) is bool:
        return str(int(value))
    if type(value) is float:
        return ('%.' + str(decimals) + 'f') % value
    return str(value)


def csv_row(ms, gps, baro, period_us):
    values = [ms, gps.get('valid', False), gps.get('gga_valid', False),
              gps.get('rmc_valid', False), gps.get('utc', ''), gps.get('date', ''),
              _format(gps.get('lat'), 7), _format(gps.get('lon'), 7),
              gps.get('altitude_msl_m'), gps.get('speed_ms'), gps.get('course_deg'),
              gps.get('course_usable', False), gps.get('quality', 0),
              gps.get('satellites', 0), gps.get('hdop'), gps.get('gga_age_ms', -1),
              gps.get('rmc_age_ms', -1), baro['valid'], baro['pressure_pa'],
              baro['temperature_c'], baro['relative_height_m'], baro['age_ms'],
              baro['d1'], baro['d2'], period_us]
    return ','.join(_format(value) for value in values) + '\n'


def _free_stem(stamp):
    # Board-Ticks koennen nach Neustarts gleich sein. Nie einen alten Lauf ersetzen.
    for index in range(10000):
        stem = 'sensors_%d_%d' % (stamp, index)
        free = True
        for suffix in ('.csv', '.json'):
            try:
                os.stat(stem + suffix)
                free = False
            except OSError as error:
                if error.args[0] != 2:
                    raise
        if free:
            return stem
    raise OSError('Keine freie Sensor-Laufnummer')


def run(profile='both', duration_s=120, save=True):
    """Bedienereinstieg fuer Bodenfunktion; nicht gleichzeitig mit app.run()."""
    global _running
    validate_settings(profile, duration_s, save)
    if _running:
        raise RuntimeError('Sensor-Test laeuft bereits')
    import time
    _running = True
    try:
        return _run(profile, duration_s, save, time)
    finally:
        _running = False


def _run(profile, duration_s, save, clock):
    settings = cfg.SENSOR_TEST
    log = SensorLog(settings['capacity'])
    period = TimingStats(settings['loop_us'], cfg.MAX_LOOP_US)
    work = TimingStats(settings['loop_us'], cfg.MAX_LOOP_US)
    gps = baro = uart = None
    resources = {}
    started = clock.ticks_ms()
    errors, latched = {}, set()
    summary = {'schema': 1, 'test_version': settings['version'],
               'control_version': cfg.VERSION, 'profile': profile,
               'purpose': 'ground_sensor_test_no_pwm', 'control_loop_timing': False,
               'configuration': {'gps': dict(cfg.GPS), 'barometer': dict(cfg.BAROMETER),
                                 'test': dict(settings)},
               'runtime': {'implementation': sys.implementation.name,
                           'version': sys.version,
                           'machine': getattr(sys.implementation, '_machine', '')},
               'errors': errors, 'shutdown_ok': False}
    def record_error(device, phase, error):
        if device not in errors:
            errors[device] = {'phase': phase, 'type': type(error).__name__,
                              'message': str(error)[:160],
                              'ms': clock.ticks_diff(clock.ticks_ms(), started)}
            print('Sensorfehler:', device, phase, str(error)[:160])
        latched.add(device)
    last_baro, last_baro_ms = None, None
    reference_sum, reference_count, reference_pa = 0, 0, None
    first_fix_ms, gps_fix_samples, baro_samples = None, 0, 0
    previous_us, log_ms, print_ms = None, None, None
    stop_reason = 'duration'
    try:
        gps, baro, uart = _devices(profile, clock, resources)
        print('Sensor-Test', settings['version'], profile, '- keine Servoansteuerung')
        if baro:
            print('MS5611 Adresse:', hex(baro.address), 'PROM CRC OK')
        while clock.ticks_diff(clock.ticks_ms(), started) < int(duration_s * 1000):
            begin = clock.ticks_us()
            now = clock.ticks_ms()
            elapsed = clock.ticks_diff(now, started)
            delta = clock.ticks_diff(begin, previous_us) if previous_us is not None else None
            period.add(delta)
            previous_us = begin
            for name, device in (('gps', gps), ('barometer', baro)):
                if device is None or name in latched:
                    continue
                try:
                    result = device.poll(now)
                    if name == 'barometer' and result is not None:
                        last_baro, last_baro_ms = result, now
                        baro_samples += 1
                        if reference_pa is None and elapsed >= settings['reference_warmup_ms']:
                            reference_sum += result[0]
                            reference_count += 1
                            if reference_count == settings['reference_samples']:
                                reference_pa = reference_sum / reference_count
                except Exception as error:
                    record_error(name, 'poll', error)
            if log_ms is None or clock.ticks_diff(now, log_ms) >= int(1000 / settings['log_hz']):
                g = gps.snapshot(now) if gps and 'gps' not in latched else {}
                if g.get('valid'):
                    gps_fix_samples += 1
                    if first_fix_ms is None:
                        first_fix_ms = elapsed
                age = clock.ticks_diff(now, last_baro_ms) if last_baro_ms is not None else -1
                valid = bool(last_baro and 'barometer' not in latched and 0 <= age < 3 * cfg.BAROMETER['sample_ms'])
                b = {'valid': valid, 'age_ms': age,
                     'pressure_pa': last_baro[0] if valid else None,
                     'temperature_c': last_baro[1] if valid else None,
                     'relative_height_m': relative_altitude(last_baro[0], reference_pa)
                     if valid and reference_pa is not None else None,
                     'd1': last_baro[2] if valid else None, 'd2': last_baro[3] if valid else None}
                log.append(csv_row(elapsed, g, b, delta if delta is not None else 0))
                log_ms = now
                if print_ms is None or clock.ticks_diff(now, print_ms) >= int(1000 / settings['console_hz']):
                    print('t=%d GPS fix=%s sat=%s lat=%s lon=%s age=(%s,%s) BARO p=%s Pa T=%s C h_rel=%s m' %
                          (elapsed, int(g.get('valid', False)), g.get('satellites', 0),
                           _format(g.get('lat'), 7), _format(g.get('lon'), 7),
                           g.get('gga_age_ms', -1), g.get('rmc_age_ms', -1),
                           _format(b['pressure_pa']), _format(b['temperature_c']),
                           _format(b['relative_height_m'])))
                    print_ms = now
            work.add(clock.ticks_diff(clock.ticks_us(), begin))
            remaining = settings['loop_us'] - clock.ticks_diff(clock.ticks_us(), begin)
            if remaining > 0:
                clock.sleep_us(remaining)
    except KeyboardInterrupt:
        stop_reason = 'keyboard_interrupt'
    except Exception as error:
        stop_reason = 'error'
        record_error('test', 'startup_or_loop', error)
    finally:
        shutdown_ok = True
        uart = resources.get('uart', uart)
        if uart is not None:
            try:
                uart.deinit()
            except BaseException as error:
                shutdown_ok = False
                record_error('uart', 'shutdown', error)
        summary.update({'stop_reason': stop_reason, 'shutdown_ok': shutdown_ok,
                        'duration_ms': clock.ticks_diff(clock.ticks_ms(), started),
                        'period': period.report(), 'work': work.report(),
                        'csv_rows_total': log.total, 'csv_rows_retained': log.count,
                        'first_paired_fix_ms': first_fix_ms, 'gps_fix_log_samples': gps_fix_samples,
                        'barometer_samples': baro_samples, 'reference_pa': reference_pa,
                        'gps_counters': dict(gps.counters) if gps else {},
                        'first_nmea_sentences': gps.first_sentences if gps else [],
                        'barometer_prom': baro.prom if baro else None,
                        'barometer_address': baro.address if baro else None})
        summary['checks'] = {'gps_nmea_seen': bool(gps and gps.counters['sentences']),
                             'paired_gps_fix_seen': first_fix_ms is not None,
                             'barometer_samples_seen': baro_samples > 0,
                             'barometer_reference_ready': reference_pa is not None}
        print('Sensor-Test beendet:', stop_reason, '| Fehler:', len(errors))
    if save:
        stem = _free_stem(started)
        summary['csv_file'] = stem + '.csv'
        log.save(summary['csv_file'])
        with open(stem + '.json', 'w') as file:
            json.dump(summary, file)
        print('Sensor-CSV gespeichert:', summary['csv_file'])
        print('Sensor-JSON gespeichert:', stem + '.json')
    return summary
