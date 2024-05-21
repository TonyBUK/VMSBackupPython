import BSAHeader
import VMSBackupHelper
import enum
import struct

class BSFileHeader :

    class RecordFormatType(enum.IntEnum) :

        RECORD_FORMAT_UDF   = 0,    # undefined
        RECORD_FORMAT_FIX   = 1,    # fixed-length record
        RECORD_FORMAT_VAR   = 2,    # variable-length record
        RECORD_FORMAT_VFC   = 3,    # variable-length with fixed-length control record
        RECORD_FORMAT_STM   = 4,    # RMS-11 stream record (valid only for sequential org)
        RECORD_FORMAT_STMLF = 5,    # stream record delimited by LF (sequential org only)
        RECORD_FORMAT_STMCR = 6     # stream record delimited by CR (sequential org only)

    #end

    class RecordAttributeType(enum.IntEnum) :

        RECORD_ATTRIBUTE_FTN    = 0,    # FORTRAN carriage control character
        RECORD_ATTRIBUTE_CR     = 1,    # line feed - record -carriage return
        RECORD_ATTRIBUTE_CRN    = 2,    # carriage control
        RECORD_ATTRIBUTE_BLK    = 3,    # records don't cross block boundaries
        RECORD_ATTRIBUTE_PRN    = 4     # print-file carriage control

    #end

    class FileHeaderType(enum.IntEnum) :

        FILENAME    = 42,   # file name
        STRUCLEV    = 43,   # file structure level
        FID         = 44,   # file ID
        BACKLINK    = 45,   # directory ID back link
        FILESIZE    = 46,   # file size in blocks
        UIC         = 47,   # file owner UIC
        FPRO        = 48,   # file protection mask
        RPRO        = 49,   # record protection mask
        ACLEVEL     = 50,   # access level
        UCHAR       = 51,   # file characteristics
        RECATTR     = 52,   # record attributes area
        REVISION    = 53,   # revision number
        CREDATE     = 54,   # creation date
        REVDATE     = 55,   # revision date
        EXPDATE     = 56,   # expiration date
        BAKDATE     = 57,   # backup date

        VERLIMIT    = 75,   # (FA) File version limit
        HIGHWATER   = 79    # (FA) Highwater mark

    #end

    def __init__(self) -> None :

        self.kFILENAME  = None
        self.kSTRUCLEV  = None
        self.kFID       = None
        self.kBACKLINK  = None
        self.kFILESIZE  = None
        self.kUIC       = None
        self.kFPRO      = None
        self.kRPRO      = None
        self.kACLEVEL   = None
        self.kUCHAR     = None
        self.kRECATTR   = None
        self.kREVISION  = None
        self.kCREDATE   = None
        self.kREVDATE   = None
        self.kEXPDATE   = None
        self.kBAKDATE   = None
        self.kVERLIMIT  = None
        self.kHIGHWATER = None

    #end

    def LoadHeaderFromBuffer(self, kBlock : bytes, nRSize : int) :

        nAddress = 2

        while nAddress < nRSize :

            # Initially the Block is unidentified
            kUnidentified = BSAHeader.BSAHeader()

            if len(kBlock[nAddress:]) < kUnidentified.GetLength() : break

            kUnidentified.LoadHeaderFromBuffer(kBlock=kBlock[nAddress:])

            # Increment the Address
            nAddress += kUnidentified.GetLength()

            # Determine the Block Type
            kBlockType = kUnidentified.W_TYPE()

            if BSFileHeader.FileHeaderType.FILENAME == kBlockType :
                self.kFILENAME = kUnidentified
            elif BSFileHeader.FileHeaderType.STRUCLEV == kBlockType :
                self.kSTRUCLEV = kUnidentified
            elif BSFileHeader.FileHeaderType.FID == kBlockType :
                self.kFID = kUnidentified
            elif BSFileHeader.FileHeaderType.BACKLINK == kBlockType :
                self.kBACKLINK = kUnidentified
            elif BSFileHeader.FileHeaderType.FILESIZE == kBlockType :
                self.kFILESIZE = kUnidentified
            elif BSFileHeader.FileHeaderType.UIC == kBlockType :
                self.kUIC = kUnidentified
            elif BSFileHeader.FileHeaderType.FPRO == kBlockType :
                self.kFPRO = kUnidentified
            elif BSFileHeader.FileHeaderType.RPRO == kBlockType :
                self.kRPRO = kUnidentified
            elif BSFileHeader.FileHeaderType.ACLEVEL == kBlockType :
                self.kACLEVEL = kUnidentified
            elif BSFileHeader.FileHeaderType.UCHAR == kBlockType :
                self.kUCHAR = kUnidentified
            elif BSFileHeader.FileHeaderType.RECATTR == kBlockType :
                self.kRECATTR = kUnidentified
            elif BSFileHeader.FileHeaderType.REVISION == kBlockType :
                self.kREVISION = kUnidentified
            elif BSFileHeader.FileHeaderType.CREDATE == kBlockType :
                self.kCREDATE = kUnidentified
            elif BSFileHeader.FileHeaderType.REVDATE == kBlockType :
                self.kREVDATE = kUnidentified
            elif BSFileHeader.FileHeaderType.EXPDATE == kBlockType :
                self.kEXPDATE = kUnidentified
            elif BSFileHeader.FileHeaderType.BAKDATE == kBlockType :
                self.kBAKDATE = kUnidentified
            elif BSFileHeader.FileHeaderType.VERLIMIT == kBlockType :
                self.kVERLIMIT = kUnidentified
            elif BSFileHeader.FileHeaderType.HIGHWATER == kBlockType :
                self.kHIGHWATER = kUnidentified
            #end

        #end

    #end

    def FILENAME(self) -> str :
        if None != self.kFILENAME :
            return "".join(map(chr, self.kFILENAME.T_TEXT()))
        else :
            return ""
        #end
    #end

    def STRUCLEV(self) -> list[int] :
        if None != self.kSTRUCLEV :
            return self.kSTRUCLEV.T_TEXT()
        else :
            return ""
        #end
    #end

    def FID(self) -> list[int] :
        if None != self.kFID :
            kText   = bytes(self.kFID.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint16_t.name]
            return struct.unpack(kFormat[0] + str(len(kText) // 2) + kFormat[1], kText)
        else :
            return []
        #end
    #end

    def FILESIZE(self) -> int :
        if None != self.kFILESIZE :
            kText   = bytes(self.kFILESIZE.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint32_t.name]
            return struct.unpack(kFormat, kText)[0]
        else :
            return 0
        #end
    #end

    def UIC(self) -> list[int] :
        if None != self.kUIC :
            kText   = bytes(self.kUIC.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint16_t.name]
            return struct.unpack(kFormat[0] + str(len(kText) // 2) + kFormat[1], kText)
        else :
            return []
        #end
    #end

    def FPRO(self) -> list[int] :
        if None != self.kFPRO :
            kText   = bytes(self.kFPRO.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint8_t.name]
            return struct.unpack(kFormat[0] + str(len(kText)) + kFormat[1], kText)
        else :
            return []
        #end
    #end

    def UCHAR(self) -> list[int] :
        if None != self.kUCHAR :
            kText   = bytes(self.kUCHAR.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint16_t.name]
            return struct.unpack(kFormat[0] + str(len(kText) // 2) + kFormat[1], kText)
        else :
            return []
        #end
    #end

    def RECATTR(self, kSizeOf : VMSBackupHelper.sizeof = VMSBackupHelper.sizeof.uint8_t) -> list[int] :
        if None != self.kRECATTR :
            kText   = bytes(self.kRECATTR.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[kSizeOf.name]
            return struct.unpack(kFormat[0] + str(len(kText) // kSizeOf.getValue()) + kFormat[1], kText)
        else :
            return []
        #end
    #end

    # TODO: Should this 512 be defined somewhere?
    def FILESIZEBYTES(self) -> int :
        kRECATTR = self.RECATTR(kSizeOf=VMSBackupHelper.sizeof.uint16_t)
        return (kRECATTR[5] * 512) - 512 + kRECATTR[6]
    #end

    def RECSIZE(self) -> int :
        return self.RECATTR(kSizeOf=VMSBackupHelper.sizeof.uint16_t)[1]
    #end

    def REVISION(self) -> int :
        if None != self.kREVISION :
            kText   = bytes(self.kREVISION.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint16_t.name]
            return struct.unpack(kFormat, kText)[0]
        else :
            return 0
        #end
    #end

    def CREDATE(self) -> int :
        if None != self.kCREDATE :
            kText   = bytes(self.kCREDATE.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.int64_t.name]
            return struct.unpack(kFormat, kText)[0]
        else :
            return 0
        #end
    #end

    def REVDATE(self) -> int :
        if None != self.kREVDATE :
            kText   = bytes(self.kREVDATE.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.int64_t.name]
            return struct.unpack(kFormat, kText)[0]
        else :
            return 0
        #end
    #end

    def EXPDATE(self) -> int :
        if None != self.kEXPDATE :
            kText   = bytes(self.kEXPDATE.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.int64_t.name]
            return struct.unpack(kFormat, kText)[0]
        else :
            return 0
        #end
    #end

    def BAKDATE(self) -> int :
        if None != self.kBAKDATE :
            kText   = bytes(self.kBAKDATE.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.int64_t.name]
            return struct.unpack(kFormat, kText)[0]
        else :
            return 0
        #end
    #end

    def VERLIMIT(self) -> int :
        if None != self.kVERLIMIT :
            kText   = bytes(self.kVERLIMIT.T_TEXT())
            kFormat = VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint16_t.name]
            return struct.unpack(kFormat, kText)[0]
        else :
            return 0
        #end
    #end

    kFILENAME   : BSAHeader.BSAHeader
    kSTRUCLEV   : BSAHeader.BSAHeader
    kFID        : BSAHeader.BSAHeader
    kBACKLINK   : BSAHeader.BSAHeader
    kFILESIZE   : BSAHeader.BSAHeader
    kUIC        : BSAHeader.BSAHeader
    kFPRO       : BSAHeader.BSAHeader
    kRPRO       : BSAHeader.BSAHeader
    kACLEVEL    : BSAHeader.BSAHeader
    kUCHAR      : BSAHeader.BSAHeader
    kRECATTR    : BSAHeader.BSAHeader
    kREVISION   : BSAHeader.BSAHeader
    kCREDATE    : BSAHeader.BSAHeader
    kREVDATE    : BSAHeader.BSAHeader
    kEXPDATE    : BSAHeader.BSAHeader
    kBAKDATE    : BSAHeader.BSAHeader
    kVERLIMIT   : BSAHeader.BSAHeader
    kHIGHWATER  : BSAHeader.BSAHeader

#end