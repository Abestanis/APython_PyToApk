"""
This script converts your Python program into an application that can start
on Android and will run your Python code with the Python interpreter
provided by the APython project (see https://github.com/Abestanis/APython).

It is also capable of packaging a python module for Android and correctly
compiling any C or C++ code in the module.

Created 25.05.2016 by Sebastian Scholz.
"""

import os
import sys

from argparse import ArgumentParser, REMAINDER
from src.config import Config


class PyToApk(object):
    config = None
    commandArgs = None

    def __init__(self, cmdArgs):
        super(PyToApk, self).__init__()
        self.config = Config(os.path.dirname(os.path.realpath(__file__)))
        self.config.parseCmdArgs(cmdArgs)
        self.commandArgs = cmdArgs.commandArgs

    def executeTask(self, task):
        if not self.config.validateValues():
            return False
        command = getattr(getattr(__import__('src.commands.' + task), 'commands'), task)
        success = False
        try:
            success = command.run(self.config, self.commandArgs)
        except KeyboardInterrupt:
            self.config.logger.error('Cancelling build due to interrupt.')
        except Exception as e:
            import traceback
            self.config.logger.error('Caught exception: ' + str(e))
            output = self.config.logger.getOutput()
            output = sys.stderr if output == sys.stdout else output
            traceback.print_exception(*sys.exc_info(), file=output)
        finally:
            return success


if __name__ == '__main__':
    parser = ArgumentParser(description=__doc__)
    commandFiles = os.listdir(os.path.join(os.path.dirname(__file__), 'src', 'commands'))
    commands = [commandFile[:-3] for commandFile in commandFiles
                if commandFile != '__init__.py' and commandFile[-3:] == '.py']
    parser.add_argument('action', choices=commands,
                        help='Specifies the action to execute.')
    parser.add_argument('commandArgs', nargs=REMAINDER,
                        help='The arguments for the specified action')
    parser.add_argument('--logFile', help='The path to a log file. If not specified, '
                                          'all output goes to stdout.')
    parser.add_argument('--logLevel', choices=['verbose', 'v', 'info', 'i', 'warn',
                                               'w', 'error', 'e', 'none', 'n'],
                        help='Specify the log level. "none" means no output except the result. '
                             'Defaults to "info".')
    parser.add_argument('--configFile', default='config.cfg',
                        help='The path to the config file. Defaults to the file '
                             '"config.cfg" in the current directory.')
    parser.add_argument('--buildDir', default='build',
                        help='The path to the build directory. Defaults to the directory '
                             '"build" in the current directory.')
    parser.add_argument('--outputDir', default='output',
                        help='The path to the output directory. Defaults to the directory '
                             '"output" in the current directory.')
    parser.add_argument('--templateDir', default='template',
                        help='The path to the template directory. Defaults to the directory '
                             '"template" in the current directory.')
    parser.add_argument('--gitPath', help='The path to the git executable (git.exe).')
    parser.add_argument('--sdkPath', help='The path to the installation directory of '
                                          'the Android Software Development Kit (sdk).')
    parser.add_argument('--ndkPath', help='The path to the installation directory of '
                                          'the Android Native Development Kit (ndk).')
    parser.add_argument('--avoidNetwork', action='store_true',
                        help='Specify if this program should avoid using the internet '
                             'if possible (e.g. to search for updates of templates).')

    args = parser.parse_args()
    pyToApk = PyToApk(args)
    result = pyToApk.executeTask(args.action)
    pyToApk.config.logger.write('Executing command {cmd} {suc}!'
                                .format(cmd=args.action, suc='SUCCEEDED' if result else 'FAILED'),
                                isError=not result)
    pyToApk.config.logger.closeLogFile()
    sys.exit(0 if result else 1)
