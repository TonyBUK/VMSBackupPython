import enum
import typing
import struct

# Add Static Initialisation Functionality
def static_init(cls):
    if getattr(cls, "static_init", None):
        cls.static_init(cls)
    return cls
#end

class Value :

    def __init__(self, nValue : int) -> None:
        self.value = nValue
    #end

#end

class sizeof(enum.Enum) :

    uint8_t  = Value(1)
    int8_t   = Value(1)
    uint16_t = Value(2)
    int16_t  = Value(2)
    uint32_t = Value(4)
    int32_t  = Value(4)
    uint64_t = Value(8)
    int64_t  = Value(8)

    def getValue(self) -> int :
        return self.value.value
    #end

#end
    
kUnpackType = {
    sizeof.uint8_t.name  : "<B",
    sizeof.int8_t.name   : "<b",
    sizeof.uint16_t.name : "<H",
    sizeof.int16_t.name  : "<h",
    sizeof.uint32_t.name : "<L",
    sizeof.int32_t.name  : "<l",
    sizeof.uint64_t.name : "<Q",
    sizeof.int64_t.name  : "<q"
}

class addr :

    def __init__(self) -> None :

        self.kElements      = []
        self.kLookup        = {}
        self.nMaxAddress    = 0

    #end

    def replaceLast(self, nMaxAddress : int, kName : str, kBaseAddr : str | typing.Any, kBaseLength : str | typing.Any, kSize : sizeof, nArraySize = 1) -> None :

        assert(kName in self.kLookup)
        assert(self.kLookup[kName] == (len(self.kElements) - 1))

        nAddress = 0
        nSize    = kSize.getValue() * nArraySize

        self.nMaxAddress = nMaxAddress

        if None != kBaseAddr :
            assert(kBaseAddr in self.kLookup)
            nAddress += self.kElements[self.kLookup[kBaseAddr]][0]
        #end

        if None != kBaseLength :
            assert(kBaseLength in self.kLookup)
            nAddress += self.kElements[self.kLookup[kBaseAddr]][1]
        #end

        self.kElements[-1] = tuple([nAddress, nSize, kUnpackType[kSize.name], kSize])
    
        if (nAddress + nSize) > self.nMaxAddress :
            self.nMaxAddress = nAddress + nSize
        #end

    #end

    def add(self, kName : str, kBaseAddr : str | typing.Any, kBaseLength : str | typing.Any, kSize : sizeof, nArraySize = 1) -> None :

        assert(kName not in self.kLookup)

        nAddress = 0
        nSize    = kSize.getValue() * nArraySize

        if None != kBaseAddr :
            assert(kBaseAddr in self.kLookup)
            nAddress += self.kElements[self.kLookup[kBaseAddr]][0]
        #end

        if None != kBaseLength :
            assert(kBaseLength in self.kLookup)
            nAddress += self.kElements[self.kLookup[kBaseAddr]][1]
        #end

        self.kLookup[kName] = len(self.kElements)
        self.kElements.append(tuple([nAddress, nSize, kUnpackType[kSize.name], kSize]))
    
        if (nAddress + nSize) > self.nMaxAddress :
            self.nMaxAddress = nAddress + nSize
        #end

    #end

    def get(self, kName : str, kDataBuffer : bytes) -> int :

        assert(kName in self.kLookup)

        kElementMetaData = self.kElements[self.kLookup[kName]]
        nArraySize = kElementMetaData[1]//kElementMetaData[3].getValue()
        kElementData = struct.unpack_from(kElementMetaData[2][0] + str(nArraySize) + kElementMetaData[2][1], kDataBuffer, kElementMetaData[0])

        if nArraySize == 1 :
            assert(len(kElementData) == 1)
            return kElementData[0]
        else :
            assert(len(kElementData) == nArraySize)
            return kElementData
        #end

    #end

    def length(self) :
        return self.nMaxAddress
    #end

    kElements   : list = None
    kLookup     : dict = None
    nMaxAddress : int

#end