"""Bewusster Einstieg: run('sensor') ohne PWM, run('manual') mit RC-Freigabe.

Der Puffer MUSS vor app/Fluglogger importiert werden (L3-Nachweis). Kein Start
beim Import, kein Autostart, kein Flugtimer. calibration.json wird nur gelesen.
"""
import config as cfg

_running = False
_pending = None


def run(profile='sensor'):
    global _running, _pending
    if profile not in ('sensor', 'manual') or cfg.AUTO_START is not False:
        raise ValueError('Expliziter Logger-Bodeneinstieg: sensor/manual, AUTO_START=False')
    if _running:
        raise RuntimeError('Fluglogger laeuft bereits')
    if _pending is not None:
        raise RuntimeError('Ungesicherte Daten im RAM: erst save_pending(), kein Neustart')
    _running = True
    buffer = None
    session = None
    saved = (cfg.START_MODE, cfg.SAVE_LOG_ON_STOP, cfg.CONSOLE_HZ)
    try:
        from ram_buffer import RecordBuffer
        settings = cfg.FLIGHT_LOGGER
        buffer = RecordBuffer(settings['capacity'], settings['record_bytes'],
                              settings['records_per_block'])
        # Erst nach Pufferreservierung Code laden, keine Hardware in diesen Imports.
        from flight_logger import FlightSession
        import app
        session = FlightSession(buffer)
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
    _pending = None
    return report
