"""Tischtest-CSV plus JSON auf dem Mac pruefen; keine MCU-/Hardwarezugriffe.

Aufruf: python3 tools/analyze_bench.py logs/T1/bench_123.csv --expect sensor
Der gleichnamige JSON-Bericht wird automatisch gelesen. PASS gilt nur fuer
die aufgezeichnete Softwarefolge; mechanische/elektrische Beobachtung separat.
"""
import argparse
import csv
import json
import math
from pathlib import Path

AXES = ('roll', 'pitch', 'yaw')
PROFILES = ('sensor', 'stabilize', 'neutral-gate', 'missing-rx', 'rx-recovery',
            'pitch-range', 'imu-fault', 'timing-fault')
REQUIRED = {'ms', 'mode', 'fault', 'dt_ms', 'pre_output_us', 'write_us',
            'neutral_count', 'armed', 'fresh'}
for axis in AXES:
    REQUIRED.update(('servo_'+axis, 'rx_'+axis, 'rx_age_'+axis+'_ms', 'rx_seq_'+axis))


def read_csv(path):
    with open(path, newline='') as file:
        reader = csv.DictReader(file)
        missing = REQUIRED-set(reader.fieldnames or ())
        if missing:
            raise ValueError('CSV braucht v0.2.3-Felder: '+', '.join(sorted(missing)))
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError('Unvollstaendige CSV-Zeile')
            for name in REQUIRED-{'mode', 'fault'}:
                value = float(row[name])
                if not math.isfinite(value):
                    raise ValueError('Nichtendlicher CSV-Wert: '+name)
                row[name] = value
            rows.append(row)
    if not rows:
        raise ValueError('CSV ist leer')
    return rows


def _sequence(events, modes):
    """Gesuchte Modusfolge mit strikt aufeinanderfolgenden Fundstellen."""
    result, index = [], 0
    for event in events:
        if event['mode'] == modes[index]:
            result.append(event)
            index += 1
            if index == len(modes):
                return result
    return []


