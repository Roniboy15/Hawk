"""Manueller Einstieg aus Thonny; Hauptfunktion ist app.run().

Logik: Dieser kleine Starter importiert die Module aus dem MCU-Dateisystem.
Nach Aenderungen Stop/Soft-Reset ausfuehren, damit gecachte Imports erneuert
werden. START_MODE und ACTIVE_AXES in config.py bestimmen den Bodenversuch.
"""
from app import run

if __name__ == '__main__':
    run()
