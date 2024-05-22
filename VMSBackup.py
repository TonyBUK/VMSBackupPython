import sys
import VMSBackupRAMCache
import VMSBackupTypes
import VMSBackupProcess

__VMSVERSION__ = "1.7"

# VMS Backup Utility
#
# This tool is designed to parse and extract Open VMS Backup data sets.  This
# has been primarily reverse engineered based on backup sets generated using
# Open VMS 5.5.
#
# This is a Python port of https://github.com/TonyBUK/VMSBackup, with a few
# quality of life improvements around folder handling.

def DisplayHelp() :
    print(f"VMSBackup Version {__VMSVERSION__}")
    print(f"")
    print(f"VMSBackup [FILE] [-L:listoption] [-N] [-X:extractmode] [-M:mask] [-F] [-V] [-D] [-?]")
    print(f"")
    print(f"  FILE           Backup Data Set")
    print(f"  -L             Selects output list")
    print(f"  listoptions     S  Suppress Output             B  Brief Output (default)")
    print(f"                  F  Full Output                 C  CSV Output")
    print(f"  -N             Don't Extract File Contents")
    print(f"  -X             Selects Extraction Mode")
    print(f"  extractmode     S  Smart/Auto Mode (default)   A  ASCII Mode")
    print(f"                  B  Binary Mode                 R  Raw Mode")
    print(f"  -M             File Extraction Mask")
    print(f"                  e.g. *.*, *.bin*, *a*.*-1 etc.")
    print(f"                  Default is *.*0.")
    print(f"  -F             Extract with full path (default off)")
    print(f"  -V             Extract with version numbers in the filename (default off)")
    print(f"  -T             Extract with file access/modification dates (default off)")
    print(f"  -R             Use RAM Caching")
    print(f"  -D             Debug Mode (default off)")
    print(f"  -DD            Enhanced Debug Mode (default off)")
    print(f"  -?             Display this help")
#end

def VMSBackup(kFile : str, kOptions : VMSBackupTypes.VMSBackupParameters = None) -> bool :

    if None == kOptions :
        kOptions = VMSBackupTypes.VMSBackupParameters()
    #end

    # Determine whether 2 passes are needed
    #
    # Scenario 1 : Smart Extract - Since we need to read the file first to determine if it's
    #              ASCII or Binary.
    # Scenario 2 : If the Extract Version is anything other than None, we need to read the
    #              all the files to determine absolute/relative version numbers.
    bTwoPassedRequired = (kOptions.bExtract and \
                          (kOptions.eExtractMode == VMSBackupTypes.ExtractMode.SMART)) or \
                         (kOptions.nExtractVersion != None)

    if VMSBackupTypes.ExtractDebug.NONE != kOptions.eExtractDebug :

        ##########################################################################
        # Debug Output
        #
        # Echo back Extraction Options

        print(f"*** START DEBUG ***")

        print(f"VMS Backup Options")
        print(f"Output Mode             = {["SUPPRESS", "BRIEF", "FULL", "CSV"][kOptions.eOutputType]}")
        print(f"Extract                 = {["OFF", "ON"][kOptions.bExtract]}")
        print(f"Extract Mode            = {["SMART", "ASCII", "BINARY", "RAW"][kOptions.eExtractMode]}")
        print(f"Extract Mask            = {kOptions.kExtractMask}")
        print(f"Extract Version         = {"*" if None == kOptions.nExtractVersion else kOptions.nExtractVersion}")
        print(f"Extract Folders         = {["OFF", "ON"][kOptions.bExtractFolder]}")
        print(f"Extract with Version    = {["OFF", "ON"][kOptions.bExtractWithVersion]}")
        print(f"Extract with Dates      = {["OFF", "ON"][kOptions.bExtractWithDate]}")
        print(f"Use RAM Cache           = {["OFF", "ON"][kOptions.bRAMCaching]}")
        print(f"Extract Debug           = {["OFF", "ON (NORMAL)", "ON (ENHANCED)"][kOptions.eExtractDebug]}")
        print(f"Number of Passes        = {[1, 2][bTwoPassedRequired]}")

        print(f"*** END DEBUG ***")

        # Debug Output
        ##########################################################################

    #end

    # Open the File
    kFileRAMCache = VMSBackupRAMCache.VMSBackupRAMCache(bRAMCaching=kOptions.bRAMCaching, kFile=kFile)

    return VMSBackupProcess.VMSBackupProcess(kFile=kFileRAMCache, kOptions=kOptions, bTwoPassesRequired=bTwoPassedRequired)

