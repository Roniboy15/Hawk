"""Recordadressierung pruefen; kein Nachweis des echten MicroPython-Heaps."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'firmware'))
from ram_buffer import RecordBuffer


class RecordBufferTests(unittest.TestCase):
    def test_whole_records_survive_every_block_boundary_without_copy(self):
        # Verschiedene Daten ueber alle Records schreiben, erst danach lesen:
        # deckt Ueberlappung, vertauschte Bloecke und den letzten Teilblock ab.
        buffer = RecordBuffer(632, 144, 16)
        format_string = '<36I'
        for index in range(buffer.capacity):
            block, offset = buffer.slot(index)
            struct.pack_into(format_string, block, offset, *([index] * 36))
        for index in range(buffer.capacity):
            block, offset = buffer.slot(index)
            self.assertEqual(struct.unpack_from(format_string, block, offset), (index,) * 36)
        first, first_offset = buffer.slot(0)
        same, offset = buffer.slot(15)
        next_block, next_offset = buffer.slot(16)
        last, last_offset = buffer.slot(631)
        self.assertIs(first, same)
        self.assertIsNot(first, next_block)
        self.assertEqual((first_offset, offset, next_offset, last_offset), (0, 2160, 0, 1008))
        self.assertEqual((len(first), len(last)), (2304, 1152))
        self.assertEqual(buffer.payload_bytes, 91008)

    def test_no_wrapping_negative_indices_or_access_after_release(self):
        buffer = RecordBuffer(2, 144)
        for index in (-1, 2, 100, True, 0.0):
            with self.assertRaises(IndexError):
                buffer.slot(index)
        buffer.release()
        buffer.release()
        with self.assertRaises(RuntimeError):
            buffer.slot(0)

    def test_invalid_sizes_rejected_before_allocation(self):
        def allocate(size):
            self.fail('Kein Allokationsversuch bei ungueltigen Groessen')
        for sizes in ((0,144,16), (5,-1,16), (5,144,0), (True,144,16), (5,1.5,16)):
            with self.subTest(sizes=sizes), self.assertRaises(ValueError):
                RecordBuffer(*sizes, allocate=allocate)

    def test_wrong_allocator_size_is_not_accepted(self):
        with self.assertRaises(ValueError):
            RecordBuffer(20, 144, 16, lambda size:bytearray(size-1))


if __name__ == '__main__':
    unittest.main()
