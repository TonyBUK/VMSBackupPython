import VMSBackupHelper
import BaseHeader

@VMSBackupHelper.static_init
class BBHeader(BaseHeader.BaseHeader) :

    def static_init(self) -> None :

        self.kAddressData = VMSBackupHelper.addr()

        self.kAddressData.add("W_SIZE",         None,                   None,                   VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_OPSYS",        "W_SIZE",               "W_SIZE",               VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_SUBSYS",       "W_OPSYS",              "W_OPSYS",              VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_APPLIC",       "W_SUBSYS",             "W_SUBSYS",             VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("L_NUMBER",       "W_APPLIC",             "W_APPLIC",             VMSBackupHelper.sizeof.uint32_t)
        self.kAddressData.add("FILL_1",         "L_NUMBER",             "L_NUMBER",             VMSBackupHelper.sizeof.int8_t, 20)
        self.kAddressData.add("W_STRUCLEV",     "FILL_1",               "FILL_1",               VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("B_STRUCVER",     "W_STRUCLEV",           None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("B_STRUCLEV",     "B_STRUCVER",           "B_STRUCVER",           VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("W_VOLNUM",       "W_STRUCLEV",           "W_STRUCLEV",           VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("L_CRC",          "W_VOLNUM",             "W_VOLNUM",             VMSBackupHelper.sizeof.uint32_t)
        self.kAddressData.add("L_BLOCKSIZE",    "L_CRC",                "L_CRC",                VMSBackupHelper.sizeof.uint32_t)
        self.kAddressData.add("L_FLAGS",        "L_BLOCKSIZE",          "L_BLOCKSIZE",          VMSBackupHelper.sizeof.uint32_t)
        self.kAddressData.add("V_NOCRC",        "L_FLAGS",              None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("T_SSNAME",       "L_FLAGS",              "L_FLAGS",              VMSBackupHelper.sizeof.int8_t, 32)
        self.kAddressData.add("W_FID",          "T_SSNAME",             "T_SSNAME",             VMSBackupHelper.sizeof.uint16_t, 3)
        self.kAddressData.add("W_FID_NUM",      "W_FID",                None,                   VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_FID_SEQ",      "W_FID_NUM",            "W_FID_NUM",            VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_FID_RVN",      "W_FID_SEQ",            "W_FID_SEQ",            VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("B_FID_RVN",      "W_FID_RVN",            "W_FID_RVN",            VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("B_FID_NMX",      "B_FID_RVN",            "B_FID_RVN",            VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("W_DID",          "W_FID",                None,                   VMSBackupHelper.sizeof.uint16_t, 3)
        self.kAddressData.add("W_DID_NUM",      "W_DID",                None,                   VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_DID_SEQ",      "W_DID_NUM",            "W_DID_NUM",            VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("W_DID_RVN",      "W_DID_SEQ",            "W_DID_SEQ",            VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("B_DID_RVN",      "W_DID_RVN",            None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("B_DID_NMX",      "B_DID_RVN",            "B_DID_RVN",            VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("T_FILENAME",     "W_FID",                "W_FID",                VMSBackupHelper.sizeof.int8_t, 128)
        self.kAddressData.add("B_RTYPE",        "T_FILENAME",           "T_FILENAME",           VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("B_RATTRIB",      "B_RTYPE",              "B_RTYPE",              VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("W_RSIZE",        "B_RATTRIB",            "B_RATTRIB",            VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("B_BKTSIZE",      "W_RSIZE",              "W_RSIZE",              VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("B_VFCSIZE",      "B_BKTSIZE",            "B_BKTSIZE",            VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("W_MAXREC",       "B_VFCSIZE",            "B_VFCSIZE",            VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("L_FILESIZE",     "W_MAXREC",             "W_MAXREC",             VMSBackupHelper.sizeof.uint32_t)
        self.kAddressData.add("T_RESERVED2",    "L_FILESIZE",           "L_FILESIZE",           VMSBackupHelper.sizeof.int8_t, 22)
        self.kAddressData.add("W_CHECKSUM",     "T_RESERVED2",          "T_RESERVED2",          VMSBackupHelper.sizeof.uint16_t)

    #end

    def W_SIZE(self) -> int :
        return self.kAddressData.get("W_SIZE", self.kBuffer)
    #end

    def W_OPSYS(self) -> int :
        return self.kAddressData.get("W_OPSYS", self.kBuffer)
    #end

    def W_SUBSYS(self) -> int :
        return self.kAddressData.get("W_SUBSYS", self.kBuffer)
    #end

    def W_APPLIC(self) -> int :
        return self.kAddressData.get("W_APPLIC", self.kBuffer)
    #end

    def L_NUMBER(self) -> int :
        return self.kAddressData.get("L_NUMBER", self.kBuffer)
    #end

    def W_STRUCLEV(self) -> int :
        return self.kAddressData.get("W_STRUCLEV", self.kBuffer)
    #end

    def B_STRUCVER(self) -> int :
        return self.kAddressData.get("B_STRUCVER", self.kBuffer)
    #end

    def B_STRUCLEV(self) -> int :
        return self.kAddressData.get("B_STRUCLEV", self.kBuffer)
    #end

    def W_VOLNUM(self) -> int :
        return self.kAddressData.get("W_VOLNUM", self.kBuffer)
    #end

    def L_CRC(self) -> int :
        return self.kAddressData.get("L_CRC", self.kBuffer)
    #end

    def L_BLOCKSIZE(self) -> int :
        return self.kAddressData.get("L_BLOCKSIZE", self.kBuffer)
    #end

    def L_FLAGS(self) -> int :
        return self.kAddressData.get("L_FLAGS", self.kBuffer)
    #end

    def V_NOCRC(self) -> int :
        return self.kAddressData.get("V_NOCRC", self.kBuffer)
    #end

    def T_SSNAME(self) -> str :
        return "".join(map(chr,[k for k in self.kAddressData.get("T_SSNAME", self.kBuffer)[1:] if k > 0]))
    #end

    def W_FID(self) -> int :
        return self.kAddressData.get("W_FID", self.kBuffer)
    #end

    def W_FID_NUM(self) -> int :
        return self.kAddressData.get("W_FID_NUM", self.kBuffer)
    #end

    def W_FID_SEQ(self) -> int :
        return self.kAddressData.get("W_FID_SEQ", self.kBuffer)
    #end

    def W_FID_RVN(self) -> int :
        return self.kAddressData.get("W_FID_RVN", self.kBuffer)
    #end

    def B_FID_RVN(self) -> int :
        return self.kAddressData.get("B_FID_RVN", self.kBuffer)
    #end

    def B_FID_NMX(self) -> int :
        return self.kAddressData.get("B_FID_NMX", self.kBuffer)
    #end

    def W_DID(self) -> int :
        return self.kAddressData.get("W_DID", self.kBuffer)
    #end

    def W_DID_NUM(self) -> int :
        return self.kAddressData.get("W_DID_NUM", self.kBuffer)
    #end

    def W_DID_SEQ(self) -> int :
        return self.kAddressData.get("W_DID_SEQ", self.kBuffer)
    #end

    def W_DID_RVN(self) -> int :
        return self.kAddressData.get("W_DID_RVN", self.kBuffer)
    #end

    def B_DID_RVN(self) -> int :
        return self.kAddressData.get("B_DID_RVN", self.kBuffer)
    #end

    def B_DID_NMX(self) -> int :
        return self.kAddressData.get("B_DID_NMX", self.kBuffer)
    #end

    def T_FILENAME(self) -> int :
        return self.kAddressData.get("T_FILENAME", self.kBuffer)
    #end

    def B_RTYPE(self) -> int :
        return self.kAddressData.get("B_RTYPE", self.kBuffer)
    #end

    def B_RATTRIB(self) -> int :
        return self.kAddressData.get("B_RATTRIB", self.kBuffer)
    #end

    def W_RSIZE(self) -> int :
        return self.kAddressData.get("W_RSIZE", self.kBuffer)
    #end

    def B_BKTSIZE(self) -> int :
        return self.kAddressData.get("B_BKTSIZE", self.kBuffer)
    #end

    def B_VFCSIZE(self) -> int :
        return self.kAddressData.get("B_VFCSIZE", self.kBuffer)
    #end

    def W_MAXREC(self) -> int :
        return self.kAddressData.get("W_MAXREC", self.kBuffer)
    #end

    def L_FILESIZE(self) -> int :
        return self.kAddressData.get("L_FILESIZE", self.kBuffer)
    #end

    def W_CHECKSUM(self) -> int :
        return self.kAddressData.get("W_CHECKSUM", self.kBuffer)
    #end

    def GetLength(self) -> bool :

        return (self.W_SIZE())

    #end

    def Validate(self, kBaseHeader) -> bool :

        return (self.L_BLOCKSIZE () == 0) or (self.L_BLOCKSIZE () == kBaseHeader.L_BLOCKSIZE ())

    #end

    kAddressData : VMSBackupHelper.addr
    kBuffer : bytes

#end