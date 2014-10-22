'''
   This file is for a collection of utilities based on process-interaction.

   Copyright (c) Timothy Savannah under LGPL, All Rights Reserved. See LICENSE for more information
'''
import datetime
import math
import glob
import os
import signal
import time
import subprocess

class Pidof:

    @staticmethod
    def getPidsOfProcess(processName, alsoContains=None, looseMatch=False):
        '''
           Determines the pids of all processes matching @processName also containing @alsoContains

           processName: String - The name of the process
           alsoContains: List - Strings which process must match.
           looseMatch: Boolean - If true, assert that any paramater contains @alsoContains. If False, must be exact match

           i.e. to match "python test.py", @processName would be "python" and @alsoContains would be ["test.py"]

           returns: A list of pids
        '''
        pipe = subprocess.Popen('pidof %s' %(processName,), shell=True, stdout=subprocess.PIPE)
        pids = pipe.stdout.read().replace('\n', '')
        pipe.wait()

        if alsoContains == None:
            alsoContains = []

        if pids:
            pids = pids.split(' ')
        else:
            # Try to cover various ways of running python and bash applications
            if '.py' in processName:
                return Pidof.getPidsOfProcess('python', [processName] + alsoContains, looseMatch)
            elif '.sh' in processName:
                return Pidof.getPidsOfProcess('bash', [processName] + alsoContains, looseMatch) + Pidof.getPidsOfProcess('sh', [processName] + alsoContains, looseMatch)
            return []

        if not alsoContains:
            return [int(pid) for pid in pids]

        newPidList = []
        # Assert this is a true match
        for pid in pids:
            try:
                cmdlineFile = open('/proc/%d/cmdline' %(int(pid),), 'r')
                cmdline = cmdlineFile.read()
                cmdlineFile.close()
            except:
                continue
            params = cmdline.split('\x00')
            addMe = True
            # Check for extra contains
            for mustContain in alsoContains:
                if looseMatch:
                    addMe = False
                    for param in params:
                        if mustContain in param:
                            addMe = True
                            break
                    if addMe:
                        break
                elif mustContain not in params:
                    addMe = False
                    break
            if addMe:
                newPidList.append(int(pid))

        return newPidList

    @staticmethod
    def killProcessesByName(processName, alsoContains=None, looseMatch=True, forceKill=False):
        '''
           Kills processes matching @processName also containing @alsoContains

           processName: String - The name of the process
           alsoContains: List - Strings which process must match
           looseMatch: Boolean - Match loosely (any argument contains strings in @alsoContains). If False, must be exact match
           forceKill: Boolean - Use signal 9 (SIGKILL) if true, else use SIGTERM

           returns: Int - Number of pids killed
        '''
        if alsoContains == None:
            alsoContains = []

        pids = Pidof.getPidsOfProcess(processName, alsoContains, looseMatch)
        if forceKill:
            signalNum = signal.SIGKILL
        else:
            signalNum = signal.SIGTERM

        pidsKilled = 0
        for pid in pids:
            try:
                os.kill(int(pid), signalNum)
                pidsKilled += 1
            except:
                pass

        return pidsKilled

class Ps:

    @staticmethod
    def getStartTimeByPid(pid):
        pipe = subprocess.Popen("ps axeo 'pid,etime' | grep -E '^[ ]*%s ' " %(str(pid)), shell=True, stdout=subprocess.PIPE)
        contents = pipe.stdout.read().replace('\n', '')
        if not contents:
            return None
        pipe.wait()
        etime = contents.split(' ')[-1]

        offsetDay = 0
        offsetHour = 0
        offsetMinute = 0
        offsetSecond = 0

        if etime.count('-'):
            offset = datetime.datetime.strptime(etime, '%d-%H:%M:%S')
            (offsetDay, offsetHour, offsetMinute, offsetSecond) = (offset.day, offset.hour, offset.minute, offset.second)
        elif etime.count(':') == 2:
            offset = datetime.datetime.strptime(etime, '%H:%M:%S')
            (offsetHour, offsetMinute, offsetSecond) = (offset.hour, offset.minute, offset.second)
        elif etime.count(':') == 1:
            offset = datetime.datetime.strptime(etime, '%M:%S')
            (offsetMinute, offsetSecond) = (offset.minute, offset.second)
        else:
            return None

        return datetime.datetime.now() - datetime.timedelta(days=offsetDay, minutes=offsetMinute, seconds=offsetSecond)


