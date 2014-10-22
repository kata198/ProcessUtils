ProcessUtils
============

Utilities and library for advanced process management (pidfiles, finding pids based on matching strings more powerful than pidof) and killing / waiting / restarting applications, and finding various pieces of information about the application.

Contains several applications as more powerful alternatives to complex sometimes-buggy alternatives like supervisor

Applications
============

getPids
=======

Comes with an application, getPids, which can be used to better identify python programs (as pidof python would return all python applications)

	Usage: getPids programName (--loose) [extra]
	 This application extends "pidof" functionality. Anything contained in optional argument [extra] must also be present

	    --loose             Arguments should be treated as "loose" matches (any order). Otherwise, exact match only.
	    [extra]             Any extra string portions for which we should match

	Example, for an application python apps/SomeApp.py

	`getPids python apps/SomeApp.py` would return the pid of that application.

The power is in the ProcessUtils.py file. Within here are several classes. Documentation can be found within ProcessUtils.py


watchProcessAndRestart
======================

Comes with an application, watchProcessAndRestart, which runs a process with any given arguments, restarting it when it dies, unless the application dies with exit code 55.

	Usage: watchProcessAndRestart [cmd]

	Keeps running application until it returns a status code of 55.



This is useful for keeping service applications running always, yet giving them the ability to stop (via trapping sigterm and exiting with status code 55, for example) for maintenance.

watchForProcessToDie
====================

Comes with an application, watchForProcessToDie, which watches for an arbitrary process to die, and returns after.

	Usage: watchForProcessToDie [timeout] [processName] (optional list of params).

	Waits for any processes matching arguments to Die

Useful for scripts that need to wait for a process to die. All params are considered loose. An application front for the equivlant methods below.


watchForProcessToStart
======================

Comes with an application, watchForProcessToStart, which watches for an arbitrary process to start, and returns after, or provides other information.

	Usage: watchForProcessToStart [timeout] [processName] (optional list of params).
	Waits for any processes matching arguments to Start

	Exits with code 51 if an old start-time was found on a process (an existing process was running, but new did not start)
	Exits with code 52 if no process was found after timeout matching the given criteria.

Useful for scripts that need to wait for a process to begin before performing an action. All params are considered loose. An application front for the equivlant methods below


Library
=======

ProcessUtils.PidOf
==================

ProcessUtils.Pidof - This class provides "pidof" functionality, for searching for application process IDs based on criteria.

*ProcessUtils.Pidof.getPidsOfProcesses(processName, alsoContains, looseMatch)*

Finds processes under name "process Name", with arguments in an optional list "alsoContains". looseMatch determines if any parameter can contain the extra strings, otherwise must be exact match.

*ProcessUtils.Pidof.killProcessesByName(processName, alsoContains=None, looseMatch=True, forceKill=False)*

Kills any process matching the criteria (same as getPidsOfProcesses). Note looseMatch defaults to true here. forceKill is the difference between SIGTERM and SIGKILL

ProcessUtils.Ps
===============

Gets information available from PS

*getStartTimeByPid(pid)*

Gets the start time (as a datetime object) of a paticular pid

ProcessUtils.PidFile
====================

Handles PID files (a file containing process ID for an application)

*writePidFile(appName, overridePid=None)*

Writes a pid file for an application, as named by "appName", into current user's home/pids folder. use overridePid to specify an explicit pid instead of os.getpid


*removePidFile(appName)*

Removes the PID for an application noted by "appName"

*killProcessByPidFile(appName, forceKill=False, removePidFile=False)*

Kills a process using the pid file. if forceKill is true, uses SIGKILL instead of SIGTERM. removePidFile param specifies whether to remove the pid file after closing app


ProcessUtils.ProcessWatching
============================

Provides mechanisms for watching processes and reacting

Exceptions:

 * OldStartTime(Exception):
 * DidNotStart(Exception):

*watchForProcessToStart(processName, alsoContains=None, timeout=30)*

Blocks and waits for a process to start. process must have the name noted by "processName", and alsoContains is a list of additional arguments. Timeout determines the max time to wait.
Raises  OldStartTime if a new process did not start (but an old process matches). Raises DidNotStart if timeout exceeds without application starting.


*watchForProcessesToDieByName(processName, alsoContains=None, looseMatch=False, ignorePids=None, timeout=30)*

Watches for a process, noted by processName and a list "alsoContains" to die. ignorePids contains an optional list of pids which will be ignored (like if starting a new app kills the old app, you would exclude the new app's pid)

*watchForProcessesToDieByPids(pids, ignorePids=None, timeout=30)*

Watches for process noted by various pids to die. ignorePids contains a list of pids to ignore.
