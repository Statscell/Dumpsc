from struct import Struct
from System.Reader import Reader
from PIL import Image, ImageDraw

from System.Logger import Console

# --------------------------
# OBJECTS
# --------------------------
class SpriteGlobals:
    def __init__(self):
        self.shape_count = 0
        self.total_animation = 0
        self.total_textures = 0
        self.text_field_count = 0
        self.matrix_count = 0
        self.color_transformation_count = 0
        self.export_count = 0
        self.names = []

class SheetData:
    def __init__(self):
        self.size = (0, 0)

class SpriteData:
    def __init__(self):
        self.id = 0
        self.regions = []

class Region:
    def __init__(self):
        self.sheet_id = 0
        self.num_points = 0
        self.rotation = 0
        self.mirroring = 0
        self.shape_points = []
        self.sheet_points = []
        self.top = -32767
        self.left = 32767
        self.bottom = 32767
        self.right = -32767
        self.size = (0, 0)
        self.zero_x = 0
        self.zero_y = 0

class Point:
    def __init__(self):
        self.x = 0
        self.y = 0

    @property
    def position(self):
        return self.x, self.y

    @position.setter
    def position(self, value):
        self.x = value[0]
        self.y = value[1]

# --------------------------
# OBJECTS END
# --------------------------

def ceil(integer) -> int:
    return round(integer + 0.5)

def decode_sc(data, fileName):
    offset_shape = 0
    offset_sheet = 0

    reader = Reader(data)
    del data

    sprite_globals = SpriteGlobals()

    sprite_globals.shape_count = reader.uint16()
    sprite_globals.total_animation = reader.uint16()
    sprite_globals.total_textures = reader.uint16()
    sprite_globals.text_field_count = reader.uint16()
    sprite_globals.matrix_count = reader.uint16()
    sprite_globals.color_transformation_count = reader.uint16()

    sheet_data = [_class() for _class in [SheetData] * sprite_globals.total_textures]
    sprite_data = [_class() for _class in [SpriteData] * sprite_globals.shape_count]

    # 5 padding bytes
    reader.uint32()
    reader.byte()

    sprite_globals.export_count = reader.uint16()
    
    # Console.info(f" └── Shape count: {sprite_globals.shape_count}, Animation count: {sprite_globals.total_animation}, Export count: {sprite_globals.export_count}, Text field count: {sprite_globals.text_field_count}")

    # Reading the id and name of export items
    exports = [_function() for _function in [reader.uint16] * sprite_globals.export_count]
    exports = { i: reader.string() for i in exports }

    # sprite_globals.names = exports.values()

    while True:
        data_block_tag = "%02x" % reader.byte()
        data_block_size = reader.uint32()

        if data_block_tag in ["01", "18"]:
            reader.byte() # Pixel Type
            sheet_data[offset_sheet].size = (reader.uint16(), reader.uint16())
            offset_sheet += 1
            continue

        elif data_block_tag == "00":
            break

        elif data_block_tag == "08":
            [reader.int32() for i in range(6)]
            continue

        elif data_block_tag == "12":
            sprite_data[offset_shape].id = reader.uint16()

            region_count = reader.uint16()
            reader.uint16() # point count

            for y in range(region_count):
                region = Region()
                data_block_tag = '%02x' % reader.byte()

                if data_block_tag == '16':
                    reader.uint32() # data block length

                    region.sheet_id = reader.byte()
                    region.num_points = reader.byte()

                    region.shape_points = [_class() for _class in [Point] * region.num_points]
                    region.sheet_points = [_class() for _class in [Point] * region.num_points]

                    for z in range(region.num_points):
                        region.shape_points[z].x = reader.int32()
                        region.shape_points[z].y = reader.int32()

                    for z in range(region.num_points):
                        w, h = [reader.uint16() * sheet_data[region.sheet_id].size[i] / 0xffff for i in range(2)]
                        x, y = [ceil(i) for i in (w, h)]

                        if int(w) == x:
                            x += 1
                        if int(h) == y:
                            y += 1

                        region.sheet_points[z].position = (x, y)
                    
                sprite_data[offset_shape].regions.append(region)
            
            reader.uint32()
            reader.byte()

            offset_shape += 1
            continue

        elif data_block_tag == "0c":
            reader.uint16()
            reader.byte()
            reader.uint16()

            cnt1 = reader.uint32()
            for i in range(cnt1):
                reader.uint16()
                reader.uint16()
                reader.uint16()
            
            cnt2 = reader.uint16()
            for i in range(cnt2):
                reader.uint16()
            for i in range(cnt2):
                reader.byte()
            for i in range(cnt2):
                reader.string()

            while True:
                inline_data_type = reader.ubyte()
                reader.int32()

                if inline_data_type == 0:
                    break
                    
                if inline_data_type == 11:
                    reader.int16()
                    reader.string()
                elif inline_data_type == 31:
                    for x in range(4):
                        reader.ubyte()
                        reader.ubyte()
                        reader.string()
                        reader.string()

            continue

        else:
            reader.read(data_block_size)
    
    for x in range(sprite_globals.shape_count):
        for y in range(len(sprite_data[x].regions)):

            region = sprite_data[x].regions[y]

            region_min_x = 32767
            region_max_x = -32767
            region_min_y = 32767
            region_max_y = -32767

            for z in range(region.num_points):
                tmp_x, tmp_y = region.shape_points[z].position

                if tmp_y > region.top:
                    region.top = tmp_y
                if tmp_x < region.left:
                    region.left = tmp_x
                if tmp_y < region.bottom:
                    region.bottom = tmp_y
                if tmp_x > region.right:
                    region.right = tmp_x
                
                sheetpoint = region.sheet_points[z]

                tmp_x, tmp_y = sheetpoint.position

                if tmp_x < region_min_x:
                    region_min_x = tmp_x
                if tmp_x > region_max_x:
                    region_max_x = tmp_x
                if tmp_y < region_min_y:
                    region_min_y = tmp_y
                if tmp_y > region_max_y:
                    region_max_y = tmp_y
                
            region = region_rotation(region)

            tmp_x, tmp_y = region_max_x - region_min_x, region_max_y - region_min_y
            size = (tmp_x, tmp_y)

            if region.rotation in (90, 270):
                size = size[::-1]

            region.size = size
        
        sprite_data[x].regions[y] = region
    
    return sprite_globals, sprite_data, sheet_data

