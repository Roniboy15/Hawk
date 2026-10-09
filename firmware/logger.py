"""Begrenzter RAM-Ring fuer Diagnose; kein Flash-Schreiben im Regelkreis.

Hauptklasse RingLog: append() ueberschreibt aelteste Zeile, save() exportiert.
Logik: letzte LOG_CAPACITY Datensaetze im RAM. Export nur nach gestoppter PWM.
Stromverlust verliert den RAM-Inhalt. Dies ist KEIN dauerhafter Fluglogger.
Felder: Zeit, Modus, Roll/Nick/Gier, Sollwerte, Servopulse, Schleifenzeit, Fehler.
"""


class RingLog:
    HEADER = 'ms,mode,roll,pitch,yaw,target_roll,target_pitch,servo_roll,servo_pitch,servo_yaw,dt_ms,fault\n'

    def __init__(self, capacity=200):
        if capacity < 1:
            raise ValueError('Logkapazitaet muss positiv sein')
        self.rows = [None]*capacity
        self.index = 0
        self.count = 0

    def append(self, row):
        self.rows[self.index] = row
        self.index = (self.index+1) % len(self.rows)
        self.count = min(self.count+1, len(self.rows))

    def ordered(self):
        start = (self.index-self.count) % len(self.rows)
        for i in range(self.count):
            yield self.rows[(start+i) % len(self.rows)]

    def save(self, path):
        with open(path, 'w') as file:
            file.write(self.HEADER)
            for row in self.ordered():
                file.write(row)
