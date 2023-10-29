# automatically generated by the FlatBuffers compiler, do not modify

# namespace: tflite_schema_head

import flatbuffers
from flatbuffers.compat import import_numpy
np = import_numpy()

class UnpackOptions(object):
    __slots__ = ['_tab']

    @classmethod
    def GetRootAs(cls, buf, offset=0):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = UnpackOptions()
        x.Init(buf, n + offset)
        return x

    @classmethod
    def GetRootAsUnpackOptions(cls, buf, offset=0):
        """This method is deprecated. Please switch to GetRootAs."""
        return cls.GetRootAs(buf, offset)
    @classmethod
    def UnpackOptionsBufferHasIdentifier(cls, buf, offset, size_prefixed=False):
        return flatbuffers.util.BufferHasIdentifier(buf, offset, b"\x54\x46\x4C\x33", size_prefixed=size_prefixed)

    # UnpackOptions
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # UnpackOptions
    def Num(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0

    # UnpackOptions
    def Axis(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(6))
        if o != 0:
            return self._tab.Get(flatbuffers.number_types.Int32Flags, o + self._tab.Pos)
        return 0

def UnpackOptionsStart(builder): builder.StartObject(2)
def Start(builder):
    return UnpackOptionsStart(builder)
def UnpackOptionsAddNum(builder, num): builder.PrependInt32Slot(0, num, 0)
def AddNum(builder, num):
    return UnpackOptionsAddNum(builder, num)
def UnpackOptionsAddAxis(builder, axis): builder.PrependInt32Slot(1, axis, 0)
def AddAxis(builder, axis):
    return UnpackOptionsAddAxis(builder, axis)
def UnpackOptionsEnd(builder): return builder.EndObject()
def End(builder):
    return UnpackOptionsEnd(builder)