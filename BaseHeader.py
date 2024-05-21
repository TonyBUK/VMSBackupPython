import VMSBackupHelper
import VMSBackupRAMCache

class BaseHeader :

    def LoadHeaderFromFile(self, kFile : VMSBackupRAMCache.VMSBackupRAMCache) -> None :
        self.kBuffer = kFile.read(self.kAddressData.length())
    #end

    def ExtendHeaderFromFile(self, kFile : VMSBackupRAMCache.VMSBackupRAMCache) -> None :
        if len(self.kBuffer) < self.kAddressData.length() :
            self.kBuffer += kFile.read(self.kAddressData.length() - len(self.kBuffer))
        #end
    #end

    def LoadHeaderFromBuffer(self, kBlock : bytes) -> None :
        assert(len(kBlock) >= self.kAddressData.length())
        self.kBuffer = kBlock[0:self.kAddressData.length()]
    #end

    def ExtendHeaderFromBuffer(self, kBlock : bytes) -> None :
        if len(self.kBuffer) < self.kAddressData.length() :
            self.kBuffer += kBlock[len(self.kBuffer):self.kAddressData.length()]
        #end
    #end

    kAddressData : VMSBackupHelper.addr = None
    kBuffer      : bytes

#end