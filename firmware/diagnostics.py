"""Begrenzte Tischtest-Diagnose ohne Hardwarezugriff oder Flash im Regelkreis.

TimingStats sammelt min/max/Summe/Anzahl statt jede Iteration zu speichern.
BenchDiagnostics haelt nur EVENT_CAPACITY Zustandswechsel im RAM. RX-Alter ist
eine konservative PIO-Zeitschaetzung, kein Capture-/Funkzeitstempel. Export erst
nach bestaetigter PWM-/PIO-Abschaltung durch app.run().
"""
try:
    import ujson as json
except ImportError:
    import json


class TimingStats:
    def __init__(self, period_us, deadline_us):
        self.period_us, self.deadline_us = period_us, deadline_us
        self.count = self.total = self.maximum = 0
        self.minimum = None
        self.over_period = self.over_deadline = self.invalid = 0

    def add(self, value):
        if value is None:
            return  # Z.B. kein PWM-Ausgang in SENSOR; nicht als 0 us messen.
        if value < 0:
            self.invalid += 1
            return
        self.count += 1
        self.total += value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = max(self.maximum, value)
        self.over_period += int(value > self.period_us)
        self.over_deadline += int(value > self.deadline_us)

    def report(self):
        return {'count': self.count, 'min_us': self.minimum,
                'max_us': self.maximum if self.count else None,
                'mean_us': self.total/self.count if self.count else None,
                'over_period': self.over_period, 'over_deadline': self.over_deadline,
                'invalid': self.invalid}


def rx_snapshot(channels, axes, now, ticks_diff):
    """Feste Reihenfolge Roll/Nick/Gier; 0 = kein Puls, -1 = Alter unbekannt.

    Nur bereits gelesene Channel-Daten ansehen, weder PIO noch GPIO abfragen.
    Sequenzen zeigen neue Pulse auch bei unveraendertem Knueppel; sie beweisen
    keine Funkverbindung, wenn der Empfaenger selbst FailSafe-Pulse erzeugt.
    """
    pulses, ages, sequences = [], [], []
    for axis in ('roll', 'pitch', 'yaw'):
        channel = channels.get(axis) if axis in axes else None
        stamp = channel.get('time') if channel else None
        age = ticks_diff(now, stamp) if stamp is not None else -1
        pulses.append((channel.get('pulse') or 0) if channel else 0)
        ages.append(age if age >= 0 else -1)
        sequences.append(channel.get('sequence', 0) if channel else 0)
    return pulses, ages, sequences


class BenchDiagnostics:
    def __init__(self, period_us, deadline_us, capacity):
        self.timing = {name: TimingStats(period_us, deadline_us)
                       for name in ('period', 'pre_output', 'write', 'work')}
        self.events = [None]*capacity
        self.index = self.event_count = self.events_total = 0
        self.iterations = self.timing_trips = 0
        self.last_state = None
        self.mode_iterations, self.fault_iterations = {}, {}

    def transition(self, ms, mode, fault, pwm, armed, neutral_count, fresh, rx, pulses):
        # Nur Modus-/Fault-/PWM-Wechsel archivieren, kein wachsender Frame-Log.
        state = (mode, fault, pwm)
        if state == self.last_state:
            return False
        self.last_state = state
        self.events[self.index] = {
            'ms': ms, 'iteration': self.iterations+1, 'mode': mode, 'fault': fault,
            'pwm': pwm, 'armed': armed, 'neutral_count': neutral_count, 'fresh': fresh,
            'rx_us': rx[0], 'rx_age_ms': rx[1], 'rx_sequence': rx[2],
            'servo_us': [pulses.get(a, 0) for a in ('roll', 'pitch', 'yaw')]}
        self.index = (self.index+1) % len(self.events)
        self.event_count = min(self.event_count+1, len(self.events))
        self.events_total += 1
        return True

    def finish(self, period_us, pre_output_us, write_us, work_us, timing_failed):
        self.iterations += 1
        self.timing_trips += int(timing_failed)
        if self.last_state:
            mode, fault, _ = self.last_state
            self.mode_iterations[mode] = self.mode_iterations.get(mode, 0)+1
            if fault:
                self.fault_iterations[fault] = self.fault_iterations.get(fault, 0)+1
        for name, value in (('period', period_us), ('pre_output', pre_output_us),
                            ('write', write_us), ('work', work_us)):
            self.timing[name].add(value)

    def report(self):
        start = (self.index-self.event_count) % len(self.events)
        events = [self.events[(start+i) % len(self.events)] for i in range(self.event_count)]
        result = {'iterations': self.iterations, 'timing_trips': self.timing_trips,
                'timing': {name: stats.report() for name, stats in self.timing.items()},
                'events_total': self.events_total,
                'events_dropped': self.events_total-self.event_count, 'events': events}
        result.update(mode_iterations=dict(self.mode_iterations),
                      fault_iterations=dict(self.fault_iterations))
        return result

    def save(self, path, metadata):
        # Diese Methode niemals aus der laufenden Schleife aufrufen.
        result = dict(metadata)
        result.update(self.report())
        with open(path, 'w') as file:
            json.dump(result, file)
