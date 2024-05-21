import VMSBackupRAMCache
import VMSBackupTypes
import VMSBackupHelper

import BBHeader
import BRHeader
import BSFileHeader

import os
import sys
import fnmatch
import datetime
import math
import struct

def FileNameWildCardCompare(kString : str, kWildCard : str) :

    # [] are frequently used in OpenVMS filenames, but to fnmatch, indicate ranges.
    # Since we're only dealing with filenames, and the rest basically works, we can
    # mitigate the issue somewhat.
    kString   = kString.replace  ("[", "<").replace("]", ">")
    kWildCard = kWildCard.replace("[", "<").replace("]", ">")

    return fnmatch.fnmatch(name=kString, pat=kWildCard)

#end

def VMSWriteEOL(kFileMetaData : VMSBackupTypes.VMSFileParameters, bForceEOL : bool = False) :

    if VMSBackupTypes.ExtractMode.ASCII == kFileMetaData.kMode :

        if (kFileMetaData.nFilePointer >= kFileMetaData.nFileSize) and kFileMetaData.bLFDetected :

            kFileMetaData.kFileHandle.write(bytes([ord(k) for k in os.linesep]))
            kFileMetaData.bLFDetected = False

        elif bForceEOL :

            kFileMetaData.kFileHandle.write(bytes([ord(k) for k in os.linesep]))

        #end

    #end

#end

def VMSWriteFile(kBlock : bytes, kFileMetaData : VMSBackupTypes.VMSFileParameters, nDataLength : int) :

    bLastElementWasLFCR = False
    bContainsLFCR       = False

    if VMSBackupTypes.ExtractMode.ASCII == kFileMetaData.kMode :

        for i,nByte in enumerate(kBlock[:nDataLength]) :

            if (nByte == ord('\r')) and not kFileMetaData.bLFDetected :

                # Do nothing whilst the EOL is assessed
                kFileMetaData.bLFDetected   = True

                # Indicate this data package contains an LF/CR entry
                bContainsLFCR               = True
                bLastElementWasLFCR         = (i+1) == nDataLength

            elif (nByte == ord('\n')) and kFileMetaData.bLFDetected :
            
                # This file already contains standard EOL conventions
                kFileMetaData.kFileHandle.write(bytes([ord(k) for k in os.linesep]))
                kFileMetaData.bLFDetected = False

                # Indicate this data package contains an LF/CR entry
                bContainsLFCR               = True
                bLastElementWasLFCR         = (i+1) == nDataLength

            elif (nByte == ord('\n')) and not kFileMetaData.bLFDetected :
            
                # This is not seen as a valid EOL, so normalise it
                kFileMetaData.kFileHandle.write(bytes([ord(k) for k in os.linesep]))
                kFileMetaData.bLFDetected = False

                # Indicate this data package contains an LF/CR entry
                bContainsLFCR               = True
                bLastElementWasLFCR         = (i+1) == nDataLength

            elif (nByte != ord('\n')) and kFileMetaData.bLFDetected :
            
                # This is not seen as a valid EOL, so normalise it
                kFileMetaData.kFileHandle.write(bytes([ord(k) for k in os.linesep]))
                kFileMetaData.bLFDetected = False

                # Indicate this data package contains an LF/CR entry
                bContainsLFCR               = True
                
                # Note: This indicates the *previous* byte was an LF/CR therefore the current
                #       element isn't, hence no check to see if the Last Element is an LF/CR
                
                # Output the current byte since it contained non-EOL data
                kFileMetaData.kFileHandle.write(bytes([nByte]))

            else :

                # Output the Current Byte
                kFileMetaData.kFileHandle.write(bytes([nByte]))

            #end

        #end

    else :

        kFileMetaData.kFileHandle.write(kBlock[:nDataLength])

    #end
        
    kFileMetaData.bContainsLFCR       = bContainsLFCR
    kFileMetaData.bLastElementWasLFCR = bLastElementWasLFCR

#end

def CloseOpenFiles(kExtractStatus : dict) :

    if None != kExtractStatus["Current"] :
        if None != kExtractStatus["Current"].kFileHandle :
            if kExtractStatus["Current"].nFilePointer != kExtractStatus["Current"].nFileSize :
                print(f"Warning: {kExtractStatus["Current"].kFileName} extracted {kExtractStatus["Current"].nFilePointer}/{kExtractStatus["Current"].nFileSize} bytes.")
            #end
#            assert(kExtractStatus["Current"].nFilePointer == kExtractStatus["Current"].nFileSize)
            kExtractStatus["Current"].closeFile()
            kExtractStatus["Current"] = None
        #end
    #end

#end

# TODO: This works for the 1st Jan 1970 Epoch, however, I really need to determine the time functions
#       don't actually mandate this, for example, the national instruments time functions actually used
#       a different epoch last time I used them, as such, this needs to calculate the true offset between
#       the VMS Time Epoch and the used Unix Epoch, however, 1st Jan 1970 is ubiquitous enough that this
#       should be correct for most people.

def TimeVMSToUnix(nVMSTime : int) -> int :
    
    return (nVMSTime - 0x07c95674beb4000) // 10000000

#end

