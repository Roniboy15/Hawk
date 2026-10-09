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
    def __init__(self, gain=1.0):
        self.q = (1.0, 0.0, 0.0, 0.0)
        self.gain = gain
        self.accel_used = False

    def seed(self, acc):
        ax, ay, az = acc
        if sum(v*v for v in acc) < 0.1:
            raise ValueError('Beschleunigung fuer Initialisierung zu klein')
        roll = math.atan2(ay, az)
        pitch = math.atan2(-ax, math.sqrt(ay*ay+az*az))
        cr, sr = math.cos(roll/2), math.sin(roll/2)
        cp, sp = math.cos(pitch/2), math.sin(pitch/2)
        self.q = (cr*cp, sr*cp, cr*sp, -sr*sp)

    def update(self, sample, dt):
        if not 0 < dt <= 0.05 or any(not math.isfinite(v) for v in sample):
            raise ValueError('Ungueltiger Filter-Zeitschritt/Messwert')
        ax, ay, az, gx, gy, gz = sample
        gx, gy, gz = [math.radians(v) for v in (gx, gy, gz)]
        w, x, y, z = self.q
        norm = math.sqrt(ax*ax+ay*ay+az*az)
        self.accel_used = False
        if 0.85 < norm < 1.15:
            ax, ay, az = ax/norm, ay/norm, az/norm
            px, py, pz = 2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)
            # Nur kleine Innovationen: dynamische Beschleunigung nicht blind folgen.
            if ax*px+ay*py+az*pz > math.cos(math.radians(25)):
                ex, ey, ez = ay*pz-az*py, az*px-ax*pz, ax*py-ay*px
                gx += self.gain*ex
                gy += self.gain*ey
                gz += self.gain*ez
                self.accel_used = True
        h = dt/2
        q = (w+(-x*gx-y*gy-z*gz)*h,
             x+(w*gx+y*gz-z*gy)*h,
             y+(w*gy+z*gx-x*gz)*h,
             z+(w*gz+x*gy-y*gx)*h)
        length = math.sqrt(sum(v*v for v in q))
        if not math.isfinite(length) or length < 0.1:
            raise ValueError('Quaternion ungueltig')
        self.q = tuple(v/length for v in q)

    def angles(self):
        w, x, y, z = self.q
        return (math.degrees(math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y))),
                math.degrees(math.asin(clamp(2*(w*y-z*x), -1, 1))),
                math.degrees(math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z))))