#end

def VMSBackupFromCLI(argv : list[str]) -> bool :

    if len(argv) < 2 :
        DisplayHelp()
        return False
    #end

    kOptions            = VMSBackupTypes.VMSBackupParameters()
    bFileArgumentFound  = False

    for kArg in argv[1:] :

        if bFileArgumentFound or kArg.startswith("-") :
            if kArg in ["-LS", "-L:S"] :
                kOptions.eOutputType = VMSBackupTypes.OutputType.SUPPRESS
            elif kArg in ["-LB", "-L:B"] :
                kOptions.eOutputType = VMSBackupTypes.OutputType.BRIEF
            elif kArg in ["-LF", "-L:F"] :
                kOptions.eOutputType = VMSBackupTypes.OutputType.FULL
            elif kArg in ["-LC", "-L:C"] :
                kOptions.eOutputType = VMSBackupTypes.OutputType.CSV
            elif "-N" == kArg :
                kOptions.bExtract = False
            elif kArg in ["-XS", "-X:S"] :
                kOptions.eExtractMode = VMSBackupTypes.ExtractMode.SMART
            elif kArg in ["-XA", "-X:A"] :
                kOptions.eExtractMode = VMSBackupTypes.ExtractMode.ASCII
            elif kArg in ["-XB", "-X:B"] :
                kOptions.eExtractMode = VMSBackupTypes.ExtractMode.BINARY
            elif kArg in ["-XR", "-X:R"] :
                kOptions.eExtractMode = VMSBackupTypes.ExtractMode.RAW
            elif kArg.startswith("-M") :
                if kArg.startswith("-M:") :
                    kOptions.kExtractMask = kArg[3:]
                else :
                    kOptions.kExtractMask = kArg[2:]
                #end
                if ";" in kOptions.kExtractMask :
                    kTokens = kOptions.kExtractMask.split(";")
                    if len(kTokens) != 2 :
                        print(f"WARNING : Invalid mask {kOptions.kExtractMask}")
                        kOptions.kExtractMask           = VMSBackupTypes.VMSBackupParameters.kExtractMask
                    else :
                        kOptions.kExtractMask           = kTokens[0]
                        if "*" == kTokens[1] :
                            kOptions.nExtractVersion    = None
                        else :
                            kOptions.nExtractVersion    = int(kTokens[1])
                        #end
                    #end
                #end
            elif "-F" == kArg :
                kOptions.bExtractFolder = True
            elif "-V" == kArg :
                kOptions.bExtractWithVersion = True
            elif "-T" == kArg :
                kOptions.bExtractWithDate = True
            elif "-R" == kArg :
                kOptions.bRAMCaching = True
            elif "-DD" == kArg :
                kOptions.eExtractDebug = VMSBackupTypes.ExtractDebug.ENHANCED
            elif "-D" == kArg :
                kOptions.eExtractDebug = VMSBackupTypes.ExtractDebug.BASIC
            elif "-?" == kArg :
                DisplayHelp()
                return True
            else :
                print(f"WARNING : Unknown parameter {kArg}")
            #end
        else :
            kFile               = kArg
            bFileArgumentFound  = True
        #end

    #end

    return VMSBackup(kFile=kFile, kOptions=kOptions)

#end

def VMSBackupFromString(kCommand : str) -> bool :
    return VMSBackupFromCLI(["VMSBackup"] + kCommand.split())
#end

if __name__ == "__main__" :
    VMSBackupFromCLI(sys.argv)
#end