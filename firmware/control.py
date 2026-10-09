"""Winkel-/Drehratenregelung und einmalige Neutralfreigabe.

Hauptklassen: AxisController (Sollwinkel -> Sollrate -> Servooffset), Gate.
Logik: begrenzter P-Regler aussen, PI-Regler innen; I standardmaessig 0.
Integrator begrenzt und bei Saettigung gegen Weiteraufbau geschuetzt.
Gier benutzt nur Sollrate (kein driftender absoluter Gierwinkel).
Gate verlangt neue RC-Frames in Neutral nur vor Aktivierung/nach RX-Ausfall.
Nach Aktivierung bleibt Trimmen ein gueltiges Kommando, ohne neue Freigabe.
Ein Automatikfehler wechselt bei gueltigem RX in manuellen Boden-Ersatzmodus;
kein unabhaengiger Hardware-Bypass. Wiederherstellung nur durch Neustart.
"""
from attitude import clamp, wrap_degrees


class AxisController:
    def __init__(self, settings, limit):
        self.settings = settings
        self.limit = limit
        self.integral = 0.0

    def reset(self):
        self.integral = 0.0

    def update(self, target, angle, rate, dt, rate_only=False):
        cfg = self.settings
        desired_rate = target if rate_only else cfg['angle_gain']*wrap_degrees(target-angle)
        desired_rate = clamp(desired_rate, -cfg['max_rate'], cfg['max_rate'])
        error = desired_rate-rate
        proposed = clamp(self.integral+cfg['rate_i']*error*dt,
                         -cfg['integral_limit'], cfg['integral_limit'])
        output = cfg['rate_p']*error+proposed
        if abs(output) <= self.limit or output*error < 0:
            self.integral = proposed
        return clamp(cfg['rate_p']*error+self.integral, -self.limit, self.limit)


class Gate:
    def __init__(self, frames=25, window=0.08):
        self.frames, self.window = frames, window
        self.count = 0
        self.armed = False

    def update(self, fresh, sticks, new_frame):
        if not fresh:
            self.armed, self.count = False, 0
        elif not self.armed and new_frame:
            self.count = self.count+1 if all(abs(s) <= self.window for s in sticks) else 0
            self.armed = self.count >= self.frames
        return self.armed


def select_mode(requested, armed, fresh, fault, reference_ok):
    if requested == 'sensor':
        return 'SENSOR'
    if not fresh:
        return 'RX_TIMEOUT'
    if not armed:
        return 'WAIT_NEUTRAL'
    if requested == 'manual':
        return 'MANUAL'
    if fault or not reference_ok:
        return 'MANUAL_FALLBACK'
    return 'STABILIZE'
