import VMSBackupHelper
import BaseHeader
import VMSBackupRAMCache

class BSAHeader(BaseHeader.BaseHeader) :

    def __init__(self) -> None :

        self.kAddressData = VMSBackupHelper.addr()

        self.kAddressData.add("W_SIZE",             None,                   None,                   VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_TYPE",             "W_SIZE",               "W_SIZE",               VMSBackupHelper.sizeof.uint16_t)

    #end

    def LoadHeaderFromFile(self, kFile : VMSBackupRAMCache.VMSBackupRAMCache) -> None :
        super().LoadHeaderFromFile(kFile=kFile)
        self.Add_T_Text()
        super().ExtendHeaderFromFile(kFile=kFile)
    #end

    def LoadHeaderFromBuffer(self, kBlock : bytes) -> None :
        super().LoadHeaderFromBuffer(kBlock=kBlock)
        self.Add_T_Text()
        super().ExtendHeaderFromBuffer(kBlock=kBlock)
    #end

    def Add_T_Text(self) :
        self.kAddressData.add("T_TEXT",             "W_TYPE",               "W_TYPE",               VMSBackupHelper.sizeof.uint8_t, self.W_SIZE())
    #end

    def W_SIZE(self) -> int :
        return self.kAddressData.get("W_SIZE", self.kBuffer)
    #end

    def W_TYPE(self) -> int :
        return self.kAddressData.get("W_TYPE", self.kBuffer)
    #end

    def T_TEXT(self) -> list[int] :
        return self.kAddressData.get("T_TEXT", self.kBuffer)
    #end

    def GetLength(self) :
        return self.kAddressData.length()
    #end

#end