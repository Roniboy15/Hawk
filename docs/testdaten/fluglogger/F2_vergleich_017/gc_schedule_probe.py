"""HOST ONLY: actual MicroPython allocations, simulated loop/GC times, no I/O."""
import sys, gc
sys.path.insert(0, sys.argv[1])  # firmware directory; machine.py stub on host path.
from imu import IMU
from attitude import Attitude
from flight_logger import FlightSession
import flight_logger

class Clock:
    us = 0
    def ticks_ms(self): return self.us // 1000
    def ticks_us(self): return self.us
    def ticks_diff(self, a, b): return a-b

class Bus:
    def readfrom_mem_into(self, addr, reg, target): pass

class Collector:
    def mem_free(self):
        clock.us += 7000
        return gc.mem_free()
    def collect(self):
        clock.us += 24000
        gc.collect()

class Probe:
    pass

class ProbeIMU(IMU):
    def __init__(self): pass

clock, probe = Clock(), Probe()
probe.clock = clock
probe.settings = {'gc_poll_ms': int(sys.argv[2]), 'gc_free_bytes': 32768}
probe.gc_work_limit_us, probe.startup_gc_us = 15000, 24000
probe.gc_count = probe.gc_max_us = probe.gc_deferred = 0
probe.gc_check_ms, probe.gc_pending, probe.gc_min_free = None, False, None
flight_logger.gc = Collector()
imu = ProbeIMU()
imu.settings = {'body_axes':(0,1,2), 'body_signs':(1,1,1),
                'acc_scale':(1,1,1), 'acc_offset':(0,0,0)}
imu.buffer = bytearray(b'\x00\x00\x00\x00\x40\x00\x00\x00\x00\x83\x01\x06\x01\x89')
imu.addr, imu.bus, imu.bias = 0x68, Bus(), (0,0,0)
imu.first_saturation = None
pose = Attitude()
for i in range(20):
    pose.update(imu.read(), 0.015)
    pose.angles()
held = []
gc.collect()
while gc.mem_free() > 70000:
    held.append(bytearray(1024))
gc.collect()
start_free = gc.mem_free()
increases = 0
for i in range(1000):
    before, planned = gc.mem_free(), probe.gc_count
    start = clock.us
    pose.update(imu.read(), 0.015)
    pose.angles()
    clock.us += 12000
    FlightSession._collect_if_due(probe, start)
    after = gc.mem_free()
    if after > before and planned == probe.gc_count:
        increases += 1  # Lower bound: unplanned collection during this step.
    clock.us += 3000
print('poll_ms=', probe.settings['gc_poll_ms'], 'start_free=', start_free,
      'unplanned_free_increases=', increases, 'planned=', probe.gc_count,
      'minimum_queried_free=', probe.gc_min_free, 'deferred=', probe.gc_deferred,
      'threshold=', gc.threshold(), 'automatic=', gc.isenabled())