class PidFile:

    @staticmethod
    def _getFullFilename(appName):
        '''
           Private method -- Generates a full pid filename from an @appName

           appName: String - Application name

           returns: String - Full path to pid file
        '''
        return os.environ['HOME'] + '/pids/' + appName + '.pid'

    @staticmethod
    def writePidFile(appName, overridePid=None):
        '''
           Writes a pidfile for @appName

           appName: Application Name
           overridePid: Override pid with this value (instead of os.getpid())
        '''
        # Ensure directory is created
        subprocess.Popen('source ~/.bashrc; mkdir -p %s/pids' %(os.environ['HOME'], ), shell=True).wait()

        pidFile = open(PidFile._getFullFilename(appName), 'w')
        pidFile.write(overridePid and str(overridePid) or str(os.getpid()))
        pidFile.close()

    @staticmethod
    def removePidFile(appName):
        '''
           Remove pidfile for @appName

           appName: String - Application Name. THIS IS A GLOB FOR KILLING MULTIPLE PROCESSES

           returns: Integer - Number of files removed
        '''
        fullFilename = PidFile._getFullFilename(appName)
        pidFilenames = glob.glob(fullFilename)

        numRemoved = 0
        for pidFilename in pidFilenames:
            try:
                os.remove(pidFilename)
                numRemoved += 1
            except:
                pass
        return numRemoved

    @staticmethod
    def killProcessByPidFile(appName, forceKill=False, removePidFile=False):
        '''
           Kills the process specified in the pid for @appName.

           appName: String - Application Name. THIS IS A GLOB FOR KILLING MULTIPLE PROCESSES
           forceKill: Boolean - True to use SIGKILL, else SIGTERM
           removePidFile: Boolean - True to also remove pid file

           returns: Integer - Number of processes killed
        '''
        fullFilename = PidFile._getFullFilename(appName)

        pidFilenames = glob.glob(fullFilename)

        if forceKill:
            signalNum = signal.SIGKILL
        else:
            signalNum = signal.SIGTERM

        numKilled = 0
        for pidFilename in pidFilenames:
            try:
                pidFile = open(pidFilename, 'r')
                pid = pidFile.read().replace('\n', '')
                os.kill(int(pid), signalNum)
                numKilled += 1
                pidFile.close()
            except:
                try:
                    pidFile.close()
                except:
                    pass

        if removePidFile:
            PidFile.removePidFile(appName)

        return numKilled

class ProcessWatching:

    class OldStartTime(Exception):
        def __init__(self, pids):
            Exception.__init__(self)
            self.pids = pids

    class DidNotStart(Exception):
        pass

    @staticmethod
    def watchForProcessToStart(processName, alsoContains=None, timeout=30):

        if alsoContains == None:
            alsoContains = []

        INTERVAL = .1

        iAmDone = True
        failedPids = []
        waitMinutes = math.ceil(timeout / 60.0)

        pids = Pidof.getPidsOfProcess(processName, alsoContains)

        for i in xrange(int(timeout / INTERVAL)):
            iAmDone = True
            failedPids = []
            if not pids:
                pids = Pidof.getPidsOfProcess(processName, alsoContains)
                iAmDone = False
                time.sleep(INTERVAL)
                continue
            for j in xrange(len(pids)):
                startTime = Ps.getStartTimeByPid(pids[j])
                if not startTime:
                    pids = Pidof.getPidsOfProcess(processName, alsoContains)
                    iAmDone = False
                    failedPids = [pids[j]]
                    break
                if datetime.datetime.now() - Ps.getStartTimeByPid(pids[j]) > datetime.timedelta(minutes=waitMinutes):
                    iAmDone = False
                    failedPids.append(pids[j])
            if iAmDone:
                break
            time.sleep(INTERVAL)
        if failedPids:
            raise ProcessWatching.OldStartTime(failedPids)
        if not iAmDone:
            raise ProcessWatching.DidNotStart()


    @staticmethod
    def watchForProcessesToDieByName(processName, alsoContains=None, looseMatch=False, ignorePids=None, timeout=30):
        '''
           Waits for a process to die by name.

           processName: String - The name of the process
           alsoContains: List - Strings which process must match
           looseMatch: Boolean - Match loosely (any argument contains strings in @alsoContains). If False, must be exact match
           timeout: Integer - seconds to wait.

           Returns True if application dies prior to timeout.
        '''
        if alsoContains == None:
            alsoContains = []

        if ignorePids == None:
            ignorePids = []

        pids = Pidof.getPidsOfProcess(processName, alsoContains, looseMatch)
        return ProcessWatching.watchForProcessesToDieByPids(pids, ignorePids, timeout)

    @staticmethod
    def watchForProcessesToDieByPids(pids, ignorePids=None, timeout=30):
        '''
           Waits for a process to die by pids

           pids: List- pids to watch
           timeout: Integer - seconds to wait.

           Returns True if application dies prior to timeout.
        '''
        INTERVAL = .1
        if ignorePids == None:
            ignorePids = []

        pids2 = pids[:]

        for i in xrange(int(timeout / INTERVAL)):
            pidsRemaining = []
            for pid in pids2:
                if pid in ignorePids:
                    continue
                if os.path.exists('/proc/' + str(pid)):
                    pidsRemaining.append(pid)
            pids2 = pidsRemaining[:]
            if not pidsRemaining:
                break
            time.sleep(INTERVAL)

        return not bool(pidsRemaining)
