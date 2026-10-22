import sys, gc, time
imu_module = __import__(sys.argv[1])
pose_module = __import__(sys.argv[2])
class Bus:
    def readfrom_mem_into(self, addr, reg, target):
        pass
class ProbeIMU(imu_module.IMU):
    def __init__(self):
        pass
imu = ProbeIMU()
imu.settings = {'body_axes':(0,1,2),'body_signs':(1,1,1),
                'acc_scale':(1,1,1),'acc_offset':(0,0,0)}
imu.buffer = bytearray(b'\x00\x00\x00\x00\x40\x00\x00\x00\x00\x83\x01\x06\x01\x89')
imu.addr, imu.bus, imu.bias = 0x68, Bus(), (0,0,0)
imu.first_saturation = None
pose=pose_module.Attitude()
for i in range(20):
    pose.update(imu.read(),0.02)
    pose.angles()
gc.collect()
gc.disable()
before=gc.mem_free()
start=time.ticks_us()
for i in range(100):
    pose.update(imu.read(),0.02)
    pose.angles()
elapsed=time.ticks_diff(time.ticks_us(),start)
after=gc.mem_free()
gc.enable()
print(sys.argv[1],sys.argv[2],'heap_bytes_100=',before-after,'pure_host_us_100=',elapsed)
