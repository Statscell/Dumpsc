# https://github.com/Galaxy1036/Dumpsc
# The code below is directly obtained from the github link below.. full credits to the author <3

import os
import lzma
import lzham
import struct
import zstandard
from PIL import Image
from System.Logger import Console
import astc_decomp
import liblzfse

def load_ktx(data):
    header = data[:64]
    ktx_data = data[64:]

    if header[12:16] == bytes.fromhex('01020304'):
        endianness = '<'

    else:
        endianness = '>'

    if header[0:7] != b'\xabKTX 11':
        raise TypeError('Unsupported or unknown KTX version: {}'.format(header[0:7]))

    glInternalFormat, = struct.unpack(endianness + 'I', header[28:32])
    pixelWidth, pixelHeight = struct.unpack(endianness + '2I', header[36:44])
    bytesOfKeyValueData, = struct.unpack(endianness + 'I', header[60:64])

    if glInternalFormat not in (0x93B0, 0x93B4, 0x93B7):
        raise TypeError('Unsupported texture format: {}'.format(hex(glInternalFormat)))

    if glInternalFormat == 0x93B0:
        block_width, block_height = 4, 4

    elif glInternalFormat == 0x93B4:
        block_width, block_height = 6, 6

    else:
        block_width, block_height = 8, 8

    key_value_data = ktx_data[:bytesOfKeyValueData]
    ktx_data = ktx_data[bytesOfKeyValueData:]

    if b'Compression_APPLE' in key_value_data:
        if ktx_data[12:15] == b'bvx':
            image_data = liblzfse.decompress(ktx_data[12:])

        else:
            raise ValueError('Unsupported compression type: {}'.format(
                ktx_data[12:15])
            )

    else:
        image_data = ktx_data[4:]

    return Image.frombytes('RGBA', (pixelWidth, pixelHeight), image_data, 'astc', (block_width, block_height, False))


def convert_pixel(pixel, type):
    if type in (0, 1):
        # RGB8888
        return struct.unpack('4B', pixel)
    elif type == 2:
        # RGB4444
        p, = struct.unpack('<H', pixel)
        return (((p >> 12) & 0xF) << 4, ((p >> 8) & 0xF) << 4, ((p >> 4) & 0xF) << 4, ((p >> 0) & 0xF) << 4)
    elif type == 3:
        # RBGA5551
        p, = struct.unpack('<H', pixel)
        return (((p >> 11) & 0x1F) << 3, ((p >> 6) & 0x1F) << 3, ((p >> 1) & 0x1F) << 3, ((p) & 0xFF) << 7)
    elif type == 4:
        # RGB565
        p, = struct.unpack("<H", pixel)
        return (((p >> 11) & 0x1F) << 3, ((p >> 5) & 0x3F) << 2, (p & 0x1F) << 3)
    elif type == 6:
        # LA88 = Luminance Alpha 88
        p, = struct.unpack("<H", pixel)
        return (p >> 8), (p >> 8), (p >> 8), (p & 0xFF)
    elif type == 10:
        # L8 = Luminance8
        p, = struct.unpack("<B", pixel)
        return p, p, p
    else:
        return None


