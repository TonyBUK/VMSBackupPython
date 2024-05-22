import os

class VMSBackupRAMCache :

    def __init__(self, bRAMCaching : bool, kFile : str) -> None :

        # Reset the State
        if bRAMCaching :
            self.kRAMCache = bytearray()
        else :
            self.kRAMCache = None
        #end
        self.nFilePointer    = 0

        # Just return the Exception to the caller for now..
        self.kFileHandle = open(kFile, "rb")
        nStart = self.kFileHandle.tell()
        self.kFileHandle.seek(0, os.SEEK_END)
        self.nFileLength = self.kFileHandle.tell() - nStart
        self.kFileHandle.seek(nStart, os.SEEK_SET)

    #end

    # TBD: This really needs to handle "filling in the blanks"
    def read(self, nLength : int) -> bytes :

        if None != self.kRAMCache :

            nCachedFilePointer = self.nFilePointer
            self.nFilePointer += nLength

            if self.nFilePointer >= len(self.kRAMCache) :
                self.kFileHandle.seek(len(self.kRAMCache), os.SEEK_SET)
                self.kRAMCache += self.kFileHandle.read(self.nFilePointer - len(self.kRAMCache))
                if self.nFilePointer > len(self.kRAMCache) :
                    self.nFilePointer  = len(self.kRAMCache)
                #end
            else :
                self.kFileHandle.seek(nLength, os.SEEK_CUR)
            #end
                
            assert(self.nFilePointer == self.kFileHandle.tell())

            return bytes(self.kRAMCache[nCachedFilePointer:nCachedFilePointer + nLength])


        else :

            return self.kFileHandle.read(nLength)

        #end

    #end

    def seek(self, nOffset : int, nWhence : int) :

        # I may revisit this, but for now just have the OS do all the hard work when seeking
        self.kFileHandle.seek(nOffset, nWhence)
        if None != self.kRAMCache :
            self.nFilePointer = self.kFileHandle.tell()
        #end

    #end
            
    def feof(self) :
        return self.tell() >= self.nFileLength
    #end

    def tell(self) -> int :
        if None != self.kRAMCache :
            return self.nFilePointer
        else :
            return self.kFileHandle.tell()
        #end
    #end

    def close(self) :
        self.kFileHandle.close()
    #end

    kRAMCache       = None
    nFilePointer    = 0
    nFileLength     = 0
    kFileHandle     = None

#end