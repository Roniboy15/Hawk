"""Expliziter Thonny-Einstieg fuer beaufsichtigte Tischtestprofile.

Auf dem MCU am >>>-Prompt: import bench_test; bench_test.run('manual').
Import allein startet nichts. Profile veraendern nur RAM-Konfiguration und
stellen sie bei Rueckkehr/Fehler wieder her. App-Kalibrierung, Frische- und
Neutralgate gelten unveraendert. Kein simuliertes RX-/I2C-/Timingversagen.
"""
import config as cfg


def run(profile='sensor'):
    if profile not in ('sensor', 'manual', 'stabilize', 'pitch-range'):
        raise ValueError('Tischtestprofil: sensor / manual / stabilize / pitch-range')
    if cfg.AUTO_START is not False:
        raise ValueError('Tischtest verlangt AUTO_START=False')
    mode = 'stabilize' if profile == 'pitch-range' else profile
    previous_mode, previous_limit = cfg.START_MODE, cfg.PITCH_CONTROL_LIMIT_DEG
    try:
        cfg.START_MODE = mode
        if profile == 'pitch-range':
            # Ein echter, leichter erreichbarer Winkelgrenz-Fault, kein
            # vorgespielter IMU-/Busfehler. Nur dieses bewusste Profil nutzt 20 Grad.
            cfg.PITCH_CONTROL_LIMIT_DEG = 20.0
        from app import run as run_app
        print('TISCHTEST:', profile, '| Ausgabe erst nach App-Neutralfreigabe.')
        if profile == 'pitch-range':
            print('Testgrenze absoluter Nick=20 Grad; danach MANUAL_FALLBACK erwartet.')
        run_app()
    finally:
        # Auch Ctrl+C/Startfehler duerfen kein Testprofil fuer den naechsten
        # Aufruf hinterlassen. Die Datei config.py wird nie geschrieben.
        cfg.START_MODE, cfg.PITCH_CONTROL_LIMIT_DEG = previous_mode, previous_limit