def inspect_run(rows, summary, expected=None):
    """Gibt Befunde statt einer allgemeinen Flug-/Hardwarefreigabe zurueck."""
    issues, warnings = [], []
    if not isinstance(summary, dict):
        raise ValueError('JSON-Bericht ist kein Objekt')
    if summary.get('summary_schema') != 1 or summary.get('csv_schema') != 2:
        raise ValueError('Unbekanntes JSON-/CSV-Schema')
    cfg = summary['configuration']
    # Kaputte/teilweise JSON-Berichte duerfen niemals still einen PASS liefern.
    for name in ('iterations', 'events_dropped', 'events_total', 'csv_rows_total',
                 'csv_rows_retained', 'timing_trips'):
        if type(summary[name]) is not int or summary[name] < 0:
            raise ValueError('Ungueltiger Berichtszaehler: '+name)
    for name in ('loop_us', 'max_loop_us', 'neutral_frames'):
        if type(cfg[name]) is not int or cfg[name] <= 0:
            raise ValueError('Ungueltiger Konfigurationswert: '+name)
    if cfg['loop_us'] > cfg['max_loop_us']:
        raise ValueError('Sollperiode ist groesser als Deadline')
    axes = cfg['active_axes']
    if not axes or len(set(axes)) != len(axes) or any(a not in AXES for a in axes):
        raise ValueError('Ungueltige aktive Achsen im Bericht')
    if not summary.get('shutdown_ok'):
        issues.append('Bestaetigte Abschaltung fehlt')
    if summary.get('stop_reason') != 'keyboard_interrupt':
        issues.append('Lauf endete mit Ausnahme statt bewusstem Stop')
    if summary['csv_rows_retained'] != len(rows):
        issues.append('CSV-Zeilenanzahl passt nicht zum JSON-Bericht')
    events = summary['events']
    if not events or not summary['iterations']:
        issues.append('Keine auswertbaren Iterationen/Zustandswechsel')
    if summary['events_dropped']:
        warnings.append('Zustandsring ueberschrieben; Modusfolge unvollstaendig')
    if summary['csv_rows_total'] > len(rows):
        warnings.append('CSV zeigt nur den Ringrest; JSON-Statistik umfasst den ganzen Lauf')
    previous = -1
    for row in rows:
        # Der erste Startabstand kann gerundet 0.00 ms sein; es ist noch keine
        # ganze Iteration. Die JSON-Periodenstatistik laesst diesen Wert aus.
        if row['ms'] < 0 or row['dt_ms'] < 0:
            issues.append('Ungueltige Zeit im CSV')
        if row['ms'] < previous:
            issues.append('Zeitfolge ist nicht monoton')
        previous = row['ms']
        for flag in ('armed', 'fresh'):
            if row[flag] not in (0, 1):
                issues.append('Ungueltiger Freigabewert '+flag)
        for axis in axes:
            servo = cfg['servos'][axis]
            pulse = row['servo_'+axis]
            if pulse and not servo['center']-servo['limit'] <= pulse <= servo['center']+servo['limit']:
                issues.append(axis+': Ausgang ausserhalb konfigurierter Grenzen')
            if row['mode'] in ('RX_TIMEOUT', 'WAIT_NEUTRAL') and pulse:
                if pulse != int(servo['center']+servo['trim']):
                    issues.append(axis+': blockierter Zustand ist nicht Trimneutral')
            if row['mode'] == 'SENSOR' and pulse:
                issues.append(axis+': SENSOR meldet einen PWM-Puls')
            if row['mode'] in ('MANUAL', 'STABILIZE', 'MANUAL_FALLBACK') and not pulse:
                issues.append(axis+': aktiver Steuermodus ohne Pulswert')
            if row['armed'] == 0 and row['mode'] in ('MANUAL', 'STABILIZE', 'MANUAL_FALLBACK'):
                issues.append('Steuermodus ohne Neutralfreigabe')
    # Moduswechsel sind unabhaengig vom 20-s-CSV-Ring gespeichert.
    for event in events:
        for axis in axes:
            index = AXES.index(axis)
            pulse = event['servo_us'][index]
            servo = cfg['servos'][axis]
            if event['pwm'] and event['mode'] in ('RX_TIMEOUT', 'WAIT_NEUTRAL'):
                if pulse != int(servo['center']+servo['trim']):
                    issues.append(axis+': Zustandswechsel war nicht Trimneutral')
            if not event['pwm'] and pulse:
                issues.append('Puls gemeldet vor PWM-Konstruktion')
    timing = summary['timing']
    for name in ('period', 'pre_output', 'write', 'work'):
        stats = timing[name]
        for key in ('count', 'over_period', 'over_deadline', 'invalid'):
            if type(stats[key]) is not int or stats[key] < 0:
                raise ValueError('Ungueltige Zeitstatistik: '+name)
        for key in ('min_us', 'max_us', 'mean_us'):
            value = stats[key]
            if stats['count'] and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
                raise ValueError('Unvollstaendige Zeitstatistik: '+name)
        if stats['count']:
            if not stats['min_us'] <= stats['mean_us'] <= stats['max_us']:
                raise ValueError('Widerspruechliche Zeitstatistik: '+name)
            if stats['max_us'] > cfg['max_loop_us'] and not stats['over_deadline']:
                raise ValueError('Fehlender Deadlinezaehler: '+name)
    if timing['work']['count']+timing['work']['invalid'] != summary['iterations']:
        raise ValueError('Zeitstatistik umfasst nicht alle abgeschlossenen Iterationen')
    if timing['period']['count']+timing['period']['invalid'] != max(0, summary['iterations']-1):
        raise ValueError('Loopabstandsstatistik ist unvollstaendig')
    if timing['work']['over_period']:
        warnings.append('Rechenzeit ueber Sollperiode; Jitter/Ursache beurteilen')
    if any(s['invalid'] for s in timing.values()):
        issues.append('Ungueltige Tick-Differenz aufgezeichnet')
    if expected and expected not in PROFILES:
        raise ValueError('Unbekanntes Testprofil')
    if expected and expected != 'timing-fault':
        if summary['timing_trips'] or any(s['over_deadline'] for s in timing.values()):
            issues.append('Unerwartete harte Zeitueberschreitung')
    if expected in ('sensor', 'stabilize', 'neutral-gate', 'missing-rx', 'rx-recovery'):
        if summary['fault_iterations'] or any(e['fault'] for e in events):
            issues.append('Unerwarteter Automatikfault')
    if expected == 'sensor':
        if cfg['requested_mode'] != 'sensor' or any(e['pwm'] for e in events):
            issues.append('SENSOR-Profil stimmt nicht / PWM aktiviert')
    elif expected == 'stabilize':
        active = _sequence(events, ('STABILIZE',))
        if cfg['requested_mode'] != 'stabilize' or not active or not active[0]['pwm']:
            issues.append('STABILIZE wurde nicht erreicht')
        elif any(e['mode'] != 'STABILIZE' for e in events if e['ms'] >= active[0]['ms']):
            issues.append('STABILIZE nach Aktivierung verlassen')
    elif expected == 'neutral-gate':
        sequence = _sequence(events, ('WAIT_NEUTRAL', 'MANUAL'))
        if cfg['requested_mode'] != 'manual' or not sequence:
            issues.append('WAIT_NEUTRAL -> MANUAL fehlt')
        elif sequence[0]['pwm'] or sequence[1]['neutral_count'] < cfg['neutral_frames']:
            issues.append('PWM vor Freigabe / zu wenige Neutralframes')
        if not any(row['mode'] == 'WAIT_NEUTRAL' and row['fresh'] and not row['armed']
                   and row['neutral_count'] == 0 and all(not row['servo_'+a] for a in axes)
                   for row in rows):
            issues.append('Start mit gesperrtem, nichtneutralem RC nicht aufgezeichnet')
    elif expected == 'missing-rx':
        if cfg['requested_mode'] not in ('manual', 'stabilize') or not _sequence(events, ('RX_TIMEOUT',)):
            issues.append('Aktuatorprofil mit RX_TIMEOUT fehlt')
        if any(e['pwm'] or e['armed'] for e in events) or any(row['servo_'+a] for row in rows for a in axes):
            issues.append('Trotz fehlendem RC wurden Ausgaenge aktiviert')
        if not events or events[-1]['mode'] != 'RX_TIMEOUT' or events[-1]['fresh']:
            issues.append('Am Testende kein fehlender RC-Kanal dokumentiert')
    elif expected == 'rx-recovery':
        sequence = _sequence(events, ('MANUAL', 'RX_TIMEOUT', 'WAIT_NEUTRAL', 'MANUAL'))
        if cfg['requested_mode'] != 'manual' or not sequence:
            issues.append('MANUAL -> RX_TIMEOUT -> WAIT_NEUTRAL -> MANUAL fehlt')
        elif not sequence[2]['fresh'] or sequence[2]['armed'] or sequence[3]['neutral_count'] < cfg['neutral_frames']:
            issues.append('RX-Wiederfreigabe ohne erforderliche Neutralframes')
    elif expected in ('pitch-range', 'imu-fault', 'timing-fault'):
        reason = {'pitch-range': 'PITCH_RANGE', 'imu-fault': 'IMU_RUNTIME',
                  'timing-fault': 'TIMING'}[expected]
        sequence = _sequence(events, ('STABILIZE', 'MANUAL_FALLBACK'))
        faults = [e for e in events if e['fault'] == reason]
        if cfg['requested_mode'] != 'stabilize' or not sequence or not faults:
            issues.append('STABILIZE -> verriegelter MANUAL_FALLBACK fehlt')
        elif any(e['mode'] == 'STABILIZE' for e in events if e['iteration'] >= faults[0]['iteration']):
            issues.append('STABILIZE nach Automatikfault wieder aktiv')
    # Eine verlorene Zustandsfolge darf keinen stillen PASS erhalten.
    complete = not summary['events_dropped']
    verdict = 'FAIL' if issues else 'PASS (Softwareprotokoll)' if expected and complete else 'BEFUND / UNVOLLSTAENDIG'
    return {'verdict': verdict, 'issues': sorted(set(issues)), 'warnings': warnings,
            'samples': len(rows), 'summary': summary}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', type=Path)
    parser.add_argument('--summary', type=Path)
    parser.add_argument('--expect', choices=PROFILES)
    args = parser.parse_args(argv)
    try:
        path = args.summary or args.csv.with_suffix('.json')
        with path.open() as file:
            summary = json.load(file)
        if Path(summary['csv_file']).name != args.csv.name:
            raise ValueError('CSV-Dateiname passt nicht zum JSON-Bericht')
        result = inspect_run(read_csv(args.csv), summary, args.expect)
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError) as error:
        print('UNVOLLSTAENDIG:', error)
        return 2
    print(result['verdict'])
    print('Version:', summary['version'], '| Modus:', summary['configuration']['requested_mode'],
          '| Iterationen:', summary['iterations'], '| CSV-Samples:', result['samples'])
    print('Modi:', summary['mode_iterations'], '| Faults:', summary['fault_iterations'])
    for name, stats in summary['timing'].items():
        print('%s: max=%s us, ueber Sollperiode=%d, ueber Deadline=%d' %
              (name, stats['max_us'], stats['over_period'], stats['over_deadline']))
    for message in result['issues']+result['warnings']:
        print('-', message)
    print('Physische Ruderwirkung, Signalpegel und Versorgung separat pruefen.')
    return 1 if result['issues'] else 0 if result['verdict'].startswith('PASS') else 2


if __name__ == '__main__':
    raise SystemExit(main())
