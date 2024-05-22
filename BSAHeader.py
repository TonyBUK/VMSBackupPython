import VMSBackupHelper
import VMSBackupRAMCache
import struct

# Note: This *could* use the BaseHeader class, however through profiling, I discovered that initialising the
#       addr class is slow when performed > 1,000,000 times per average save set, especially when in the
#       majority of the cases, the data is considered immutable.
#
#       This class acts as an exception to the rule, where the T_TEXT entry derives its size from the W_SIZE
#       field, meaning each instance of the class likely will have 

_W_SIZE_ADDR   = 0
_W_SIZE_TYPE   = VMSBackupHelper.sizeof.uint16_t
_W_SIZE_COUNT  = 1
_W_SIZE_LEN    = _W_SIZE_TYPE.getValue()
_W_SIZE_STRUCT = VMSBackupHelper.kUnpackType[_W_SIZE_TYPE.name]

_W_TYPE_ADDR   = _W_SIZE_ADDR + (_W_SIZE_COUNT * _W_SIZE_LEN)
_W_TYPE_TYPE   = VMSBackupHelper.sizeof.uint16_t
_W_TYPE_COUNT  = 1
_W_TYPE_LEN    = _W_TYPE_TYPE.getValue()
_W_TYPE_STRUCT = VMSBackupHelper.kUnpackType[_W_TYPE_TYPE.name]

_T_TEXT_ADDR   = _W_TYPE_ADDR + (_W_TYPE_COUNT * _W_TYPE_LEN)
_T_TEXT_TYPE   = VMSBackupHelper.sizeof.uint8_t
_T_TEXT_STRUCT = VMSBackupHelper.kUnpackType[_T_TEXT_TYPE.name]

class BSAHeader() :

    def __init__(self) -> None :

        self.kBuffer = bytearray()
        self.kCache  = {}
        self.nLength = 0

    #end

    def LoadHeaderFromFile(self, kFile : VMSBackupRAMCache.VMSBackupRAMCache) -> None :

        self.kBuffer += kFile.read(_T_TEXT_ADDR)
        self.kBuffer += kFile.read(self.W_SIZE())

        self.nLength = len(self.kBuffer)

    #end

    def LoadHeaderFromBuffer(self, kBlock : bytes) -> None :

        assert(len(kBlock) >= _T_TEXT_ADDR)
        self.kBuffer += kBlock[0:_T_TEXT_ADDR]
        if len(kBlock) >= (_T_TEXT_ADDR + self.W_SIZE()) :
            self.kBuffer += kBlock[_T_TEXT_ADDR:_T_TEXT_ADDR + self.W_SIZE()]
        #end

        self.nLength = len(self.kBuffer)

    #end

    def get(self, kDataBuffer : bytes, kCache : dict, kStructUnpackText : str, nCount : int, nOffset : int) -> int :

        if nOffset in kCache :

            return kCache[nOffset]

        else :

            kElementData = struct.unpack_from(kStructUnpackText[0] + str(nCount) + kStructUnpackText[1], kDataBuffer, nOffset)

            if nCount == 1 :
                assert(len(kElementData) == 1)
                kCache[nOffset] = kElementData[0]
                return kElementData[0]
            else :
                assert(len(kElementData) == nCount)
                kCache[nOffset] = kElementData
                return kElementData
            #end

        #end

    #end

    def W_SIZE(self) -> int :
        return self.get(self.kBuffer, self.kCache, _W_SIZE_STRUCT, _W_SIZE_COUNT, _W_SIZE_ADDR)
    #end

    def W_TYPE(self) -> int :
        return self.get(self.kBuffer, self.kCache, _W_TYPE_STRUCT, _W_TYPE_COUNT, _W_TYPE_ADDR)
    #end

    def T_TEXT(self) -> list[int] :
        return self.get(self.kBuffer, self.kCache, _T_TEXT_STRUCT, self.W_SIZE(), _T_TEXT_ADDR)
    #end

    def GetLength(self) :
        if 0 == self.nLength :
            return _T_TEXT_ADDR
        else :
            return self.nLength
        #end
    #end

    kBuffer      : bytearray            = None
    kCache       : dict                 = None
    nLength      : int                  = None

#end