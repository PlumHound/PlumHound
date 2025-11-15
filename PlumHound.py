#!/usr/bin/env python
# -*- coding: utf8 -*-

# PlumHound https://github.com/PlumHound/PlumHound | https://plumhound.defensiveorigins.com/
# BloodHoundAD Wrapper for Purple Teams | https://github.com/BloodHoundAD/BloodHound
# BloodHound CE (Newest version) can also be used | https://github.com/SpecterOps/BloodHound

# GNU GPL 3.0

import sys
import traceback

# Import PlumHound libraries
import lib.phCheckPython 
import lib.phCLImanagement
import lib.phNotifyArgs
import lib.phTasks
import lib.phDatabase

ph_version = "1.6"


def main() -> int:
    """
    Main entry point for PlumHound CLI. Returns an exit code (0 success, non-zero error).
    This function is referenced by the pyproject entry point: PlumHound:main
    """
    try:
        # Check if Py2 environment.  If not executing in Python3, exit nicely.
        lib.phCheckPython.CheckPython2()

        # Commandline Arguments (ArgParse) configuration
        phArgs = lib.phCLImanagement.SetupArguments(ph_version)

        # Check if Py3 environment.  If not expected version of 3, notify nicely
        lib.phCheckPython.CheckPython3(phArgs)

        # Report execution parameters
        lib.phNotifyArgs.NotifyArgs(phArgs, ph_version)

        # Generate TaskList (jobs)
        phTaskList = lib.phTasks.MakeTaskList(phArgs)

        # Setup Driver (excluding BlueHound)
        phDriver = lib.phDatabase.setup_database_conn(phArgs)

        # Execute Jobs in Task List
        lib.phTasks.TaskExecution(phTaskList, phDriver, phArgs)

        # Close the neoj4 connection.
        lib.phDatabase.close_database_con(phArgs, phDriver)

        return 0
    except SystemExit:
        # Let argparse or other code call sys.exit() behave normally
        raise
    except Exception:
        # Print traceback for visibility when used as a console command
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

