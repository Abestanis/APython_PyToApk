from __future__ import absolute_import

import os

try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser
from .logger import Logger
from .utils.files import resolvePath


class Config(object):
    """
    Holds a general set of configuration for all commands as
    well as a logger object and a handle to the configuration file
    to receive sections from it.
    """

    class ConfigSection:
        """A handle to a section from a configuration file."""
        _parser = None
        _sectionName = None
        _currDir = None

        def __init__(self, parser, sectionName, currDir):
            self._parser = parser
            self._sectionName = sectionName
            self._currDir = currDir

        def hasOption(self, name):
            """>>> hasOption(name) -> boolean
            Returns True if the section has an option
            with the given name.
            """
            return self._parser.has_option(self._sectionName, name)

        def get(self, name, evaluatePath=False):
            """>>> get(name, evaluatePath) -> string
            Returns the value of the option named name in this section.
            If evaluatePath is True, the value is treated as a
            path and will be resolved to an absolute path.
            """
            result = self._parser.get(self._sectionName, name)
            if evaluatePath:
                result = resolvePath(result, self._currDir)
            return result

        def getBoolean(self, name):
            """>>> getBoolean(name) -> boolean
            Returns the boolean value of the option named name
            in this section.
            """
            return self._parser.getboolean(self._sectionName, name)

    _parser = None
    logger = Logger()
    currDir = None
    avoidNetwork = False
    buildDir = None
    outputDir = None
    templateDir = None
    gitPath = None
    sdkPath = None
    ndkPath = None

    def __init__(self, currDir):
        self.currDir = currDir

    def loadConfigFile(self, configPath, configureLogging=True):
        """>>> loadConfigFile(configPath, configureLogging) -> success
        Loads all configuration possible from the given
        configuration file. If configureLogging is False
        no configuration specific to logging is loaded.
        """
        if configPath is None:
            configPath = os.path.join(self.currDir, 'config.cfg')
        if not self._loadConfigFile(configPath):
            return False
        if configureLogging:
            self._parseLoggingConfig()
        if self._parser.has_option('General', 'avoidNetwork'):
            self.avoidNetwork = self._parser.getboolean('General', 'avoidNetwork')
        if self._parser.has_option('Paths', 'buildDir'):
            self.buildDir = resolvePath(self._parser.get('Paths', 'buildDir'), self.currDir)
        if self._parser.has_option('Paths', 'outputDir'):
            self.outputDir = resolvePath(self._parser.get('Paths', 'outputDir'), self.currDir)
        if self._parser.has_option('Paths', 'templateDir'):
            self.templateDir = resolvePath(self._parser.get('Paths', 'templateDir'), self.currDir)
        if self._parser.has_option('Paths', 'gitPath'):
            self.gitPath = self._parser.get('Paths', 'gitPath')
        if self._parser.has_option('Paths', 'sdkPath'):
            self.sdkPath = resolvePath(self._parser.get('Paths', 'sdkPath'), self.currDir)
        if self._parser.has_option('Paths', 'ndkPath'):
            self.ndkPath = resolvePath(self._parser.get('Paths', 'ndkPath'), self.currDir)
        return True

    def parseCmdArgs(self, args):
        """>>> parseCmdArgs(args) -> success
        Parses the given command line arguments.
        Also loads the configuration file if one was
        specified by the command line arguments.
        """
        self._parseLoggingConfig(args)
        if not self.loadConfigFile(args.configFile, configureLogging=False):
            return False
        if 'avoidNetwork' in args and args.avoidNetwork:  # Is not specified if False
            self.avoidNetwork = args.avoidNetwork
        if 'buildDir' in args and args.buildDir is not None:
            self.buildDir = resolvePath(args.buildDir, self.currDir)
        if 'outputDir' in args and args.outputDir is not None:
            self.outputDir = resolvePath(args.outputDir, self.currDir)
        if 'templateDir' in args and args.templateDir is not None:
            self.templateDir = resolvePath(args.templateDir, self.currDir)
        if 'gitPath' in args and args.gitPath is not None:
            self.gitPath = args.gitPath
        if 'sdkPath' in args and args.sdkPath is not None:
            self.sdkPath = resolvePath(args.sdkPath, self.currDir)
        if 'ndkPath' in args and args.ndkPath is not None:
            self.ndkPath = resolvePath(args.ndkPath, self.currDir)
        return True

    def validateValues(self):
        """>>> validateValues() -> boolean
        Validate that the current config values are
        correct. Note that some config fields are allowed
        to be empty: sdkPath, ndkPath and gitPath.
        """
        valid = True

        def _checkDir(path, name, allowMissing=False, requireExist=True):
            if path is None:
                if allowMissing:
                    return True
                self.logger.error('Invalid configuration: No path for the {name} directory given!'
                                  .format(name=name))
                return False
            elif os.path.isfile(path):
                self.logger.error('Invalid configuration: The path to the {name} directory points '
                                  'to an existing file ({path})!'.format(name=name, path=path))
                return False
            elif requireExist and not os.path.isdir(path):
                self.logger.error('Invalid configuration: The path to the {name} directory does '
                                  'not point to an existing directory ({path})!'
                                  .format(name=name, path=path))
                return False
            return True

        valid = _checkDir(self.buildDir, 'build', requireExist=False) and valid
        valid = _checkDir(self.outputDir, 'output', requireExist=False) and valid
        valid = _checkDir(self.templateDir, 'template', requireExist=False) and valid
        valid = _checkDir(self.sdkPath, 'sdk', allowMissing=True) and valid
        valid = _checkDir(self.ndkPath, 'ndk', allowMissing=True) and valid
        if self.gitPath is not None and os.system(self.gitPath + ' --version') != 0:
            valid = False
            self.logger.error('Invalid configuration: The path to the git executable is invalid '
                              '({path})'.format(path=self.gitPath))
        return valid

    def getSection(self, sectionName):
        """>>> getSection(sectionName) -> Section or None
        Get the section with the sectionName from the
        loaded configuration file.
        """
        if self._parser is None or not self._parser.has_section(sectionName):
            return None
        return self.ConfigSection(self._parser, sectionName, self.currDir)

    def _loadConfigFile(self, path):
        """>>> _loadConfigFile(path) -> success
        Load the config file at path in a new
        ConfigParser.
        """
        if self._parser is not None:
            return True
        self._parser = RawConfigParser()
        path = resolvePath(path, self.currDir)
        if path not in self._parser.read(path):
            self.logger.warn('Failed to read the config file from ' + path)
            return False
        return True

    def _parseLoggingConfig(self, cmdArgs=None):
        """>>> _parseLoggingConfig(cmdArgs)
        Parse all logging related configuration from the
        given command line arguments and from any configuration
        file specified by the arguments.
        """
        cmdHasLevel = cmdHasFile = False
        if cmdArgs is not None:
            if 'logFile' in cmdArgs and cmdArgs.logFile is not None:
                if self.logger.setLogFile(resolvePath(cmdArgs.logFile, self.currDir)):
                    cmdHasFile = True
            if 'logLevel' in cmdArgs and cmdArgs.logLevel is not None:
                if self._parseLogLevel(cmdArgs.logLevel):
                    cmdHasLevel = True
        if not self._loadConfigFile(cmdArgs.configFile):
            return
        if not cmdHasFile and self._parser.has_option('Paths', 'logFile'):
            logFile = resolvePath(self._parser.get('Paths', 'logFile'), self.currDir)
            self.logger.setLogFile(logFile)
        if not cmdHasLevel and self._parser.has_option('General', 'logLevel'):
            self._parseLogLevel(self._parser.get('General', 'logLevel'))

    def _parseLogLevel(self, logLevel):
        """>>> _parseLogLevel(logLevel) -> success
        Parse and set the log level of the logger.
        """
        LOG_LEVELS = {
            'verbose': Logger.PRIORITY_VERBOSE,
            'info': Logger.PRIORITY_INFO,
            'warn': Logger.PRIORITY_WARN,
            'error': Logger.PRIORITY_ERROR,
            'none': Logger.PRIORITY_NONE,
        }
        logLevel = logLevel.strip().lower()
        key = None
        if logLevel in LOG_LEVELS.keys():
            key = logLevel
        elif len(logLevel) == 1:  # Allow 'v', 'i', 'w', 'e' and 'n'
            for name in LOG_LEVELS.keys():
                if name[0] == logLevel:
                    key = name
                    break
        if key is not None:
            self.logger.setPriority(LOG_LEVELS[key])
            return True
        self.logger.warn('Failed to parse invalid log level "{level}"'.format(level=logLevel))
        return False
