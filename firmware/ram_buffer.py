"""Vorab reservierte, recordweise adressierbare RAM-Bloecke, ohne Hardware.

Jeder Record liegt vollstaendig in einem kleinen bytearray. So braucht der
gesamte Mitschnitt keinen zusammenhaengenden Heapbereich. Kein Ring, kein
automatisches Verkleinern; ein ungueltiger Index wird immer abgewiesen.
Das Datenformat und die Aufnahmeverwaltung gehoeren zum spaeteren Logger.
"""


class RecordBuffer:
    def __init__(self, capacity, record_bytes, records_per_block=16, allocate=bytearray):
        for value in (capacity, record_bytes, records_per_block):
            if type(value) is not int or value <= 0:
                raise ValueError('RAM-Puffergroessen muessen positive Ganzzahlen sein')
        self.capacity = capacity
        self.record_bytes = record_bytes
        self.records_per_block = records_per_block
        self.block_count = (capacity + records_per_block - 1) // records_per_block
        self.payload_bytes = capacity * record_bytes
        self.max_block_bytes = min(capacity, records_per_block) * record_bytes
        self._blocks = [None] * self.block_count
        try:
            for index in range(self.block_count):
                # Auch der letzte Block reserviert nur die benoetigten Records.
                count = min(records_per_block, capacity - index * records_per_block)
                self._blocks[index] = allocate(count * record_bytes)
                if len(self._blocks[index]) != count * record_bytes:
                    raise ValueError('RAM-Allokation liefert falsche Blockgroesse')
        except BaseException:
            # Auch MemoryError/Ctrl+C nach mehreren Bloecken laesst keinen
            # halben Puffer zurueck. Der Aufrufer kann danach gc.collect() nutzen.
            self.release()
            raise

    def slot(self, index):
        """(Block, Byteoffset) fuer struct.pack_into/unpack_from, ohne Datenkopie."""
        if self._blocks is None:
            raise RuntimeError('RAM-Puffer ist freigegeben')
        if type(index) is not int or not 0 <= index < self.capacity:
            raise IndexError('RAM-Recordindex ausserhalb des Puffers')
        return (self._blocks[index // self.records_per_block],
                (index % self.records_per_block) * self.record_bytes)

    def release(self):
        """Alle Blockreferenzen loesen; bereits herausgegebene Slots nicht halten."""
        self._blocks = None
