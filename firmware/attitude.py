"""Dreidimensionale Orientierung aus Gyro und Beschleunigung schaetzen.

Hauptklasse Attitude: seed(accel) initialisiert Roll/Nick, update(sample,dt)
integriert ein normiertes Quaternion; angles() liefert Grad.
Logik: alle drei Gyroachsen gleichzeitig integrieren. Bei |a| nahe 1 g wird
ein begrenzter Gravitationsfehler zur Driftkorrektur verwendet (Mahony-artig,
ohne Bias-Integrator). Keine absolute Gierreferenz, keine GPS/Airspeed-Fusion.
Kein ArduPilot-Port/EKF: Flugbeschleunigungen koennen die Schaetzung stoeren.
Eulerwinkel nur fuer Anzeige und begrenzte Tischtest-Regelung; Quaternion
bleibt auch ueber 70 Grad Roll definiert. Nick nahe +/-90 Grad ist fuer
den Euler-Regler ungeeignet und wird von der Betriebslogik behandelt.
"""
import math

# Gemeinsame Obergrenze fuer Filter und Konfigurationspruefung in app.py.
MAX_DT_S = 0.05


def clamp(value, low, high):
    return min(high, max(low, value))


def wrap_degrees(angle):
    return (angle + 180.0) % 360.0 - 180.0


def quaternion(roll, pitch, yaw):
    r, p, y = [math.radians(v)/2 for v in (roll, pitch, yaw)]
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p),
                              math.sin(p), math.cos(y), math.sin(y))
    return (cr*cp*cy+sr*sp*sy, sr*cp*cy-cr*sp*sy,
            cr*sp*cy+sr*cp*sy, cr*cp*sy-sr*sp*cy)


def body_error(current, target):
    """Kuerzester Quaternionfehler als Rotationvektor in Koerperachsen, Grad."""
    aw, ax, ay, az = current
    bw, bx, by, bz = target
    # conjugate(current) * target
    w = aw*bw+ax*bx+ay*by+az*bz
    x = aw*bx-ax*bw-ay*bz+az*by
    y = aw*by+ax*bz-ay*bw-az*bx
    z = aw*bz-ax*by+ay*bx-az*bw
    if w < 0:
        w, x, y, z = -w, -x, -y, -z
    norm = math.sqrt(x*x+y*y+z*z)
    if norm < 1e-8:
        return (0.0, 0.0, 0.0)
    scale = math.degrees(2*math.atan2(norm, max(0.0, w)))/norm
    return (x*scale, y*scale, z*scale)


class Attitude:
    def __init__(self, gain=1.0, recovery=None):
        self.q = (1.0, 0.0, 0.0, 0.0)
        self.gain = gain
        self.accel_used = False
        self.recovery = recovery
        self.quiet_s = 0.0
        self.tilt_valid = False
        self.recoveries = 0

    def invalidate(self):
        self.tilt_valid, self.quiet_s = False, 0.0

    def seed(self, acc):
        ax, ay, az = acc
        if sum(v*v for v in acc) < 0.1:
            raise ValueError('Beschleunigung fuer Initialisierung zu klein')
        roll = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.sqrt(ay*ay+az*az))
        cr, sr = math.cos(roll/2), math.sin(roll/2)
        cp, sp = math.cos(pitch/2), math.sin(pitch/2)
        self.q = (cr*cp, sr*cp, cr*sp, -sr*sp)
        self.tilt_valid = True

    def update(self, sample, dt, use_accel=True):
        if not 0 < dt <= MAX_DT_S or any(not math.isfinite(v) for v in sample):
            raise ValueError('Ungueltiger Filter-Zeitschritt/Messwert')
        ax, ay, az, gx, gy, gz = sample
        rate2 = gx*gx+gy*gy+gz*gz
        gx, gy, gz = math.radians(gx), math.radians(gy), math.radians(gz)
        w, x, y, z = self.q
        norm = math.sqrt(ax*ax+ay*ay+az*az)
        self.accel_used = False
        r = self.recovery
        quiet = bool(r and use_accel and abs(norm-1) < r['accel_band_g'] and
                     rate2 < r['gyro_max_dps']**2)
        self.quiet_s = min(r['quiet_s'], self.quiet_s+dt) if quiet else 0.0
        if use_accel and 0.85 < norm < 1.15:
            ax, ay, az = ax/norm, ay/norm, az/norm
            px, py, pz = 2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)
            dot = clamp(ax*px+ay*py+az*pz, -1, 1)
            small = dot > math.cos(math.radians(25))
            recovering = bool(r and self.quiet_s >= r['quiet_s'])
            if recovering and not small:
                self.tilt_valid = False
            # Bewegte Messungen behalten die25-Grad-Sperre. Erst nach ruhigen
            # Messungen grosse Fehler LANGSAM korrigieren, niemals pose.seed().
            if small or recovering:
                ex, ey, ez = ay*pz-az*py, az*px-ax*pz, ax*py-ay*px
                length = math.sqrt(ex*ex+ey*ey+ez*ez)
                if recovering and not self.tilt_valid and length < 1e-6 and dot < 0:
                    # Genau180 Grad: Kreuzprodukt allein hat keinen Wiederfang.
                    ex, ey, ez = (0, pz, -py) if abs(px) < 0.9 else (-pz, 0, px)
                    length = math.sqrt(ex*ex+ey*ey+ez*ez)
                scale = self.gain
                if recovering and not self.tilt_valid and length > 1e-8:
                    scale = min(self.gain*math.acos(dot),
                                math.radians(r['max_correction_dps']))/length
                gx += scale*ex
                gy += scale*ey
                gz += scale*ez
                self.accel_used = True
                if recovering and not self.tilt_valid and dot > math.cos(math.radians(5)):
                    self.tilt_valid = True
                    self.recoveries += 1
        # Exakte Rotation fuer konstante Rate im Schritt. Die alte Eulernaeherung
        # erzeugt bei schnellen Discus-Drehungen auch ohne Clipping Lagefehler.
        speed = math.sqrt(gx*gx+gy*gy+gz*gz)
        h = math.sin(speed*dt/2)/speed if speed > 1e-8 else dt/2
        c = math.cos(speed*dt/2)
        q = (w*c+(-x*gx-y*gy-z*gz)*h,
             x*c+(w*gx+y*gz-z*gy)*h,
             y*c+(w*gy+z*gx-x*gz)*h,
             z*c+(w*gz+x*gy-y*gx)*h)
        # Feste vier Komponenten direkt rechnen: gleiche Normierung ohne
        # Generator-/Listenobjekte in jeder Regeliteration.
        length = math.sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3])
        if not math.isfinite(length) or length < 0.1:
            raise ValueError('Quaternion ungueltig')
        self.q = (q[0]/length, q[1]/length, q[2]/length, q[3]/length)

    def angles(self):
        w, x, y, z = self.q
        return (math.degrees(math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y))),
                math.degrees(math.asin(clamp(2*(w*y-z*x), -1, 1))),
                math.degrees(math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))))