def DecodeTimeAndDate (nVMSTime : int, nSubSecondResolution : int) -> str :

    ##########################################################
    # Constants

    MONTH = ["JAN", "FEB", "MAR", "APR",
             "MAY", "JUN", "JUL", "AUG",
             "SEP", "OCT", "NOV", "DEC"]

    ##########################################################
    # Variables

    # Open VMS Time is a 64 Bit value representing 100ns tics since 00:00 November 17, 1858
    # (Modified Julian Day Zero)
    # http://h71000.www7.hp.com/wizard/wiz_2315.html

    # C Time Stamp is a 32 Bit value representing seconds since January 1 1970

    if 0 == nVMSTime :
        return "<None Specified>"
    else :

        # Convert time to GM Time
        nUnixTime = TimeVMSToUnix(nVMSTime)
        kGMTTime = datetime.datetime.fromtimestamp(nUnixTime, tz=datetime.timezone.utc)

        # Configure the Common Part of the Date String
        kDateString = f"{kGMTTime.day}-{MONTH[kGMTTime.month-1]}-{kGMTTime.year} {kGMTTime.hour:02}:{kGMTTime.minute:02}:{kGMTTime.second:02}"

        if 0 == nSubSecondResolution :
            # Output the Date/Time to match the Open VMS directory listing
            return kDateString
        else :
            # The above algorithm will only have a resolution of seconds, therefore
            # extra processing is required in order to get milliseconds
            
            # VMS Time has an LSB of 100ns
            # Convert to Hundredths of a Second
            nTimeSubSeconds = int((nVMSTime % 10000000) // math.pow(10, 7 - nSubSecondResolution))
            return kDateString + f".{nTimeSubSeconds:02}"
        #end

    #end

#end

def DecodeFileProtection(nValue : int) -> str :

    kReturnString = ""

    if 0 == (nValue & 0x1) : kReturnString += "R"
    if 0 == (nValue & 0x2) : kReturnString += "W"
    if 0 == (nValue & 0x4) : kReturnString += "E"
    if 0 == (nValue & 0x8) : kReturnString += "D"

    return kReturnString

#end

def DecodeRecordFormat(nValue : int, nSize : int) -> str :

    nValue = nValue & 0xF
    if BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_UDF == nValue :
        return ""
    elif BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_FIX == nValue :
        return "Fixed length 512 byte records"
    elif BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_VAR == nValue :
        return "Variable length" + (f", maximum {nSize} bytes" if (0 != nSize) else "")
    elif BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_VFC == nValue :
        return "VFC, 2 byte header" + (f", maximum {nSize} bytes" if (0 != nSize) else "")
    elif BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_STM == nValue :
        return "Stream" + (f", maximum {nSize} bytes" if (0 != nSize) else "")
    elif BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_STMLF == nValue :
        return "Stream_LF" + (f", maximum {nSize} bytes" if (0 != nSize) else "")
    elif BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_STMCR == nValue :
        return "Stream_CR" + (f", maximum {nSize} bytes" if (0 != nSize) else "")
    #end
    
    return ""

#end

def DecodeRecordAttributes(nValue : int, bFirstPass : bool) -> str :

    if BSFileHeader.BSFileHeader.RecordAttributeType.RECORD_ATTRIBUTE_FTN == nValue :
        return "None"
    elif BSFileHeader.BSFileHeader.RecordAttributeType.RECORD_ATTRIBUTE_CR == nValue :
        return ""
    elif BSFileHeader.BSFileHeader.RecordAttributeType.RECORD_ATTRIBUTE_CRN == nValue :
        return "Carriage return carriage control"
    elif BSFileHeader.BSFileHeader.RecordAttributeType.RECORD_ATTRIBUTE_BLK == nValue :
        return ""
    elif BSFileHeader.BSFileHeader.RecordAttributeType.RECORD_ATTRIBUTE_PRN == nValue :
        return "Print file carriage control"
    elif not bFirstPass :
        return f"WARNING : Unknown attribute {nValue}"
    #end

    return ""

#end

def DumpHeader(kHeader : BBHeader.BBHeader, kOptions : VMSBackupTypes.VMSBackupParameters) :
    print(f"Save set:          {kHeader.T_SSNAME()}")
    print(f"Block size:        {kHeader.L_BLOCKSIZE()}")
    print("")
#end

def DumpBriefFileHeader(kFileHeader : BSFileHeader.BSFileHeader, nSubSecondResolution : int) :

    # Output the File Name
    print(f"{kFileHeader.FILENAME()}")

    # Output the File Size
    kRECATTR = kFileHeader.RECATTR(kSizeOf=VMSBackupHelper.sizeof.uint16_t)
    if kRECATTR[6] == 0 :
        print(f"                      Size: {kRECATTR[5] - 1:7}/{kFileHeader.FILESIZE():<7}", end="")
    else :
        print(f"                      Size: {kRECATTR[5]:7}/{kFileHeader.FILESIZE():<7}", end="")
    #end

    # Output the Creation Date
    print(f"   Created: {DecodeTimeAndDate(nVMSTime=kFileHeader.CREDATE(), nSubSecondResolution=nSubSecondResolution)}")

#end

def DumpFullFileHeader(kFileHeader : BSFileHeader.BSFileHeader, kHeader : BRHeader.BRHeader, bFirstPass : bool) :

    # TO BE CLEANED
    # Change False to True to have the output format match a directory /full syntax, otherwise it will
    # match a backup set view.

    if True :

        ##########################################################
        # Dump the Full File Header (Directory Format)
        
        # Output the File Name
        print(f"{kFileHeader.FILENAME()}", end="")

        # Output the File Id
        print(f"                  File ID:  ({kFileHeader.FID()[0]},{kFileHeader.FID()[1]},{kFileHeader.FID()[2] - 1})")

        # Output the File Size
        kRECATTR = kFileHeader.RECATTR(kSizeOf=VMSBackupHelper.sizeof.uint16_t)
        if kRECATTR[6] == 0 :
            print(f"Size: {(kRECATTR[5] - 1):12}/{kFileHeader.FILESIZE():<12}", end="")
        else :
            print(f"Size: {kRECATTR[5]:12}/{kFileHeader.FILESIZE():<12}", end="")
        #end

        # Output the Owner
        print(f"Owner: [{kFileHeader.UIC()[1]:06o},{kFileHeader.UIC()[0]:06o}]")

        # Output the Creation Date
        print(f"Created:  {DecodeTimeAndDate(nVMSTime=kFileHeader.CREDATE(), nSubSecondResolution=2)}")

        # Output the Revised Date
        print(f"Revised:  {DecodeTimeAndDate(nVMSTime=kFileHeader.REVDATE(), nSubSecondResolution=2)} ({kFileHeader.REVISION()})")

        # Output the Expiry Date
        print(f"Expires:  {DecodeTimeAndDate(nVMSTime=kFileHeader.EXPDATE(), nSubSecondResolution=2)}")

        # Output the Backup Date
        print(f"Backup:  {DecodeTimeAndDate(nVMSTime=kFileHeader.BAKDATE(), nSubSecondResolution=2)}")

        # Output File Organisation
        # TODO: Not enough data collated to determine other enumerations
        print("File organization:  ", end="")

        if not kHeader.V_NONSEQUENTIAL() :
            print("Sequential")
        else :
            print("????")
        #end

        # File Attributes
        print("File attributes:    ", end="")

        # File Attributes - Allocation
        print(f"Allocation: {kFileHeader.FILESIZE()}", end="")

        # File Attributes - Extend
        # TODO: No Idea, always 0
        print(", Extend: 0", end="")

        # File Attributes - Global Buffer Count
        # TODO: No Idea, always 0
        print(", Global Buffer Count: 0", end="")

        # File Attributes - , Version Limit
        print(f", Version limit: {kFileHeader.VERLIMIT()}", end="")

        # File Attributes - ????
        # TODO: No Idea, sometimes ", Contiguous-best-try", the check below seems to
        #       work for test data
        if 32 == kFileHeader.UCHAR()[0] :
            print(", Contiguous best try")
        else :
            print("")
        #end

        # Record Format
        print(f"  Record format:      {DecodeRecordFormat(nValue=kFileHeader.RECATTR()[0], nSize=kFileHeader.RECSIZE())}")

        # Record Attributes
        print(f"  Record attributes:  {DecodeRecordAttributes(nValue=kFileHeader.RECATTR()[1], bFirstPass=bFirstPass)}")

        # Output File Protection
        print("  File protection:    ", end="")
        print(f"System:{DecodeFileProtection(nValue=kFileHeader.FPRO()[0])}", end="")
        print(f", Owner:{DecodeFileProtection(nValue=kFileHeader.FPRO()[0] >> 4)}", end="")
        print(f", Group:{DecodeFileProtection(nValue=kFileHeader.FPRO()[1])}", end="")
        print(f", World:{DecodeFileProtection(nValue=kFileHeader.FPRO()[1] >> 4)}", end="")
        print("")

    else :

        DumpBriefFileHeader(kFileHeader=kFileHeader, nSubSecondResolution=0)

        # Output the Owner
        print(f"                      Owner: [{kFileHeader.UIC()[1]:06o},{kFileHeader.UIC()[0]:06o}]  ", end="")

        # Output the Revised Date
        print(f"Revised: {DecodeTimeAndDate(nVMSTime=kFileHeader.REVDATE(), nSubSecondResolution=0)} ({kFileHeader.REVISION()})")

        # Output the File Id
        # Note : As a quirk, we actually cut the string if it's too wide
        print("                      File ID: " + f"({kFileHeader.FID()[0]},{kFileHeader.FID()[1]},{kFileHeader.FID()[2] - 1})              "[:14], end="")

        # Output the Expiry Date
        print(f" Expires: {DecodeTimeAndDate(nVMSTime=kFileHeader.EXPDATE(), nSubSecondResolution=0)}")

        # Output the Backup Date
        print(f"                                              Backup:  {DecodeTimeAndDate(nVMSTime=kFileHeader.BAKDATE(), nSubSecondResolution=0)}")

        # Output File Protection
        print("  File protection:    ", end="")
        print(f"System:{DecodeFileProtection(nValue=kFileHeader.FPRO()[0])}", end="")
        print(f", Owner:{DecodeFileProtection(nValue=kFileHeader.FPRO()[0] >> 4)}", end="")
        print(f", Group:{DecodeFileProtection(nValue=kFileHeader.FPRO()[1])}", end="")
        print(f", World:{DecodeFileProtection(nValue=kFileHeader.FPRO()[1] >> 4)}", end="")
        print("")

        # Output File Organisation
        # TODO: Not enough data collated to determine other enumerations
        print("  File organization:  ", end="")

        if not kHeader.V_NONSEQUENTIAL() :
            print("Sequential")
        else :
            print("????")
        #end

        # File Attributes
        print("  File attributes:    ", end="")

        # File Attributes - Allocation
        print(f"Allocation = {kFileHeader.FILESIZE()}", end="")

        # File Attributes - Extend
        # TODO: No Idea, always 0
        print(", Extend = 0")

        # File Attributes - Global Buffer Count
        # TODO: No Idea, always 0
        print("                      Global Buffer Count = 0", end="")

        # File Attributes - ????
        # TODO: No Idea, sometimes ", Contiguous-best-try", the check below seems to
        #       work for test data
        if 32 == kFileHeader.UCHAR()[0] :
            print(", Contiguous best try")
        else :
            print("")
        #end

        # Record Format
        print(f"  Record format:      {DecodeRecordFormat(nValue=kFileHeader.RECATTR()[0], nSize=kFileHeader.RECSIZE())}")

        # Record Attributes
        print(f"  Record attributes:  {DecodeRecordAttributes(nValue=kFileHeader.RECATTR()[1], bFirstPass=bFirstPass)}")

    #end

#end

def DumpCSVFileHeader(kFileHeader : BSFileHeader.BSFileHeader, kHeader : BRHeader.BRHeader, bFirstPass : bool) :

    # Output the File Name
    print(f"\"{kFileHeader.FILENAME()}\",", end="")

    # Output the File Size
    kRECATTR = kFileHeader.RECATTR(kSizeOf=VMSBackupHelper.sizeof.uint16_t)
    if kRECATTR[6] == 0 :
        print(f"{(kRECATTR[5] - 1)},{kFileHeader.FILESIZE()},", end="")
    else :
        print(f"{(kRECATTR[5] - 0)},{kFileHeader.FILESIZE()},", end="")
    #end

    # Output the Creation Date
    print(f"\"{DecodeTimeAndDate(nVMSTime=kFileHeader.CREDATE(), nSubSecondResolution=7)}\",", end="")

    # Output the Owner
    print(f"{kFileHeader.UIC()[1]:06o},{kFileHeader.UIC()[0]:06o},", end="")

    # Output the Revised Date
    print(f"\"{DecodeTimeAndDate(nVMSTime=kFileHeader.REVDATE(), nSubSecondResolution=7)}\",{kFileHeader.REVISION()},", end="")

    # Output the File Id
    print(f"{kFileHeader.FID()[0]},{kFileHeader.FID()[1]},{kFileHeader.FID()[2]},", end="")

    # Output the Expiry Date
    print(f"\"{DecodeTimeAndDate(nVMSTime=kFileHeader.EXPDATE(), nSubSecondResolution=7)}\",", end="")

    # Output the Backup Date
    print(f"\"{DecodeTimeAndDate(nVMSTime=kFileHeader.BAKDATE(), nSubSecondResolution=7)}\",", end="")

    # Output File Protection
    print(f"\"{DecodeFileProtection(nValue=kFileHeader.FPRO()[0]     )}\",", end="")
    print(f"\"{DecodeFileProtection(nValue=kFileHeader.FPRO()[0] >> 4)}\",", end="")
    print(f"\"{DecodeFileProtection(nValue=kFileHeader.FPRO()[1]     )}\",", end="")
    print(f"\"{DecodeFileProtection(nValue=kFileHeader.FPRO()[1] >> 4)}\",", end="")

    # Output File Organisation
    # TODO: Not enough data collated to determine other enumerations
    if not kHeader.V_NONSEQUENTIAL() :
        print("Sequential,", end="")
    else :
        print("????,", end="")
    #end

    # File Attributes
    
    # File Attributes - Allocation
    print(f"{kFileHeader.FILESIZE()},", end="")

    # File Attributes - Extend
    # TODO: No Idea, always 0
    print("0,", end="")

    # File Attributes - Global Buffer Count
    # TODO: No Idea, always 0
    print("0,", end="")

    # File Attributes - ????
    # TODO: No Idea, sometimes ", Contiguous-best-try", the check below seems to
    #       work for test data
    if 32 == kFileHeader.UCHAR()[0] :
        print("Contiguous best try,", end="")
    else :
        print(",", end="")
    #end

    # Record Format
    print(f"\"{DecodeRecordFormat(nValue=kFileHeader.RECATTR()[0], nSize=kFileHeader.RECSIZE())}\",", end="")

    # Record Attributes
    print(f"\"{DecodeRecordAttributes(nValue=kFileHeader.RECATTR()[1], bFirstPass=bFirstPass)}\"", end="")

    print("")

#end

def SetNewerFile(kFileName : str, nFileVersion : int, kFileList : dict) :

    if kFileName not in kFileList :

        # By Default this must be the latest version
        kFileList[kFileName] = {"Version" : nFileVersion}

    else :

        # Determine if this is a later version
        if nFileVersion >= kFileList[kFileName]["Version"] :
            kFileList[kFileName]["Version"]  = nFileVersion
        #end

    #end

#end

def IsTargetFile(kFileName : str, nFileVersion : int, nTargetExtractVersion : int, kFileList : dict) -> bool :

    assert(kFileName in kFileList)

    # None represents "*"
    if None == nTargetExtractVersion :

        return True
    
    else :

        # Determine if this version is correct
        if nTargetExtractVersion > 0 :

            # Version must be exact
            return nTargetExtractVersion == nFileVersion

        else :

            # This is a relative version
            # So ;0 means it must be the latest version
            #    ;-1 means it must be the version prior to the latest
            # etc.
            return (kFileList[kFileName]["Version"] + nTargetExtractVersion) == nFileVersion

        #end

    #end

#end

def VMSBackupProcessFile(kBlock : bytes, kHeader : BRHeader.BRHeader, kOptions : VMSBackupTypes.VMSBackupParameters, kFileList : dict, kExtractStatus : dict, bFirstPass : bool) :

    ##########################################################
    # Convert the File Record into a series of streams

    kFileHeader = BSFileHeader.BSFileHeader()
    kFileHeader.LoadHeaderFromBuffer(kBlock=kBlock, nRSize=kHeader.W_RSIZE())

    # Copy the File Name
    kFileNameNoMask = kFileHeader.FILENAME()

    # Strip the Version Delimiter if required
    nFileVersion = 0
    if ";" in kFileNameNoMask :
        nSemiPos        = kFileNameNoMask.find(";")
        nFileVersion    = int(kFileNameNoMask[nSemiPos+1:])
        kFileNameNoMask = kFileNameNoMask[:nSemiPos]
    #end

    # See if this is a file that needs processing
    bWildCardMatch = FileNameWildCardCompare(kString=kFileNameNoMask, kWildCard=kOptions.kExtractMask)

    ##########################################################
    # Handle Older Versions

    if bWildCardMatch :

        SetNewerFile(kFileName=kFileNameNoMask, nFileVersion=nFileVersion, kFileList=kFileList)
        bTargetFile = IsTargetFile(kFileName=kFileNameNoMask, nFileVersion=nFileVersion, nTargetExtractVersion=kOptions.nExtractVersion, kFileList=kFileList)

    else :

        bTargetFile = False

    #end

    # Add the Filename to the List to Process
    if kFileHeader.FILENAME() not in kFileList :

        # Add the Raw File Parameters to the List
        # TODO: RECATTR[0] occasionally has a value outside the range defined by RecordFormatType.  I've mitigated it for now by masking
        #       the lower nibble, but I've no way of knowing if this is accurate for the time being.
        kFileList[kFileHeader.FILENAME()] = VMSBackupTypes.VMSFileParameters(bIsTargetFile=bTargetFile, kMode=kOptions.eExtractMode)
        kFileList[kFileHeader.FILENAME()].setFileMetaData(nFileSize=kFileHeader.FILESIZEBYTES(), kFormat=kFileHeader.RECATTR()[0] & 0x0F)

    #end

    ##########################################################
    # Handle Data Extraction if required

    if kOptions.bExtract :

        if bTargetFile :

            # Initialise the File Type

            if  (VMSBackupTypes.ExtractMode.SMART == kOptions.eExtractMode) and bFirstPass and bTargetFile :

                ##########################################################
                # DEBUG (ENHANCED)

                if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

                    print("*** DEBUG *** ", end="")
                    print(f"Beginning smart parse for {kFileHeader.FILENAME()}")

                #end

                # DEBUG (ENHANCED)
                ##########################################################

            elif bTargetFile :

                ##########################################################
                # DEBUG (ENHANCED)

                if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

                    print("*** DEBUG *** ", end="")
                    print(f"Beginning parse/extract for {kFileHeader.FILENAME()}")

                #end

                # DEBUG (ENHANCED)
                ##########################################################

            #end

            # Close any open files
            CloseOpenFiles(kExtractStatus=kExtractStatus)

            # Set the Current Item of Interest
            kExtractStatus["Current"] = kFileList[kFileHeader.FILENAME()]

            # If this is not the first pass (or we're in single pass mode)
            if not bFirstPass and bTargetFile :

                # DEBUG (ENHANCED)
                ##########################################################

                # Open the File for Writing
                kExtractStatus["Current"].openFile(kFileName=kFileHeader.FILENAME(), kOptions=kOptions, nCreationDate=TimeVMSToUnix(nVMSTime=kFileHeader.CREDATE()), nModificationDate=TimeVMSToUnix(nVMSTime=kFileHeader.REVDATE()))

                ##########################################################
                # DEBUG (ENHANCED)

                if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

                    print("*** DEBUG *** ", end="")
                    print(f"Using {[None, "ASCII", "BINARY", "RAW"][kExtractStatus["Current"].kMode]} for {kFileHeader.FILENAME()}")

                #end

            #end

        #end

    #end

    ##########################################################
    # Dump the contents of the File Record

    if not bFirstPass and bWildCardMatch and bTargetFile :

        if VMSBackupTypes.OutputType.BRIEF == kOptions.eOutputType :
            DumpBriefFileHeader(kFileHeader=kFileHeader, nSubSecondResolution=2)
        elif VMSBackupTypes.OutputType.FULL == kOptions.eOutputType :
            DumpFullFileHeader(kFileHeader=kFileHeader, kHeader=kHeader, bFirstPass=bFirstPass)
        elif VMSBackupTypes.OutputType.CSV == kOptions.eOutputType :
            DumpCSVFileHeader(kFileHeader=kFileHeader, kHeader=kHeader, bFirstPass=bFirstPass)
        #end

    #end

#end

def ProcessVBNRaw(kBlock : bytes, kHeader : BRHeader.BRHeader, kFileMetaData : VMSBackupTypes.VMSFileParameters, kOptions : VMSBackupTypes.VMSBackupParameters, bFirstPass : bool) :

    if (kFileMetaData.nFilePointer + kHeader.W_RSIZE()) < kFileMetaData.nFileSize :

        VMSWriteFile(kBlock=kBlock, kFileMetaData=kFileMetaData, nDataLength=kHeader.W_RSIZE())
        kFileMetaData.nFilePointer += kHeader.W_RSIZE()

    else :

        VMSWriteFile(kBlock=kBlock, kFileMetaData=kFileMetaData, nDataLength=kFileMetaData.nFileSize - kFileMetaData.nFilePointer)
        kFileMetaData.nFilePointer += kFileMetaData.nFileSize - kFileMetaData.nFilePointer

    #end

#end

def ProcessVBNNonVar(kBlock : bytes, kHeader : BRHeader.BRHeader, kFileMetaData : VMSBackupTypes.VMSFileParameters, kOptions : VMSBackupTypes.VMSBackupParameters, bFirstPass : bool) :

    if (kFileMetaData.nFilePointer + kHeader.W_RSIZE()) < kFileMetaData.nFileSize :

        if None == kFileMetaData.kFileHandle :

            if VMSBackupTypes.ExtractMode.SMART == kFileMetaData.kMode :

                for nRecordPointer in range(kHeader.W_RSIZE()) :

                    if kBlock[nRecordPointer] > 0x7F :

                        kFileMetaData.kMode       = VMSBackupTypes.ExtractMode.BINARY
                        kFileMetaData.bIgnoreVBN = True
                        break

                    #end

                #end

            #end

        else :

            VMSWriteFile(kBlock=kBlock, kFileMetaData=kFileMetaData, nDataLength=kHeader.W_RSIZE())

        #end

        kFileMetaData.nFilePointer += kHeader.W_RSIZE()

    else :

        if None == kFileMetaData.kFileHandle :

            if VMSBackupTypes.ExtractMode.SMART == kFileMetaData.kMode :

                for nRecordPointer in range(kFileMetaData.nFileSize - kFileMetaData.nFilePointer) :

                    if kBlock[nRecordPointer] > 0x7F :

                        kFileMetaData.kMode       = VMSBackupTypes.ExtractMode.BINARY
                        kFileMetaData.bIgnoreVBN = True
                        break

                    #end

                #end

            #end

        else :

            VMSWriteFile(kBlock=kBlock, kFileMetaData=kFileMetaData, nDataLength=kFileMetaData.nFileSize - kFileMetaData.nFilePointer)
            kFileMetaData.nFilePointer += (kFileMetaData.nFileSize - kFileMetaData.nFilePointer)

            VMSWriteEOL(kFileMetaData=kFileMetaData)

        #end

    #end

#end

def ProcessVBNVar(kBlock : bytes, kHeader : BRHeader.BRHeader, kFileMetaData : VMSBackupTypes.VMSFileParameters, kOptions : VMSBackupTypes.VMSBackupParameters, bFirstPass : bool) :

    kFileMetaData.bLastElementWasLFCR = False
    kFileMetaData.bContainsLFCR       = False

    bSkipHeader = BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_VFC == kFileMetaData.kFormat

    if bSkipHeader :
        nRecordLengthModifier = 2
    else :
        nRecordLengthModifier = 0
    #end

    # Set the Starting Position of the Record and shift the file pointer
    # (this handles the scenario whereby a header might span a record
    #  but not actually contain any length data)
    nRecordPointer              = kFileMetaData.nRemainingStartPos
    kFileMetaData.nFilePointer += kFileMetaData.nRemainingStartPos

    # First Pass requires the file to be scanned as long as it's deemed an ASCII file
    if kFileMetaData.nRemainingRecordLength > 0 :

        if bFirstPass :

            for nLocalRecordPointer in range(kFileMetaData.nRemainingStartPos, kFileMetaData.nRemainingRecordLength) :

                if nLocalRecordPointer >= kHeader.W_RSIZE() :
                    kFileMetaData.nRemainingStartPos      = 0
                    kFileMetaData.nRemainingRecordLength -= nLocalRecordPointer
                    return
                #end

                if VMSBackupTypes.ExtractMode.SMART == kFileMetaData.kMode :
                    if kBlock[nLocalRecordPointer] > 0x7F :
                        kFileMetaData.kMode = VMSBackupTypes.ExtractMode.BINARY
                        break
                    #end
                #end

            #end
                    
            nRecordPointer += kFileMetaData.nRemainingRecordLength

        else :

            # TODO: Probably a bug elsewhere, but sanity check an overflow of the record
            if (nRecordPointer + kFileMetaData.nRemainingRecordLength) >= kHeader.W_RSIZE() :

                VMSWriteFile(kBlock=kBlock[nRecordPointer:], kFileMetaData=kFileMetaData, nDataLength=kHeader.W_RSIZE() - nRecordPointer)
                kFileMetaData.nRemainingStartPos      = 0
                kFileMetaData.nRemainingRecordLength -= kHeader.W_RSIZE() - nRecordPointer
                kFileMetaData.nFilePointer           += kHeader.W_RSIZE() - nRecordPointer

                nRecordPointer                       += kHeader.W_RSIZE() - nRecordPointer

                # Record Pointers aren't allowed to finish on an odd byte
                if 0 != (nRecordPointer % 2) :

                    kFileMetaData.nFilePointer += 1

                #end

                return

            #end

            # Write File
            VMSWriteFile(kBlock=kBlock[nRecordPointer:], kFileMetaData=kFileMetaData, nDataLength=kFileMetaData.nRemainingRecordLength)

            nRecordPointer += kFileMetaData.nRemainingRecordLength

        #end

        kFileMetaData.nFilePointer             += kFileMetaData.nRemainingRecordLength
        kFileMetaData.nRemainingStartPos        = 0
        kFileMetaData.nRemainingRecordLength    = 0

        # Record Pointers aren't allowed to finish on an odd byte
        if 0 != (nRecordPointer % 2) :

            nRecordPointer             += 1
            kFileMetaData.nFilePointer += 1

        #end

        if None != kFileMetaData.kFileHandle :
            VMSWriteEOL(kFileMetaData=kFileMetaData, bForceEOL=not kFileMetaData.bLastElementWasLFCR)
        #end

    #end

    # Reset the Remaining Start Position
    kFileMetaData.nRemainingStartPos = 0

    while (nRecordPointer < kHeader.W_RSIZE()) and (kFileMetaData.nFilePointer < kFileMetaData.nFileSize) :

        nRecordLength   = struct.unpack_from(VMSBackupHelper.kUnpackType[VMSBackupHelper.sizeof.uint16_t.name], kBlock, nRecordPointer)[0] - nRecordLengthModifier
        nRecordPointer += 2 + nRecordLengthModifier

        # TODO: .DIR 'files' always seem to have 0xFFFF followed by a whole lot of nothing.  I've mitigated this for now by writing this as
        #       data , but I've no test data to verify this.
        if 0xFFFF == nRecordLength :
            kFileMetaData.nFilePointer += 2
            continue
        #end

        if nRecordPointer <= kHeader.W_RSIZE() :

            if (nRecordPointer + nRecordLength) >= kHeader.W_RSIZE() :

                kFileMetaData.nRemainingStartPos     = 0
                kFileMetaData.nRemainingRecordLength = nRecordLength
                nRecordLength                        = kHeader.W_RSIZE() - nRecordPointer
                kFileMetaData.nRemainingRecordLength = kFileMetaData.nRemainingRecordLength - nRecordLength

            #end

            if None == kFileMetaData.kFileHandle :

                # First Pass requires the file to be scanned as long as it's deemed an ASCII file
                for nLocalRecordPointer in range(nRecordPointer, nRecordPointer + nRecordLength) :
                    if VMSBackupTypes.ExtractMode.SMART == kFileMetaData.kMode :
                        if kBlock[nLocalRecordPointer] > 0x7F :
                            kFileMetaData.kMode      = VMSBackupTypes.ExtractMode.BINARY
                            kFileMetaData.bIgnoreVBN = True
                            break
                        #end
                    #end
                #end

                nRecordPointer += nRecordLength

            else :

                # Write File
                VMSWriteFile(kBlock=kBlock[nRecordPointer:], kFileMetaData=kFileMetaData, nDataLength=nRecordLength)
            
                nRecordPointer += nRecordLength

            #end

            kFileMetaData.nFilePointer += 2 + nRecordLength + nRecordLengthModifier

            # Record Pointers aren't allowed to finish on an odd byte
            if 0 != (nRecordPointer % 2) :

                nRecordPointer             += 1
                kFileMetaData.nFilePointer += 1

            #end

            if 0 == kFileMetaData.nRemainingRecordLength :
                if None != kFileMetaData.kFileHandle :
                    VMSWriteEOL(kFileMetaData=kFileMetaData, bForceEOL=(0 == kFileMetaData.nRemainingRecordLength) and not kFileMetaData.bLastElementWasLFCR)
                #end
            #end

        else :

            # The calculated file pointer is outside the RWIN size, which means
            # only the record header exists in this buffer, therefore transfer
            # the record data to be handled in the next buffer
            kFileMetaData.nFilePointer             += (nRecordPointer - kHeader.W_RSIZE())
            kFileMetaData.nRemainingStartPos        = nRecordPointer - kHeader.W_RSIZE()
            kFileMetaData.nRemainingRecordLength    = nRecordLength

            # A Zero length record is basically a new line
            if kFileMetaData.nRemainingRecordLength == 0 :

                if None != kFileMetaData.kFileHandle :

                    VMSWriteEOL(kFileMetaData=kFileMetaData, bForceEOL=(0 == kFileMetaData.nRemainingRecordLength) and not kFileMetaData.bLastElementWasLFCR)

                #end

            #end

        #end

    #end

#end

def ProcessVBN(kBlock : bytes, kHeader : BRHeader.BRHeader, kFileMetaData : VMSBackupTypes.VMSFileParameters, kOptions : VMSBackupTypes.VMSBackupParameters, bFirstPass : bool) :

    ##########################################################
    # DEBUG (ENHANCED)

    if None != kFileMetaData.kFileHandle :

        if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

            print("*** DEBUG *** ", end="")
            print(f"File Pointer = 0x{kFileMetaData.nFilePointer:08X}, File Size = 0x{kFileMetaData.nFileSize:08X}")

        #end

    #end

    # DEBUG (ENHANCED)
    ##########################################################

    if kFileMetaData.kFormat in [BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_VAR,
                                 BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_VFC] :

        if VMSBackupTypes.ExtractMode.RAW != kOptions.eExtractMode :

            # Process the record in Binary/ASCII Mode
            ProcessVBNVar(kBlock=kBlock, kHeader=kHeader, kFileMetaData=kFileMetaData, kOptions=kOptions, bFirstPass=bFirstPass)

        elif None != kFileMetaData.kFileHandle :

            # Process the record in Raw Mode
            ProcessVBNRaw(kBlock=kBlock, kHeader=kHeader, kFileMetaData=kFileMetaData, kOptions=kOptions, bFirstPass=bFirstPass)

        #end

    elif kFileMetaData.kFormat in [BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_FIX,
                                   BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_STM,
                                   BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_STMLF,
                                   BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_STMCR] :

        if VMSBackupTypes.ExtractMode.RAW != kOptions.eExtractMode :

            # Process the record in Binary/ASCII Mode
            ProcessVBNNonVar(kBlock=kBlock, kHeader=kHeader, kFileMetaData=kFileMetaData, kOptions=kOptions, bFirstPass=bFirstPass)

        elif None != kFileMetaData.kFileHandle :

            # Process the record in Raw Mode
            ProcessVBNRaw(kBlock=kBlock, kHeader=kHeader, kFileMetaData=kFileMetaData, kOptions=kOptions, bFirstPass=bFirstPass)

        #end

    elif kFileMetaData.kFormat in [BSFileHeader.BSFileHeader.RecordFormatType.RECORD_FORMAT_UDF] :

        if None != kFileMetaData.kFileHandle :

            # Process the record in Raw Mode
            ProcessVBNRaw(kBlock=kBlock, kHeader=kHeader, kFileMetaData=kFileMetaData, kOptions=kOptions, bFirstPass=bFirstPass)

        #end

    #end

    ##########################################################
    # DEBUG (ENHANCED)

    if None != kFileMetaData.kFileHandle :

        if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

            print("*** DEBUG *** ", end="")
            print(f"File Pointer = 0x{kFileMetaData.nFilePointer:08X}, File Size = 0x{kFileMetaData.nFileSize:08X}")

        #end

    #end

    # DEBUG (ENHANCED)
    ##########################################################

#end

def VMSBackupProcessBackupSaveSetRecord(kBlock : bytes, nAddress : int, kHeader : BBHeader.BBHeader, kOptions : VMSBackupTypes.VMSBackupParameters, bFirstPass : bool, bLastBlock : bool, kFileList : dict, kExtractStatus : dict) -> tuple[bool,int] :

    # Read the Header
    kRecordHeader = BRHeader.BRHeader()
    kRecordHeader.LoadHeaderFromBuffer(kBlock=kBlock)

    # Skip past the Record Header
    nAddress += kRecordHeader.GetLength()

    if 0 == kRecordHeader.W_RSIZE() :
        return True, kHeader.L_BLOCKSIZE() # nAddress
    #end

    kRecordType = kRecordHeader.W_RTYPE()
    if not kRecordType in [BRHeader.BRHeader.RecordType.RECORD_VBN,
                           BRHeader.BRHeader.RecordType.RECORD_VOLUME,
                           BRHeader.BRHeader.RecordType.RECORD_NULL] :

        # Close any open files
        CloseOpenFiles(kExtractStatus=kExtractStatus)

    #end

    if BRHeader.BRHeader.RecordType.RECORD_NULL == kRecordType :

        ##########################################################
        # DEBUG (ENHANCED)

        if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

            print("*** DEBUG *** ", end="")
            print("NULL RECORD")

        #end

        # DEBUG (ENHANCED)
        ##########################################################

    elif BRHeader.BRHeader.RecordType.RECORD_SUMMARY == kRecordType :

        ##########################################################
        # DEBUG (ENHANCED)

        if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

            print("*** DEBUG *** ", end="")
            print("SUMMARY RECORD")

        #end

        # DEBUG (ENHANCED)
        ##########################################################

    elif BRHeader.BRHeader.RecordType.RECORD_VOLUME == kRecordType :

        ##########################################################
        # DEBUG (ENHANCED)

        if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

            print("*** DEBUG *** ", end="")
            print("VOLUME RECORD")

        #end

        # DEBUG (ENHANCED)
        ##########################################################

            return True, kHeader.L_BLOCKSIZE()

    elif BRHeader.BRHeader.RecordType.RECORD_FILE == kRecordType :

        ##########################################################
        # DEBUG (ENHANCED)

        if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

            print("*** DEBUG *** ", end="")
            print("FILE RECORD")

        #end

        # DEBUG (ENHANCED)
        ##########################################################

        VMSBackupProcessFile(kBlock=kBlock[kRecordHeader.GetLength():], kHeader=kRecordHeader, kOptions=kOptions, kFileList=kFileList, kExtractStatus=kExtractStatus, bFirstPass=bFirstPass)

    elif BRHeader.BRHeader.RecordType.RECORD_VBN == kRecordType :

        ##########################################################
        # DEBUG (ENHANCED)

        if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

            print("*** DEBUG *** ", end="")
            print("VBN RECORD")

        #end

        # DEBUG (ENHANCED)
        ##########################################################

        if None != kExtractStatus["Current"] :

            if not kExtractStatus["Current"].bIgnoreVBN :

                ProcessVBN(kBlock=kBlock[kRecordHeader.GetLength():], kHeader=kRecordHeader, kFileMetaData=kExtractStatus["Current"], kOptions=kOptions, bFirstPass=bFirstPass)

            #end

        #end

    else :

        if not bFirstPass and (not bLastBlock or (VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug)) :

            print(f"WARNING : Invalid Record ({kRecordHeader.W_RTYPE ()}).")
            print(f"WARNING : Invalid Record ({kRecordHeader.W_RSIZE ()}).")

        #end

        CloseOpenFiles(kExtractStatus=kExtractStatus)

        return False, nAddress

    #end

    # Move to the Next Record
    nAddress += kRecordHeader.W_RSIZE()

    return True, nAddress

#end

def VMSBackupProcessBlock(kBlock : bytes, kBlockHeader : BBHeader.BBHeader, kOptions : VMSBackupTypes.VMSBackupParameters, nBaseAddress : int, nMaxAddress : int, bFirstPass : bool, kFileList : dict, kExtractStatus : dict) -> bool :

    # Cumulative validity of this block
    bValid = True

    # Last Block?
    bLastBlock = False

    # Current Block Header
    kCurrentHeader = BBHeader.BBHeader()
    kCurrentHeader.LoadHeaderFromBuffer(kBlock=kBlock)

    # Validate the Size
    if kCurrentHeader.Validate(kBaseHeader=kBlockHeader) :

        # Skip the Block Header
        nBlockAddress = kBlockHeader.GetLength()

        # Determine if this is the last block
        # This forms a little bit of a kludge, but it seems that
        # occasionally backup files basically have garbage at the tail end
        # of the last block, so errors on the last block will be handled,
        # but suppressed from all but debug.
        bLastBlock = (nMaxAddress - nBaseAddress) <= kBlockHeader.L_BLOCKSIZE()

        # Last Block Address
        nLastBlockAddress = nBlockAddress

        # Iterate through the current Block
        while (nBlockAddress < kCurrentHeader.L_BLOCKSIZE()) and bValid :

            # Preserve the Prior to Last Block Address for debugging
            nLastLastBlockAddress  = nLastBlockAddress

            # Preserve the Last Block Address for debugging
            nLastBlockAddress = nBlockAddress

            ##########################################################
            # DEBUG (ENHANCED)

            if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

                print("*** DEBUG *** ", end="")
                print(f"Processing Record Address : 0x{(nBaseAddress + nBlockAddress):08x}")

            #end

            # DEBUG (ENHANCED)
            ##########################################################

            # Process the Record
            bValid, nBlockAddress = VMSBackupProcessBackupSaveSetRecord(kBlock=kBlock[nBlockAddress:], nAddress=nBlockAddress, kHeader=kBlockHeader, kOptions=kOptions, bFirstPass=bFirstPass, bLastBlock=bLastBlock, kFileList=kFileList, kExtractStatus=kExtractStatus)

            # Output Errors if the Record is invalid
            if not bValid :

                # Close any open files
                CloseOpenFiles(kExtractStatus=kExtractStatus)

                if not bFirstPass :

                    if VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug :

                        print("*** START DEBUG ***")

                        print(f"Last Valid Record Address : 0x{nLastLastBlockAddress:08x}")
                        print(f"Invalid Record Address    : 0x{nLastBlockAddress:08X}")

                        print("*** END DEBUG ***")

                    #end

                #end

            #end

        #end

    else :

        # Close any open files
        CloseOpenFiles(kExtractStatus=kExtractStatus)

        if False == bFirstPass :
            if VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug :
                print(f"WARNING : Invalid block size {kCurrentHeader.L_BLOCKSIZE()} Read, {kBlockHeader.L_BLOCKSIZE()} Expected.  Skipping block", out=sys.stderr)
            #end
        #end

    #end

    return bValid or (bLastBlock and (VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug))

#end

def VMSBackupProcess(kFile : VMSBackupRAMCache.VMSBackupRAMCache, kOptions : VMSBackupTypes.VMSBackupParameters, bTwoPassesRequired : bool) -> bool :

    # Extract Status
    kExtractStatus = {}
    kExtractStatus["Current"] = None

    # Flag indicating a 2nd pass is needed
    bSecondPass = not bTwoPassesRequired

    # File List
    kFileList = {}

    kBlockHeader = BBHeader.BBHeader()

    # Buffer the File Start
    nAbsStart = kFile.tell()

    # Load the Block Header
    kBlockHeader.LoadHeaderFromFile(kFile=kFile)

    # Dump the Block Header
    if VMSBackupTypes.OutputType.SUPPRESS != kOptions.eOutputType :
        DumpHeader(kHeader=kBlockHeader, kOptions=kOptions)
    #end

    # Point the file buffer to the end
    kFile.seek(0, os.SEEK_END)
    nAbsEnd = kFile.tell()

    # Point the file buffer back to the start
    kFile.seek(nAbsStart, os.SEEK_SET)

    ##########################################################
    # DEBUG

    if VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug :

        print("*** DEBUG *** ", end="")

        # Output the Block Address for debugging purposes
        print("STARTING FIRST FILE PARSE")

    #end

    # END DEBUG
    ##########################################################

    while True :

        # Force the Algorithm to valid (needed if this is a 2nd pass)
        bValid  = True

        # Process the entire file
        while (False == kFile.feof()) and bValid :

            # Read the Current Block
            nBlock = kFile.tell()
            kBlock = kFile.read(kBlockHeader.L_BLOCKSIZE())

            ##########################################################
            # DEBUG (ENHANCED)

            if VMSBackupTypes.ExtractDebug.ENHANCED == kOptions.eExtractDebug :

                print("*** DEBUG *** ", end="")
                print(f"Processing Block Address  : 0x{nBlock:08x}")

            #end

            # END DEBUG (ENHANCED)
            ##########################################################

            # There's actually a curious difference in behaviour between Python and C here from what I can tell.
            # Python seems to flag the file as having reached the EOF even if the final read successfully completed.
            # Whereas C does not in the same scenario.  This ensures the behaviour matches C.
            if (False == kFile.feof()) or (len(kBlock) == kBlockHeader.L_BLOCKSIZE()) :

                bValid = VMSBackupProcessBlock(kBlock=kBlock, kBlockHeader=kBlockHeader, kOptions=kOptions, nBaseAddress=nBlock, nMaxAddress=nAbsEnd, bFirstPass=not bSecondPass, kFileList=kFileList, kExtractStatus=kExtractStatus)

            #end

            if (False == bValid) and (False == bSecondPass):

                ##########################################################
                # DEBUG (ENHANCED)

                if VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug :

                    print("*** DEBUG *** ", end="")
                    print(f"Block Address             : 0x{nBlock - nAbsStart:08x}")

                #end

                # END DEBUG (ENHANCED)
                ##########################################################

            #end

        #end

        # If Two Passes are Required
        if bTwoPassesRequired and (False == bSecondPass) :

            # Indicate this is no longer the first pass
            bSecondPass = True

            # Point the file buffer back to the start
            kFile.seek(nOffset=nAbsStart, nWhence=os.SEEK_SET)

            ##########################################################
            # DEBUG

            if VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug :

                print("*** DEBUG *** ", end="")
                print("STARTING SECOND FILE PARSE")

            #end

            # END DEBUG
            ##########################################################

        else :

            break

        #end

    #end

    # Close any open files
    CloseOpenFiles(kExtractStatus=kExtractStatus)

    kFile.close()

    return True

#end