import VMSBackupHelper
import BaseHeader
import enum

@VMSBackupHelper.static_init
class BRHeader(BaseHeader.BaseHeader) :

    class RecordType(enum.IntEnum) :
        RECORD_NULL         = 0,    # null record
        RECORD_SUMMARY      = 1,    # BACKUP summary record
        RECORD_VOLUME       = 2,    # volume summary record
        RECORD_FILE         = 3,    # file attribute record
        RECORD_VBN          = 4,    # file virtual block record
        RECORD_PHYSVOL      = 5,    # physical volume attribute record
        RECORD_LBN          = 6,    # physical volume logical block record
        RECORD_FID          = 7,    # file ID record
        RECORD_FILE_EXT     = 8,    # file attribute extension record
        RECORD_LBN_576      = 9,    # 576 byte LBN record
        RECORD_RS_DIRATTR   = 10,   # RSTS directory attribute record
        RECORD_ALIAS        = 11,
        RECORD_MAX_RTYPE    = 12    # max record type

    def static_init(self) -> None :

        self.kAddressData = VMSBackupHelper.addr()

        self.kAddressData.add("W_RSIZE",            None,                   None,                   VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_RTYPE",            "W_RSIZE",              "W_RSIZE",              VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("L_FLAGS",            "W_RTYPE",              "W_RTYPE",              VMSBackupHelper.sizeof.uint32_t)
        self.kAddressData.add("V_BADDATA",          "L_FLAGS",              None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("V_DIRECTORY",        "L_FLAGS",              None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("V_NONSEQUENTIAL",    "L_FLAGS",              None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("V_BLOCKERRS",        "L_FLAGS",              None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("V_ALIAS_ENTRY",      "L_FLAGS",              None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("V_HEADONLY",         "L_FLAGS",              None,                   VMSBackupHelper.sizeof.uint8_t)
        self.kAddressData.add("L_ADDRESS",          "L_FLAGS",              "L_FLAGS",              VMSBackupHelper.sizeof.uint32_t)
        self.kAddressData.add("W_BLOCKFLAGS",       "L_ADDRESS",            "L_ADDRESS",            VMSBackupHelper.sizeof.uint16_t)
        self.kAddressData.add("W_RESERVED",         "W_BLOCKFLAGS",         "W_BLOCKFLAGS",         VMSBackupHelper.sizeof.uint16_t)

    #end

    def W_RSIZE(self) -> int :
        return self.kAddressData.get("W_RSIZE", self.kBuffer)
    #end

    def W_RTYPE(self) -> int :
        return self.kAddressData.get("W_RTYPE", self.kBuffer)
    #end

    def L_FLAGS(self) -> int :
        return self.kAddressData.get("L_FLAGS", self.kBuffer)
    #end

    def V_BADDATA(self) -> bool :
        return (self.kAddressData.get("V_BADDATA", self.kBuffer) & 0x80) == 0x80
    #end

    def V_DIRECTORY(self) -> bool :
        return (self.kAddressData.get("V_DIRECTORY", self.kBuffer) & 0x40) == 0x40
    #end

    def V_NONSEQUENTIAL(self) -> bool :
        return (self.kAddressData.get("V_NONSEQUENTIAL", self.kBuffer) & 0x20) == 0x20
    #end

    def V_BLOCKERRS(self) -> bool :
        return (self.kAddressData.get("V_BLOCKERRS", self.kBuffer) & 0x10) == 0x10
    #end

    def V_ALIAS_ENTRY(self) -> bool :
        return (self.kAddressData.get("V_ALIAS_ENTRY", self.kBuffer) & 0x08) == 0x08
    #end

    def V_HEADONLY(self) -> bool :
        return (self.kAddressData.get("V_HEADONLY", self.kBuffer) & 0x04) == 0x04
    #end

    def L_ADDRESS(self) -> int :
        return self.kAddressData.get("L_ADDRESS", self.kBuffer)
    #end

    def W_BLOCKFLAGS(self) -> int :
        return self.kAddressData.get("W_BLOCKFLAGS", self.kBuffer)
    #end

    def W_RESERVED(self) -> int :
        return self.kAddressData.get("W_RESERVED", self.kBuffer)
    #end

    def GetLength(self) -> bool :

        return (self.kAddressData.length())

    #end

#end