def decompress_data(data, baseName="Unknown"):
    version = None

    if data[:2] == b'SC':
        # Skip the header if there's any
        pre_version = int.from_bytes(data[2: 6], 'big')

        if pre_version == 4:
            version = int.from_bytes(data[6: 10], 'big')
            hash_length = int.from_bytes(data[10: 14], 'big')
            end_block_size = int.from_bytes(data[-4:], 'big')

            data = data[14 + hash_length:-end_block_size - 9]

        else:
            version = pre_version
            hash_length = int.from_bytes(data[6: 10], 'big')
            data = data[10 + hash_length:]

    if version in (None, 1, 3):
        try:
            if data[:4] == b'SCLZ':
                Console.info(' ├── Detected LZHAM compression')

                dict_size = int.from_bytes(data[4:5], 'big')
                uncompressed_size = int.from_bytes(data[5:9], 'little')
                decompressed = lzham.decompress(data[9:], uncompressed_size, {
                                                'dict_size_log2': dict_size})

            elif data[:4] == bytes.fromhex('28 B5 2F FD'):
                Console.info(' ├── Detected Zstandard compression')
                decompressed = zstandard.decompress(data)

            else:
                Console.info(' ├── Detected LZMA compression')
                data = data[0:9] + (b'\x00' * 4) + data[9:]
                decompressor = lzma.LZMADecompressor()

                output = []

                while decompressor.needs_input:
                    output.append(decompressor.decompress(data))

                decompressed = b''.join(output)

        except Exception as _:
            Console.info(' └── Cannot decompress {} !'.format(baseName))
            return

    else:
        decompressed = data

    return decompressed


def process_sc(baseName, data, path, decompress):
    if decompress:
        decompressed = decompress_data(data, baseName)

    else:
        decompressed = data

    i = 0
    picCount = 0

    images = []

    while len(decompressed[i:]) > 5:
        fileType, = struct.unpack('<b', bytes([decompressed[i]]))

        if fileType == 0x2D:
            i += 4  # Ignore this uint32, it's basically the fileSize + the size of subType + width + height (9 bytes)

        fileSize, = struct.unpack('<I', decompressed[i + 1:i + 5])
        subType, = struct.unpack('<b', bytes([decompressed[i + 5]]))
        width, = struct.unpack('<H', decompressed[i + 6:i + 8])
        height, = struct.unpack('<H', decompressed[i + 8:i + 10])
        i += 10

        if fileType != 0x2D:
            if subType in (0, 1):
                pixelSize = 4
            elif subType in (2, 3, 4, 6):
                pixelSize = 2
            elif subType == 10:
                pixelSize = 1
            elif subType != 15:
                raise Exception("Unknown pixel type {}.".format(subType))

            if subType == 15:
                ktx_size, = struct.unpack('<I', decompressed[i:i + 4])
                img = load_ktx(decompressed[i + 4: i + 4 + ktx_size])
                i += 4 + ktx_size

            else:
                img = Image.new("RGBA", (width, height))
                pixels = []

                for y in range(height):
                    for x in range(width):
                        pixels.append(convert_pixel(decompressed[i:i + pixelSize], subType))
                        i += pixelSize

                img.putdata(pixels)

            if fileType == 29 or fileType == 28 or fileType == 27:
                imgl = img.load()
                iSrcPix = 0

                for l in range(height // 32):  # block of 32 lines
                    # normal 32-pixels blocks
                    for k in range(width // 32):  # 32-pixels blocks in a line
                        for j in range(32):  # line in a multi line block
                            for h in range(32):  # pixels in a block
                                imgl[h + (k * 32), j + (l * 32)] = pixels[iSrcPix]
                                iSrcPix += 1
                    # line end blocks
                    for j in range(32):
                        for h in range(width % 32):
                            imgl[h + (width - (width % 32)), j + (l * 32)] = pixels[iSrcPix]
                            iSrcPix += 1
                # final lines
                for k in range(width // 32):  # 32-pixels blocks in a line
                    for j in range(height % 32):  # line in a multi line block
                        for h in range(32):  # pixels in a 32-pixels-block
                            imgl[h + (k * 32), j + (height - (height % 32))] = pixels[iSrcPix]
                            iSrcPix += 1
                # line end blocks
                for j in range(height % 32):
                    for h in range(width % 32):
                        imgl[h + (width - (width % 32)), j + (height - (height % 32))] = pixels[iSrcPix]
                        iSrcPix += 1

        else:
            img = load_ktx(decompressed[i:i + fileSize])
            i += fileSize

        img.save(path + baseName + ('_' * picCount) + '.png', 'PNG')
        picCount += 1
        images.append(img)

    return images
