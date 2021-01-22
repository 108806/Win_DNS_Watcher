import os
import sys
import argparse
import ctypes
from time import sleep
import datetime
import subprocess
import traceback

__author__= 0x1a906

"""
This program checks whether the specified DNS record exists in the Windows DNS Cache:
[USAGE] $python Windows_DNS.py wikipedia.org
You can also specify a second parameter of time interval measured in seconds between the checks:
[USAGE] $python3 Windows_DNS.py wikipedia.org --interval=15 --verbose=True

Important : This doesn't know when the previous match occured if the program wasn't running atm, 
so it clears the old cache and starts to log to file always after that clearing it.
"""

#Handling all the command line arguments:
parser = argparse.ArgumentParser()
parser.add_argument("record_name", help="Target name to be searched, ie www.google.com")
parser.add_argument("--verbose", default=False, help="Verbose mode, turned off by default.")
parser.add_argument("--interval", default=30, 
                    help="Time interval measured in seconds between the checks.", type=int)
args = parser.parse_args()
if args.verbose: print("[INFO] : Verbose mode turned on.")


def isUserAdmin():
    """
    @return: True if the current user is an 'Admin' whatever that means
    (root on Unix), otherwise False. This is mostly useless for now, may be removed in next version.
    """

    if sys.platform == "win32":
        # WARNING: requires Windows XP SP2 or higher!
        try:
            admin = ctypes.windll.shell32.IsUserAnAdmin()
            if admin: print("""
            
            [INFO]
            Admin privileges not needed for anything, running this as a regular user is recommended.

            """)
        except:
            traceback.print_exc()
            print("[INFO] Admin check failed, assuming not an admin.")
            return False
    elif sys.platform == "Linux":
        return os.getuid() == 0
    else:
        raise RuntimeError("[ERROR] Unsupported operating system for this module and version: %s" % (os.name,)) 


def run_command(cmd):
    """given shell command, returns communication tuple of stdout and stderr"""
    return subprocess.Popen(cmd, 
                            universal_newlines=True,
                            encoding="utf8",
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            stdin=subprocess.PIPE,
                            shell=True)


def eternity(target_record:str, interval:int=30, verbose:bool=False):
    """ 
    Param : target_record = str, classic format like 'https://google.com'
    Param : interval = int, seconds between flushing cache ang running again, 
    if not provided it is being set to 30 to keep it low profile.
    This is designed as the main loop of the program.
    
    @return : nothing.
    """
    def printv(*kwargs):
        if args.verbose: 
            for arg in kwargs:
                if type(arg)==str:
                    print(arg)
                    continue
                for x in arg:
                    print(x)
    
    #An almost foolproof arg parsing:
    target_record = target_record.strip().replace('\n','').replace('\r\n', '').replace(' ', '')
    printv(target_record)
    
    cmd = "ipconfig /displaydns | findstr " + target_record         # Old wae, this is tha wae!

    getCache = lambda : str(run_command(cmd).communicate()[0])
    #Paranoid and ugly, but safe even with crappy terminal emulators:
    cleanCache = lambda cache :  cache.replace('  ', ' ').strip().replace('\t', ' ').replace('\r\n', '\t').split('\n')
    
    logfile = open('WIN_DNS_LOG.txt', 'a+', encoding='utf8')

    while True:
        printv(F"[VERBOSE] Main goes on. Refreshing in {interval} s.")
        sleep(interval)
        
        cache = getCache()
        cache = cleanCache(cache)
        printv("[VERBOSE] - Cache : ", cache)

        if cache : assert type(cache) == list
        else : print("[WARNING]: Command execution failed. This will not stop the process from trying again over and over.")
        
        if len(cache) > 1:
            now = datetime.datetime.now()
            time_f = (f'{now:%Y-%m-%d %H:%M:%S}')
            printv(F"[VERBOSE] HIT @ : {time_f}")
            try:
                with open('WIN_DNS_LOG.txt', 'a+', encoding='utf8') as logfile:
                    logfile.write(F"[MATCH] : {time_f} : {target_record}\n")
            except Exception:
                print("[ERROR] : ", Exception)
            run_command('ipconfig /flushdns')
        else:
            printv("[VERBOSE] No hits with : ", target_record)



#Clearing the DNS Cache for the first run, hence the loop flushes it only after getting a match in DNS register.
run_command('ipconfig /flushdns')

#All actual tings to skrrah right here:
if __name__ == "__main__":
    eternity(args.record_name, args.interval, args.verbose)
