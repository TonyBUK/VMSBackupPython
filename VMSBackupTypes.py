import enum
import io
import os

class OutputType(enum.IntEnum):
    SUPPRESS    = 0
    BRIEF       = 1
    FULL        = 2
    CSV         = 3
#end

class ExtractMode(enum.IntEnum):
    SMART       = 0
    ASCII       = 1
    BINARY      = 2
    RAW         = 3
#end

class ExtractDebug(enum.IntEnum):
    NONE        = 0
    BASIC       = 1
    ENHANCED    = 2
#end

class VMSBackupParameters :

    # Verbose Options
    eOutputType             = OutputType.BRIEF

    # Extraction Options
    bExtract                = True

    # Manual selection of Extract Mode

    # Smart Mode auto selects ASCII/Binary per file based on the contents.

    # ASCII Mode will perform file interpretations related to end of line
    # protocols.

    # Binary Mode will extract the data without interpretation with the
    # exception of records, which shall strip the length fields.

    # Raw Mode will extract the data with NO interpreation, leaving records
    # with their length fields intact.
    eExtractMode            = ExtractMode.SMART

    # Extract Mask
    kExtractMask            = "*.*"
    nExtractVersion         = 0 # Set to None to extract all versions

    # Folder Extract
    bExtractFolder          = False

    # Date Extract
    bExtractWithDate        = False

    # Bake Version Number into Filename
    bExtractWithVersion     = False

    # RAM Caching
    bRAMCaching             = False

    # Debug Mode
    eExtractDebug           = ExtractDebug.NONE

#end

class VMSFileParameters :

    def __init__(self, bIsTargetFile : bool, kMode : ExtractMode) :

        self.kMode                  = kMode
        self.bIgnoreVBN             = not bIsTargetFile
        self.bLFDetected            = False
        self.bLastElementWasLFCR    = False
        self.bContainsLFCR          = False
        self.nFilePointer           = 0
        self.nFileSize              = 0
        self.kFormat                = 0
        self.nRemainingStartPos     = 0
        self.nRemainingRecordLength = 0
        self.kFileHandle            = None
        self.kFileName              = ""
        self.kFilePath              = ""
        self.nCreationDate          = 0
        self.nModificationDate      = 0
        self.bExtractWithDates      = False

    #end

    def sanitize(self, kPath : str) :

        # This uses the subset defined here for the portable POSIX file name character set
        # https://www.ibm.com/docs/en/zos/2.1.0?topic=locales-posix-portable-file-name-character-set
        #
        # Note: In addition is we'll allow the following: ;$
        LEGAL = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-" + ";$"

        return "".join([k if k in LEGAL else "_" for k in kPath])

    #end

    def setFileMetaData(self, nFileSize : int, kFormat : int) :

        self.nFileSize              = nFileSize
        self.kFormat                = kFormat

    #end

    def setFileMode(self, kMode : ExtractMode) :

        self.kMode = kMode

    #end

    def getFileMode(self) -> ExtractMode :

        return self.kMode

    #end

    def openFile(self, kFileName : str, kOptions : VMSBackupParameters, nCreationDate : int, nModificationDate : int) :

        # Split the Folder Name
        if "]" in kFileName :
            kFolderName     = kFileName[:kFileName.find("]")]
            assert("[" in kFolderName)
            kFolderName     = kFolderName[kFolderName.find("[") + 1:]
            kFolderStack    = kFolderName.split(".")
            kFileName       = kFileName[(kFileName.find("]") + 1):]
        else :
            kFolderStack    = []
        #end

        # Strip the File Version if needed
        if not kOptions.bExtractWithVersion :
            if ";" in kFileName :
                kFileName = kFileName[:kFileName.find(";")]
            #end
        #end

        # Create the Extraction Folder if Needed
        if kOptions.bExtractFolder :

            kCurrentPath = os.path.abspath(os.curdir)
            kTargetPath  = os.path.join(kCurrentPath, os.path.join(*[self.sanitize(k) for k in kFolderStack]))

            if not os.path.isdir(kTargetPath) :
                os.makedirs(kTargetPath)
            #end
            os.chdir(kTargetPath)
            self.kFilePath = kTargetPath

        #end

        # All Modes are Binary except ASCII which is either explicitly selected, or determined by Smart Parsing
        if ExtractMode.SMART == self.kMode :
            self.kMode = ExtractMode.ASCII
        #end

        # This may seem contrary to ASCII Mode, however, Python is very strict around the validity of data written
        # to files in this mode versus C. In C, ASCII Mode is really just setting the convention for EOL processing,
        # whereas in Python, all string data passed needs to be convertable into the character encoding mechanism,
        # i.e. UTF-8.  As such, it's easier to just open the file in binary mode, and handle EOL's by hand, with the
        # normalisation into the OS preferred EOL convention being handled with os.linesep.
        self.kFileName   = self.sanitize(kFileName)
        self.kFileHandle = open(self.kFileName, "wb")

        # Jump back to the Root Folder
        if kOptions.bExtractFolder :
            os.chdir(kCurrentPath)
        #end

        # Indicate we need to Process the VBN Data Again
        # Note: This is really just an optimisation to skip processing during the parse/scanning phase for any files
        #       that either aren't needed, or have already had their types detected.
        self.bIgnoreVBN             = False

        # Reset the File Pointers
        self.nFilePointer           = 0
        self.nRemainingStartPos     = 0
        self.nRemainingRecordLength = 0

        # Time Stamps
        self.nCreationDate          = nCreationDate
        self.nModificationDate      = nModificationDate
        self.bExtractWithDates      = kOptions.bExtractWithDate

    #end

    def closeFile(self) :

        if None != self.kFileHandle :

            self.kFileHandle.close()
            self.kFileHandle = None

            if self.bExtractWithDates :

                os.utime(os.path.join(self.kFilePath, self.kFileName), (self.nModificationDate, self.nCreationDate))

            #end

        #end

    #end

    kMode                   : ExtractMode
    bIgnoreVBN              : bool

    # Current File Data
    bLFDetected             : bool
    bLastElementWasLFCR     : bool
    bContainsLFCR           : bool
    nFilePointer            : int
    nFileSize               : int
    kFormat                 : int
    nRemainingStartPos      : int
    nRemainingRecordLength  : int
    kFileHandle             : io.TextIOWrapper
    kFileName               : str
    kFilePath               : str
    nCreationDate           : int
    nModificationDate       : int

#end
