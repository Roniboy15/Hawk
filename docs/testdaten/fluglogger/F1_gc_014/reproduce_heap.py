import sys, gc, micropython
module = __import__(sys.argv[1])
payload = b'GNTXT,' + bytes(range(32,127)).replace(b'*', b'')
checksum = 0
for byte in payload:
    checksum ^= byte
line = b'$' + payload + b'*%02X' % checksum
for i in range(int(sys.argv[2])):
    getattr(module, 'pad%d' % i, None)
print('BEFORE'); micropython.qstr_info()
blocks = []
try:
    while True:
        blocks.append(bytearray(1024))
except MemoryError:
    pass
for i in range(0,len(blocks),2):
    blocks[i] = None
gc.collect()
print('FREE', gc.mem_free())
fields = module.checked_fields(line)
assert ','.join(fields).encode() == payload
print('PASS'); micropython.qstr_info()
