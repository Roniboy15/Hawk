"""Bewusster Einstieg: run('sensor') ohne PWM, run('manual') mit RC-Freigabe.

Der Puffer MUSS vor app/Fluglogger importiert werden (L3-Nachweis). Kein Start
beim Import, kein Flugtimer. Optionaler Bordstart verlangt eine BOOT-Freigabe.
calibration.json wird nur gelesen.
"""
import config as cfg

_running = False
_pending = None


def _wait_for_start():
    # Erst nach Puffer/Imports und FlightSession-Pinpruefung aufrufen. Vor dem
    # App-Start gibt es weder RC-PIO noch Servo-PWM; BOOT kann nichts abwuergen.
    import time
    from machine import Pin
    from rp2 import bootsel_button
    from neopixel import NeoPixel
    from flight_records import GroundStop
    s = cfg.FLIGHT_LOGGER
    button = GroundStop(time.ticks_diff, s['stop_hold_ms'])
    led = NeoPixel(Pin(s['led_pin'], Pin.OUT), 1)
    try:
        led[0] = (s['led_brightness'], 0, s['led_brightness'])
        led.write()
        print('Bordstart: BOOT loslassen, dann 2 s halten; bei Weiss loslassen.')
        while not button.update(bool(bootsel_button()), True, time.ticks_ms()):
            time.sleep_ms(s['button_poll_ms'])
        led[0] = (s['led_brightness'],)*3
        led.write()
        # Gehaltener Starttaster darf nicht bis in den laufenden Logger reichen.
        while bootsel_button():
            time.sleep_ms(s['button_poll_ms'])
    finally:
        led[0] = (0, 0, 0)
        led.write()


def run(profile='sensor', wait_for_button=False):
    global _running, _pending
    if profile not in ('sensor', 'manual') or cfg.AUTO_START is not False:
        raise ValueError('Expliziter Logger-Bodeneinstieg: sensor/manual, AUTO_START=False')
    if _running:
        raise RuntimeError('Fluglogger laeuft bereits')
    if _pending is not None:
        raise RuntimeError('Ungesicherte Daten im RAM: erst save_pending(), kein Neustart')
    if cfg.LOGGER_PROFILE not in ('snapshot1', 'response20'):
        raise ValueError('Loggerprofil muss snapshot1 oder response20 sein')
    _running = True
    buffer = fast_buffer = None
    session = None
    saved = (cfg.START_MODE, cfg.SAVE_LOG_ON_STOP, cfg.CONSOLE_HZ)
    try:
        from ram_buffer import RecordBuffer
        settings = cfg.FLIGHT_LOGGER
        fast = cfg.RESPONSE_LOGGER if cfg.LOGGER_PROFILE == 'response20' else None
        capacity = fast['snapshot_capacity'] if fast else settings['capacity']
        buffer = RecordBuffer(capacity, settings['record_bytes'], settings['records_per_block'])
        if fast:
            fast_buffer = RecordBuffer(fast['capacity'], fast['record_bytes'], fast['records_per_block'])
        # Erst nach Pufferreservierung Code laden, keine Hardware in diesen Imports.
        from flight_logger import FlightSession
        import app
        if fast:
            from response_log import ResponseLog
            session = FlightSession(buffer, response=ResponseLog(fast_buffer))
        else:
            session = FlightSession(buffer)
        session.preflight_storage()
        if wait_for_button:
            _wait_for_start()
            session.start_method = 'boot_button'
        cfg.START_MODE, cfg.SAVE_LOG_ON_STOP, cfg.CONSOLE_HZ = profile, False, 1
        return app.run(session=session)
    finally:
        cfg.START_MODE, cfg.SAVE_LOG_ON_STOP, cfg.CONSOLE_HZ = saved
        if (session is not None and not session.exported and
                (session.count or session.export_context is not None)):
            # Bei Exportfehlern nicht ausgerechnet den einzigen Datensatz freigeben.
            # Ein erneuter Export bleibt an bestaetigten Hardwarestop gebunden.
            _pending = session
        elif buffer is not None:
            buffer.release()
            if fast_buffer is not None:
                fast_buffer.release()
        _running = False


def save_pending():
    """Nur nach bestaetigtem Stop: gescheiterten Export mit neuer Dateinummer versuchen."""
    global _pending
    if _running or _pending is None:
        raise RuntimeError('Kein gestoppter, ungesicherter Flug vorhanden')
    if not _pending.can_export or _pending.export_context is None:
        raise RuntimeError('Abschaltung unbestaetigt; kein Flash-Export erlaubt')
    report = _pending.export(*_pending.export_context)
    _pending.buffer.release()
    if _pending.response is not None:
        _pending.response.buffer.release()
    _pending = None
    return report