def cut_sprites(sprite_globals, sprite_data, sheet_data, sheet_image, folder_export):
    for x in range(sprite_globals.shape_count):
        for y in range(len(sprite_data[x].regions)):
            region = sprite_data[x].regions[y]

            # for i in range(len(region.sheet_points)):
            #     _x, _y = region.sheet_points[i].position
            #     print(f"region {x}.{i} - {_x},{_y}")

            polygon = [region.sheet_points[z].position for z in range(region.num_points)]

            img_mask = Image.new("L", sheet_data[region.sheet_id].size, 0)
            ImageDraw.Draw(img_mask).polygon(polygon, fill=255)
            bbox = img_mask.getbbox()
            if not bbox:
                continue

            region_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
            tmp_region = Image.new("RGBA", region_size, None)
            tmp_region.paste(sheet_image[region.sheet_id].crop(bbox), None, img_mask.crop(bbox))
            if region.mirroring:
                tmp_region = tmp_region.transform(region_size, Image.EXTENT, (region_size[0], 0, 0, region_size[1]))

            tmp_region.rotate(region.rotation, expand=True) \
                .save(f'{folder_export}/{x}_{y}.png')

def region_rotation(region):
    def calc_sum(points):
        x1, y1 = points[(z + 1) % num_points].position
        x2, y2 = points[z].position
        return (x1 - x2) * (y1 + y2)

    sum_sheet = 0
    sum_shape = 0
    num_points = region.num_points

    for z in range(num_points):
        sum_sheet += calc_sum(region.sheet_points)
        sum_shape += calc_sum(region.shape_points)

    sheet_orientation = -1 if (sum_sheet < 0) else 1
    shape_orientation = -1 if (sum_shape < 0) else 1

    region.mirroring = int(not (shape_orientation == sheet_orientation))

    if region.mirroring:
        for x in range(num_points):
            pos = region.shape_points[x].position
            region.shape_points[x].position = (pos[0] * - 1, pos[1])

    pos00 = region.sheet_points[0].position
    pos01 = region.sheet_points[1].position
    pos10 = region.shape_points[0].position
    pos11 = region.shape_points[1].position

    if pos01[0] > pos00[0]:
        px = 1
    elif pos01[0] < pos00[0]:
        px = 2
    else:
        px = 3

    if pos01[1] < pos00[1]:
        py = 1
    elif pos01[1] > pos00[1]:
        py = 2
    else:
        py = 3

    if pos11[0] > pos10[0]:
        qx = 1
    elif pos11[0] < pos10[0]:
        qx = 2
    else:
        qx = 3

    if pos11[1] > pos10[1]:
        qy = 1
    elif pos11[1] < pos10[1]:
        qy = 2
    else:
        qy = 3

    rotation = 0
    if px == qx and py == qy:
        rotation = 0

    elif px == 3:
        if px == qy:
            if py == qx:
                rotation = 1
            else:
                rotation = 3
        else:
            rotation = 2

    elif py == 3:
        if py == qx:
            if px == qy:
                rotation = 3
            else:
                rotation = 1
        else:
            rotation = 2

    elif px != qx and py != qy:
        rotation = 2

    elif px == py:
        if px != qx:
            rotation = 3
        elif py != qy:
            rotation = 1

    elif px != py:
        if px != qx:
            rotation = 1
        elif py != qy:
            rotation = 3

    if sheet_orientation == -1 and rotation in (1, 3):
        rotation += 2
        rotation %= 4

    region.rotation = rotation * 90
    return region
