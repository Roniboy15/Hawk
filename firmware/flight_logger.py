"""MANUAL-Basislogger: Sensoren/CH3/LED, RAM im Loop, Export erst nach Stop.

Wird von flight_start NACH Pufferreservierung importiert. Nur start() erzeugt
Hardware. Steuerachsen gehoeren weiterhin ausschliesslich app/Receiver.
Zusatzfehler schalten hoechstens die Aufnahme ab, nicht die MANUAL-Ausgabe.
"""
import gc
import json
import os
import time
import config as cfg
from gps import GPS, _utc
from ms5611 import MS5611, relative_altitude
from recording import RecordingSwitch
from flight_records import RECORD_BYTES, FORMAT, COLUMNS, GroundStop, encode, csv_row


class FlightSession:
    def __init__(self, buffer, clock=time):
        self.buffer, self.clock = buffer, clock
        self.settings = dict(cfg.FLIGHT_LOGGER)
        self.start_method = 'explicit'
        s = self.settings
        if s['record_bytes'] != RECORD_BYTES or buffer.record_bytes != RECORD_BYTES:
            raise ValueError('Flugrecordformat passt nicht zum reservierten Puffer')
        for key in ('capacity', 'sample_ms', 'reserve_bytes', 'flash_reserve_bytes',
                    'led_brightness', 'stop_hold_ms', 'button_poll_ms',
                    'gps_ready_epochs', 'gps_min_satellites',
                    'gc_free_bytes', 'gc_work_limit_us', 'gc_poll_ms'):
            if type(s[key]) is not int or s[key] <= 0:
                raise ValueError('Ungueltige Fluglogger-Einstellung: '+key)
        if (s['sample_ms'] != 1000 or s['capacity'] != buffer.capacity or
                not 1 <= s['led_brightness'] <= 32 or s['led_pin'] != 16 or
                not 0 < s['gps_max_hdop'] <= 10 or s['reserve_bytes'] < 65536 or
                s['flash_reserve_bytes'] < 131072 or s['stop_hold_ms'] < 2000 or
                not 20 <= s['button_poll_ms'] <= 100 or
                not 16384 <= s['gc_free_bytes'] < s['reserve_bytes'] or
                s['gc_work_limit_us'] >= cfg.MAX_LOOP_US or
                not 20 <= s['gc_poll_ms'] <= 500):
            raise ValueError('Ungepruefte Fluglogger-Rate/Reserve/LED-Einstellung')
        # Alle neuen Pins vor jeder Hardwareinitialisierung auf Konflikte pruefen.
        pins = [cfg.SENSOR['sda'], cfg.SENSOR['scl']]
        pins += [s['pin'] for s in cfg.RECEIVER.values()]
        pins += [s['pin'] for s in cfg.SERVOS.values()]
        pins += [cfg.RECORDING_CHANNEL['pin'], cfg.GPS['rx'], cfg.GPS['tx'],
                 cfg.BAROMETER['sda'], cfg.BAROMETER['scl'], s['led_pin']]
        if (any(type(p) is not int or not 0 <= p <= 29 for p in pins) or
                len(set(pins)) != len(pins) or cfg.BAROMETER['i2c'] != 1 or
                cfg.BAROMETER['sda'] % 4 != 2 or
                cfg.BAROMETER['scl'] != cfg.BAROMETER['sda']+1):
            raise ValueError('Fluglogger-Pins kollidieren oder I2C1-Zuordnung falsch')
        r = cfg.RECORDING_CHANNEL
        self.switch = RecordingSwitch(r['low_us'], r['high_us'], r['hold_ms'],
                                      clock.ticks_diff, r['sign'])
        self.stop = GroundStop(clock.ticks_diff, s['stop_hold_ms'])
        self.aux = self.uart = self.gps = self.baro = self.led = self.button = None
        self.errors = {}
        self.count = self.samples = self.segment = 0
        self.recording = self.full = self.disabled = False
        self.last_sample_ms = self.last_button_ms = None
        self.last_imu_ms = self.last_baro_ms = None
        self.last_baro = self.fix = self.fix_ms = self.last_epoch = None
        self.gps_state = {}  # Arbeitssnapshot, vor Loop/RAM-Pruefung fuellen.
        self.good_epochs = 0
        self.reference_sum = self.reference_count = 0
        self.reference_pa = None
        self.started = None
        self.last_state = self.last_color = None
        self.free_after_init = None
        self.startup_gc_us = None
        self.gc_work_limit_us = 0  # Erst nach echter Startmessung freigeben.
        self.gc_count = self.gc_max_us = self.gc_deferred = 0
        self.gc_min_free = None
        self.gc_check_ms, self.gc_pending = None, False
        self.can_export = self.exported = False
        self.export_context = None
        self.stage_timing = None  # app aktiviert dies nur fuer SENSOR-Diagnose.

    def fail(self, name, error):
        # Pro Komponente ein begrenzter Fehler; kein wachsender Fehlerlog im Flug.
        if name not in self.errors:
            self.errors[name] = type(error).__name__+': '+str(error)[:160]
        if name == 'logger':
            self.disabled, self.recording = True, False
            self.color((self.settings['led_brightness'], self.settings['led_brightness']//3, 0))

    def start(self, metadata):
        from machine import Pin, UART, I2C
        from receiver import Receiver
        from neopixel import NeoPixel
        from rp2 import bootsel_button
        self.started = self.clock.ticks_ms()
        self.button = bootsel_button
        # Eigener vierter PIO-Kanal: sein Verlust ist NICHT all_fresh() der drei
        # Steuerachsen. app besitzt weiter die PIOs ab Index 0.
        self.aux = Receiver({'record': {'pin': cfg.RECORDING_CHANNEL['pin']}}, ('record',),
                            cfg.RX_TIMEOUT_MS, max_poll_ms=(cfg.MAX_LOOP_US+999)//1000,
                            sm_start=len(cfg.ACTIVE_AXES))
        self.led = NeoPixel(Pin(self.settings['led_pin'], Pin.OUT), 1)
        for name in ('gps', 'barometer'):
            try:
                if name == 'gps':
                    s = cfg.GPS
                    self.uart = UART(s['uart'], baudrate=s['baudrate'], tx=Pin(s['tx']),
                                     rx=Pin(s['rx']), bits=8, parity=None, stop=1,
                                     timeout=0, timeout_char=0, rxbuf=s['rxbuf'])
                    self.gps = GPS(self.uart, self.clock.ticks_diff, stale_ms=s['stale_ms'],
                                   max_read=s['max_read'], rxbuf=s['rxbuf'],
                                   max_poll_ms=s['max_poll_ms'],
                                   course_min_speed_ms=s['course_min_speed_ms'])
                    self.gps.snapshot(self.clock.ticks_ms(), self.gps_state)
                else:
                    s = cfg.BAROMETER
                    bus = I2C(s['i2c'], sda=Pin(s['sda']), scl=Pin(s['scl']),
                              freq=s['freq'], timeout=10000)
                    self.baro = MS5611(bus, address=s['address'], sample_ms=s['sample_ms'],
                                       sleep_ms=self.clock.sleep_ms, ticks_diff=self.clock.ticks_diff,
                                       ticks_ms=self.clock.ticks_ms)
            except Exception as error:
                self.fail(name, error)  # Fehlende Zusatzerfassung beendet MANUAL nicht.
        gc_start = self.clock.ticks_us()
        gc.collect()  # Bereits vorhandene Startbereinigung, nicht neu im Loop.
        self.startup_gc_us = self.clock.ticks_diff(self.clock.ticks_us(), gc_start)
        self.free_after_init = gc.mem_free()
        if self.free_after_init < self.settings['reserve_bytes']:
            raise MemoryError('Fluglogger: %d B frei, %d B Reserve nach echten Objekten verlangt' %
                              (self.free_after_init, self.settings['reserve_bytes']))
        # 5 ms Abstand zur Deadline, aus der gemessenen Start-GC abgeleitet.
        # Das ist eine Planungshilfe, keine obere Laufzeitgarantie fuer spaetere GC.
        self.gc_work_limit_us = max(0, min(self.settings['gc_work_limit_us'],
                                  cfg.MAX_LOOP_US-self.startup_gc_us-5000))
        self.gc_check_ms = self.clock.ticks_ms()
        self.color((12, 0, 0))
        print('Fluglogger', self.settings['version'], ': 1 Hz, CH3 unten/oben Pause/Aufnahme.')
        print('Nach Landung CH3 unten, BOOT 2 s halten; erst nach Speichermeldung ausschalten.')
        print('RAM nach echten Objekten frei:', self.free_after_init)

    def color(self, color):
        if self.led is not None and 'led' not in self.errors and color != self.last_color:
            try:
                self.led[0] = color
                self.led.write()
                self.last_color = color
            except Exception as error:
                self.fail('led', error)

    def _poll_sensors(self, now):
        if self.gps is not None and 'gps' not in self.errors:
            try:
                self.gps.poll(now)
                g = self.gps.snapshot(now, self.gps_state)
                # Letztes kohärentes Paar behalten, wenn nur die UTC-Epochen
                # kurz verschieden sind. Echte No-Fix-/Stale-Zustaende loeschen es.
                if not g.get('gga_valid') or not g.get('rmc_valid'):
                    self.fix, self.good_epochs, self.last_epoch = None, 0, None
                elif g['valid'] and (g['date'], g['utc']) != self.last_epoch:
                    self.last_epoch = (g['date'], g['utc'])
                    # Nur neue kohärente Fixepochen kopieren (~1 Hz). Ein spaeter
                    # gemischtes GGA/RMC-Paar darf den gueltigen Cache nicht aendern.
                    self.fix, self.fix_ms = dict(g), now
                    good = (g['satellites'] >= self.settings['gps_min_satellites'] and
                            g['hdop'] is not None and g['hdop'] <= self.settings['gps_max_hdop'])
                    self.good_epochs = min(self.settings['gps_ready_epochs'],
                                           self.good_epochs+1) if good else 0
            except Exception as error:
                self.fail('gps', error)
                self.fix, self.good_epochs = None, 0
        if self.stage_timing is not None:
            self.stage_timing.mark(4)  # GPS-Read/Parser/Fixpruefung separat.
        if self.baro is not None and 'barometer' not in self.errors:
            try:
                result = self.baro.poll(now)
                if result is not None:
                    self.last_baro, self.last_baro_ms = result, now
                    if self.reference_pa is None and self.clock.ticks_diff(now, self.started) >= 2000:
                        self.reference_sum += result[0]
                        self.reference_count += 1
                        if self.reference_count == 20:
                            self.reference_pa = self.reference_sum/20
            except Exception as error:
                self.fail('barometer', error)
        if self.stage_timing is not None:
            self.stage_timing.mark(5)

    def _snapshots(self, now):
        g = {}
        if self.fix is not None:
            g = dict(self.fix)
            age = self.clock.ticks_diff(now, self.fix_ms)
            for key in ('gga_age_ms', 'rmc_age_ms'):
                g[key] += age
            if age < 0 or max(g['gga_age_ms'], g['rmc_age_ms']) >= cfg.GPS['stale_ms']:
                g = {}  # Kein alter Fix bekommt eine neue Zeitmarke.
            else:
                g['utc_ms'] = _utc(g['utc'])
        age = self.clock.ticks_diff(now, self.last_baro_ms) if self.last_baro_ms is not None else -1
        valid = bool(self.last_baro and 'barometer' not in self.errors and
                     0 <= age < 3*cfg.BAROMETER['sample_ms'])
        b = {'valid': valid, 'age_ms': age,
             'pressure_pa': self.last_baro[0] if valid else None,
             'temperature_c': self.last_baro[1] if valid else None,
             'relative_height_m': relative_altitude(self.last_baro[0], self.reference_pa)
                 if valid and self.reference_pa is not None else None}
        return g, b

    def _append(self, kind, now, control, g, b, ch3, ready):
        if self.full or self.disabled:
            return
        if self.count == self.buffer.capacity-1:
            kind = 5  # Letzten Slot fuer eindeutiges FULL-Ereignis reservieren.
            self.full, self.recording = True, False
        encode(self.buffer, self.count, self.clock.ticks_diff(now, self.started),
               self.segment, kind, control, g, b, ch3, self.recording, ready, self.full)
        self.count += 1
        self.samples += int(kind == 1)

    def _collect_if_due(self, iteration_start):
        if self.gc_work_limit_us <= 0:
            return
        now = self.clock.ticks_ms()
        if (not self.gc_pending and self.gc_check_ms is not None and
                0 <= self.clock.ticks_diff(now, self.gc_check_ms) < self.settings['gc_poll_ms']):
            return  # mem_free() durchsucht den Heap, deshalb nicht jeden Loop.
        elapsed = self.clock.ticks_diff(self.clock.ticks_us(), iteration_start)
        if not 0 <= elapsed <= self.gc_work_limit_us:
            self.gc_deferred += 1
            return  # Arbeitsbudget VOR der kostspieligen Speicherabfrage pruefen.
        if not self.gc_pending:
            free = gc.mem_free()
            self.gc_check_ms = self.clock.ticks_ms()
            self.gc_min_free = free if self.gc_min_free is None else min(self.gc_min_free, free)
            if free >= self.settings['gc_free_bytes']:
                return
            self.gc_pending = True
        # Abfragezeit ist jetzt verbraucht: verbleibenden Platz bis zur echten
        # Deadline pruefen, nicht erneut das alte 15-ms-Arbeitslimit anwenden.
        budget = cfg.MAX_LOOP_US-max(self.startup_gc_us or 0, self.gc_max_us)-5000
        if not 0 <= self.clock.ticks_diff(self.clock.ticks_us(), iteration_start) <= budget:
            self.gc_deferred += 1
            return  # Anforderung merken, naechstes Mal ohne erneuten Heapscan.
        started = self.clock.ticks_us()
        gc.collect()  # Nach Ausgabe/LED; kein Flash, automatische GC bleibt aktiv.
        self.gc_count += 1
        self.gc_max_us = max(self.gc_max_us,
                            self.clock.ticks_diff(self.clock.ticks_us(), started))
        self.gc_pending = False
        self.gc_check_ms = self.clock.ticks_ms()

    def step(self, now, control):
        # Abfragekosten von BOOT/NeoPixel/Sensoren gehoeren zur gemessenen Arbeit.
        # BOOT bei Start erst loslassen; kein Stop waehrend Aufnahme, kein CH3-Export.
        if ('button' not in self.errors and (self.last_button_ms is None or
                self.clock.ticks_diff(now, self.last_button_ms) >= self.settings['button_poll_ms'])):
            self.last_button_ms = now
            try:
                if self.stop.update(bool(self.button()), not self.recording, now):
                    if self.stage_timing is not None:
                        self.stage_timing.mark(3)
                    return True
            except Exception as error:
                self.fail('button', error)
        if self.stage_timing is not None:
            self.stage_timing.mark(3)  # Logger-Eintritt/Kontext und BOOT-Abfrage.
        self._poll_sensors(now)
        ch3, fresh = None, False
        if self.aux is not None and 'channel' not in self.errors:
            try:
                self.aux.poll(now)
                ch3 = self.aux.channels['record']['pulse']
                fresh = self.aux.fresh('record', now)
            except Exception as error:
                self.fail('channel', error)
        wanted, event = self.switch.update(ch3, fresh, now)
        if self.stage_timing is not None:
            self.stage_timing.mark(6)
        self.recording = bool(wanted and not self.full and not self.disabled)
        if control['imu_fresh']:
            self.last_imu_ms = now
        control['imu_age_ms'] = self.clock.ticks_diff(now, self.last_imu_ms) if self.last_imu_ms is not None else -1
        age = self.clock.ticks_diff(now, self.fix_ms) if self.fix is not None else -1
        ready = bool(self.fix is not None and 0 <= age and
                     age+max(self.fix['gga_age_ms'], self.fix['rmc_age_ms']) < cfg.GPS['stale_ms'] and
                     self.good_epochs >= self.settings['gps_ready_epochs'])
        state = (control['mode'], control['fault'])
        due = self.recording and (self.last_sample_ms is None or
                self.clock.ticks_diff(now, self.last_sample_ms) >= self.settings['sample_ms'])
        # Hoehenrechnung/Record-Snapshots nur fuer echte Zeilen; Pollen/LED/BOOT
        # laufen weiterhin jede Iteration, auch bei pausierter Aufnahme.
        needed = bool(event or due or (self.recording and state != self.last_state))
        if needed and not self.full and not self.disabled:
            g, b = self._snapshots(now)
            control['work_to_log_us'] = self.clock.ticks_diff(self.clock.ticks_us(), control['iteration_start_us'])
        if event == 'start' and self.recording:
            self.segment += 1
            self._append(2, now, control, g, b, ch3, ready)
            self.last_sample_ms = now
        elif event in ('stop', 'channel_invalid') and not self.full and not self.disabled:
            self._append(3 if event == 'stop' else 4, now, control, g, b, ch3, ready)
        elif self.recording and state != self.last_state:
            self._append(6, now, control, g, b, ch3, ready)
        if self.recording and (self.last_sample_ms is None or
                self.clock.ticks_diff(now, self.last_sample_ms) >= self.settings['sample_ms']):
            self._append(1, now, control, g, b, ch3, ready)
            self.last_sample_ms = now
        self.last_state = state
        level = self.settings['led_brightness']
        blink_on = not self.recording or (now//250) % 2 == 0
        color = ((level, level//3, 0) if self.full or self.errors else
                 (0, level, 0) if ready else (level, 0, 0))
        if self.full or self.errors:
            blink_on = (now//125) % 2 == 0
        self.color(color if blink_on else (0, 0, 0))
        if self.stage_timing is not None:
            self.stage_timing.mark(7)  # Snapshots/Packen/LED, auch bei CH3-Pause.
        # app misst anschliessend Work/Period: die ganze GC-Pause bleibt sichtbar
        # und loest bei Ueberschreitung unveraendert die TIMING-Reaktion aus.
        self._collect_if_due(control['iteration_start_us'])
        return False

    def close(self):
        # Alles versuchen, Fehler erst danach weiterreichen. Kein Export wenn
        # irgendein PIO-/UART-Abschaltversuch unbestaetigt blieb.
        error = None
        for device, method in ((self.aux, 'close'), (self.uart, 'deinit')):
            if device is not None:
                try:
                    getattr(device, method)()
                except BaseException as current:
                    if error is None:
                        error = current
        if error is not None:
            raise error

    def export(self, metadata, diagnostics, reason):
        # Ausschliesslich nach app-bestaetigtem PWM/PIO/UART-Stop aufrufen.
        if not self.can_export:
            raise RuntimeError('Flugexport ohne bestaetigte Hardwareabschaltung gesperrt')
        self.color((0, 0, self.settings['led_brightness']))
        fs = os.statvfs('.')
        free = (fs[1] or fs[0])*min(fs[3], fs[4])
        # Konservativer Text-/JSON-Platzbedarf plus Dateisystemreserve.
        if free < self.count*1024+131072+self.settings['flash_reserve_bytes']:
            self.color((self.settings['led_brightness'], 0, 0))
            raise OSError('Zu wenig Flash fuer Export plus Reserve; RAM nicht ausschalten')
        for index in range(10000):
            stem = 'flight_%d_%d' % (self.clock.ticks_ms(), index)
            occupied = False
            for suffix in ('.csv', '.json'):
                try:
                    os.stat(stem+suffix)
                    occupied = True
                except OSError as error:
                    if error.args[0] != 2:
                        raise
            if not occupied:
                break
        else:
            raise OSError('Keine freie Fluglog-Dateinummer')
        report = dict(metadata)
        report.update(schema=1, logger_version=self.settings['version'],
                      start_method=self.start_method,
                      logger_configuration=self.settings, recording_channel=dict(cfg.RECORDING_CHANNEL),
                      gps_configuration=dict(cfg.GPS), barometer_configuration=dict(cfg.BAROMETER),
                      shutdown_ok=True, stop_reason=reason, csv_file=stem+'.csv',
                      csv_rows=self.count, samples=self.samples, segments=self.segment,
                      storage='record_aligned_ram', record_format=FORMAT,
                      allocated_bytes=self.buffer.payload_bytes, capacity=self.buffer.capacity,
                      record_bytes=RECORD_BYTES, full=self.full, logger_disabled=self.disabled,
                      errors=dict(self.errors), free_after_init_bytes=self.free_after_init,
                      startup_gc_us=self.startup_gc_us,
                      runtime_gc={'count': self.gc_count, 'max_us': self.gc_max_us,
                                  'deferred': self.gc_deferred, 'min_free_bytes': self.gc_min_free,
                                  'work_limit_us': self.gc_work_limit_us,
                                  'poll_ms': self.settings['gc_poll_ms'],
                                  'automatic_enabled': gc.isenabled()},
                      reserve_check_stage='after_sensors_receiver_before_pwm',
                      duration_ms=self.clock.ticks_diff(self.clock.ticks_ms(), self.started),
                      valid_bit_names=['imu', 'gps', 'barometer', 'gps_course', 'gga', 'rmc'],
                      status_bit_names=['recording', 'rc_armed', 'control_rx_fresh',
                                        'pwm_present', 'gps_ready', 'full'],
                      reference_pa=self.reference_pa, diagnostics=diagnostics.report(),
                      gps_counters=dict(self.gps.counters) if self.gps else {},
                      barometer_prom=self.baro.prom if self.baro else None)
        report['stage_timing'] = self.stage_timing.report() if self.stage_timing is not None else None
        with open(stem+'.csv', 'w') as file:
            file.write(COLUMNS+'\n')
            for index in range(self.count):
                file.write(csv_row(self.buffer, index))
        with open(stem+'.json', 'w') as file:
            json.dump(report, file)
        if hasattr(os, 'sync'):
            os.sync()
        self.color((0, self.settings['led_brightness'], self.settings['led_brightness']))
        print('Flugdaten gespeichert:', stem+'.csv')
        print('Flugbericht gespeichert:', stem+'.json', '- jetzt Versorgung abschalten.')
        self.exported = True
        return report
