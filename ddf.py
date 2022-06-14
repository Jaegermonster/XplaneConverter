import struct

class DataItem:
    def __init__(self, name):
        self.name = name
        self.data = {}

class DDF:
    format_character = {
        'signed char'    : 'b',
        'unsigned char'  : 'B',
        'signed short'   : 'h',
        'unsigned short' : 'H',
        'signed long'    : 'l',
        'unsigned long'  : 'L',
        'float'          : 'f',
        'double'         : 'd'
        }

    def __init__(self, trackname):
        self.trackname = trackname
        self.info = {}
        self.items = []
        self.itemindex = {}
        self.packetformat = '='

        with open(trackname + '.ddf') as f:
            # read info block
            for line in f:
                line = line.rstrip('\n')
                if (line == ''):
                    break
                elif (line == '[*DDF*]'):
                    continue
                else:
                    item = line.split(' = ', maxsplit=1)
                    self.info[item[0]] = item[1]
            # read data description
            for line in f:
                line = line.rstrip('\n')
                if (line == ''):
                    continue
                elif (line[0] == '['):
                    ddf_item = DataItem(line[1:-1])
                    self.itemindex[ddf_item.name] = len(self.items)
                    self.items.append(ddf_item)
                    continue
                else:
                    item = line.split(' = ', maxsplit=1)
                    ddf_item.data[item[0]] = item[1]
                    if (item[0] == 'DataType'):
                        self.packetformat += DDF.format_character[item[1]]
        self.packetsize = int(self.info['PacketSize'])

    def __iter__(self):
        self.binfile = open(self.trackname + '.bin', 'rb')
        return self

    def __next__(self):
        packet = self.binfile.read(self.packetsize)
        if (not packet):
            self.binfile.close()
            raise StopIteration
        data = struct.unpack(self.packetformat, packet)
        return dict(zip(list(self.itemindex), data))
