"""Gespeicherte Kalibrierung lesen, pruefen und im Stillstand schreiben.

Hauptfunktionen: load(), save(), check_channel(), check_orientation().
Logik: fehlende Datei erlaubt Sensoranzeige, aber keine Servoaktivierung.
RC-Min/Mitte/Max und Lage-Referenz werden explizit erfasst; Neutral wandert
nicht automatisch mit Sendertrimmung. Schreiben nur bei gestoppter Regelung.
Die neue quaternionbasierte Nick-/Rollreferenz wird neu gemessen; die alte
roll_level_cal_v1.json wird weder geloescht noch stillschweigend uebernommen.
"""
try:
    import ujson as json
except ImportError:
    import json
import math


def load(path):
    try:
        with open(path) as file:
            data = json.load(file)
    except OSError:
        return {'schema': 1, 'rc': {}, 'level': None}
    if data.get('schema') != 1 or not isinstance(data.get('rc'), dict):
        raise ValueError('Kalibrierdatei ungueltig')
    for channel in data['rc'].values():
        check_channel(channel)
    level = data.get('level')
    if level is not None:
        for name in ('roll', 'pitch'):
            value = level[name]
            if not math.isfinite(value) or abs(value) > 30:
                raise ValueError('Lagenreferenz unplausibel')
    return data


def check_channel(channel):
    low, center, high = (channel[key] for key in ('min', 'center', 'max'))
    if not (900 <= low < center < high <= 2100):
        raise ValueError('RC-Werte ungueltig')
    if center - low < 100 or high - center < 100:
        raise ValueError('RC-Weg zu klein')


def check_orientation(level, sensor_config):
    if (list(sensor_config['body_axes']) != level.get('axes') or
            list(sensor_config['body_signs']) != level.get('signs') or
            list(sensor_config['acc_offset']) != level.get('offset') or
            list(sensor_config['acc_scale']) != level.get('scale')):
        raise ValueError('Sensoranordnung/Korrektur geaendert: Lage neu speichern')


def save(path, data):
    # Kein Schreiben im Regelkreis. Temp-Datei vermindert Verlust beim Abbruch.
    import os
    with open(path + '.tmp', 'w') as file:
        json.dump(data, file)
        file.flush()
    os.rename(path + '.tmp', path)
