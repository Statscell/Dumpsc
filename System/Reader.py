import io

class Reader(io.BytesIO):
    def __init__(self, buffer: bytes = b'', endian: str = 'little'):
        super().__init__(buffer)
        self.buffer = buffer
        self.endian = endian

    def read_int(self, length: int, signed=False):
        return int.from_bytes(self.read(length), self.endian, signed=signed)

    def ubyte(self):
        return self.read_int(1)

    def byte(self):
        return self.read_int(1, True)

    def uint16(self):
        return self.read_int(2)

    def int16(self):
        return self.read_int(2, True)

    def uint32(self):
        return self.read_int(4)

    def int32(self):
        return self.read_int(4, True)

    def string(self):
        length = self.ubyte()
        if length != 255:
            return self.read(length).decode()
        return ''
