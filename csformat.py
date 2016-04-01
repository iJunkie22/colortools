import struct
from collections import OrderedDict


class DataBlock(object):
    expanded_field = False
    name_field = None
    block_type_field = bytes
    color_space_field = NotImplemented
    colors_od = NotImplemented
    block_count = NotImplemented

    n0_struct = struct.Struct('h')
    n1_struct = struct.Struct('hs')
    e_struct = struct.Struct('?')

    @property
    def name_len_prop(self):
        if self.name_field is None:
            return 0
        else:
            return len(self.name_field)

    def _pack_name_field(self)->bytes:
        if self.name_field is None:
            return self.n0_struct.pack(0)
        elif isinstance(self.name_field, str) or isinstance(self.name_field, bytes):
            return self.n1_struct.pack(len(self.name_field), self.name_field)
        else:
            raise NotImplementedError

    def unpack_name_field(self, fstream):
        name_len = self.n0_struct.unpack(fstream.peek(2)[:2])[0]

        if name_len == 0:  # the block is nameless
            fstream.read(2)
            self.name_field = None
        else:
            snap = fstream.tell()
            nl, self.name_field = struct.unpack('h' + str(name_len) + 's', fstream.read(2 + name_len)[:2 + name_len])

    def unpack_color_field(self, fstream):
        return NotImplemented

    def unpack_expanded_field(self, fstream):
        self.expanded_field = self.e_struct.unpack(fstream.read(1)[:1])[0]

    def _pack_expanded_field(self)->bytes:
        assert isinstance(self.expanded_field, bool)
        return self.e_struct.pack(self.expanded_field)

    def unpack_block_count(self, fstream):
        raise NotImplementedError

    def pack(self):
        return NotImplemented

    def unpack(self, fstream, is_first=False):
        self.unpack_name_field(fstream)
        self.unpack_color_field(fstream)
        if not is_first:
            self.unpack_expanded_field(fstream)


class ColorBlock(DataBlock):
    block_type_field = b'\x01\x00'
    color_space_field = int

    def unpack_color_field(self, fstream):
        self.color_space_field = self.n0_struct.unpack(fstream.read(2)[:2])[0]

        if self.color_space_field == 1:
            self.colors_od = OrderedDict.fromkeys('rgb')

        elif self.color_space_field == 2:
            self.colors_od = OrderedDict.fromkeys('cmyk')

        else:
            raise NotImplementedError

        for k in self.colors_od.keys():
            self.colors_od[k] = struct.unpack('f', fstream.read(4)[:4])[0]


class GroupBlockStart(DataBlock):
    block_type_field = b'\x02\x00'


class GroupBlockEnd(DataBlock):
    block_type_field = b'\x03\x00'

    def pack(self)->bytes:
        return b'\x03\x00'

    def unpack_expanded_field(self, fstream):
        raise NotImplementedError

    def unpack(self, fstream, is_first=False):
        return NotImplemented


class BlockCountBlock(DataBlock):
    block_count = int

    def unpack_expanded_field(self, fstream):
        raise NotImplementedError

    def unpack_block_count(self, fstream):
        self.block_count = self.n0_struct.unpack(fstream.read(2)[:2])[0]


class CSFile(object):
    def __init__(self):
        pass


class CSFileReader(object):
    MAGIC_NUMBER = (b'C', b'S')
    struct_mn = struct.Struct('2s')

    def __init__(self, fileOrStream):
        self.file = fileOrStream
        self.blocks = []
        self.reset()
        assert self.struct_mn.unpack(self.file.read(len(self.MAGIC_NUMBER))) == self.MAGIC_NUMBER

    def reset(self) ->int:
        pos = self.file.tell()
        if __debug__ and pos > 0:
            print("resetting file position")

        self.file.seek(0)
        return pos

    def _load_block(self)->int:
        # print(self.file.tell(), self.file.peek(2)[:2])

        if len(self.blocks) == 1:
            self.blocks.append(BlockCountBlock())
            self.blocks[-1].unpack_block_count(self.file)
            return 3

        btype = self.file.read(2)[:2]
        if btype == b'':
            return -1

        for i, cls_n in enumerate((ColorBlock, GroupBlockStart, GroupBlockEnd)):
            if btype == cls_n.block_type_field:
                self.blocks.append(cls_n())
                return i

        if __debug__:
            ss = self.file.tell()
            raise NotImplementedError(str(ss) + '-->Unknown block type:  ' + str(struct.unpack('h', btype)) + ':raw ' + str(btype))
        else:
            return -1

    def next_block(self):
        rcode = self._load_block()
        if rcode == -1:
            return False

        print(self.file.tell(), '-->loaded a ', self.blocks[-1])

        if rcode < 2:  # block has name
            self.blocks[-1].unpack(self.file, len(self.blocks) == 0)
            return True

    def read_all_blocks(self):
        while True:
            return self.next_block()



    @property
    def tail_block_type(self):
        try:
            return type(self.blocks[-1])
        except IndexError:
            return None


class CSColor(object):
    def __init__(self):
        self.name_str = ""
        self.colorspace = 1  # RGB
        self.expanded = False
        self.r = 0.0
        self.g = 0.0
        self.b = 0.0

    @property
    def name_str_len(self):
        return len(self.name_str)

with open("color_xml_test_data.cs", 'rb') as cs_fd:
    csf = CSFileReader(cs_fd)
    csf.read_all_blocks()
    print(csf.blocks)
    print(csf.tail_block_type)

exit()

with open("color_xml_test_data.cs", 'rb') as cs_fd:
    print(b''.join(struct.unpack('cc', cs_fd.read(2))).decode('utf-8'))
    block_type = struct.unpack('h', cs_fd.read(2))[0]
    print(block_type)
    name_str_len = struct.unpack('h', cs_fd.read(2))[0]
    print(name_str_len)
    if name_str_len > 0:
        name_str_str = struct.unpack('s', cs_fd.read(name_str_len))
        print(name_str_str)
    color_space = struct.unpack('h', cs_fd.read(2))[0]
    print(color_space)
    if color_space != 1:  # RGB
        raise NotImplementedError

    r, g, b = struct.unpack('fff', cs_fd.read(12))
    print(r, g, b)

    expanded = struct.unpack('?', cs_fd.read(1))[0]
    print(expanded)



