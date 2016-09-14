import os
from ConfigParser import ConfigParser
from logger import Logger

class Config(object):
    
    class ConfigSection:
        _parser = None
        _sectionName = None
        
        def __init__(self, parser, sectionName):
            self._parser = parser
            self._sectionName = sectionName
        
        def hasOption(self, name):
            return self._parser.has_option(self._sectionName, name)
        
        def get(self, name):
            return self._parser.get(self._sectionName, name)
        
        def getBoolean(self, name):
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
    
    def loadConfigFile(self, configPath, configureLogging = True):
        if configPath == None:
            configPath = os.path.join(self.currDir, 'config.cfg')
        if not self._loadConfigFile(configPath):
            return False
        if configureLogging:
            self._parseLoggingConfig()
        if self._parser.has_option('General', 'avoidNetwork'):
            self.avoidNetwork = self._parser.getboolean('General', 'avoidNetwork')
        if self._parser.has_option('Paths', 'buildDir'):
            self.buildDir = self.evaluatePath(self._parser.get('Paths', 'buildDir'))
        if self._parser.has_option('Paths', 'outputDir'):
            self.outputDir = self.evaluatePath(self._parser.get('Paths', 'outputDir'))
        if self._parser.has_option('Paths', 'templateDir'):
            self.templateDir = self.evaluatePath(self._parser.get('Paths', 'templateDir'))
        if self._parser.has_option('Paths', 'gitPath'):
            self.gitPath = self.evaluatePath(self._parser.get('Paths', 'gitPath'))
        if self._parser.has_option('Paths', 'sdkPath'):
            self.sdkPath = self.evaluatePath(self._parser.get('Paths', 'sdkPath'))
        if self._parser.has_option('Paths', 'ndkPath'):
            self.ndkPath = self.evaluatePath(self._parser.get('Paths', 'ndkPath'))
        return True
    
    def parseCmdArgs(self, args):
        self._parseLoggingConfig(args)
        self.loadConfigFile(args.configFile, configureLogging = False)
        if 'avoidNetwork' in args and args.avoidNetwork: # Is not specified if False
            self.avoidNetwork = args.avoidNetwork
        if 'buildDir' in args and args.buildDir != None:
            self.buildDir = self.evaluatePath(args.buildDir)
        if 'outputDir' in args and args.outputDir != None:
            self.outputDir = self.evaluatePath(args.outputDir)
        if 'templateDir' in args and args.templateDir != None:
            self.templateDir = self.evaluatePath(args.templateDir)
        if 'gitPath' in args and args.gitPath != None:
            self.gitPath = self.evaluatePath(args.gitPath)
        if 'sdkPath' in args and args.sdkPath != None:
            self.sdkPath = self.evaluatePath(args.sdkPath)
        if 'ndkPath' in args and args.ndkPath != None:
            self.ndkPath = self.evaluatePath(args.ndkPath)
        return True
    
    def validateValues(self):
        valid = True
        def _checkDir(path, name, allowMissing = False, requireExist = True):
            if path == None:
                if allowMissing: return
                valid = False
                self.logger.error('Invalid configuration: No path for the ' +
                                  name +' directory given!')
            elif os.path.isfile(path):
                valid = False
                self.logger.error('Invalid configuration: The path to the ' + name +
                                  ' directory points to an existing file (' + path + ')!')
            elif requireExist and not os.path.isdir(path):
                valid = False
                self.logger.error('Invalid configuration: The path to the ' + name +
                                  ' directory does not point to an existing directory ('
                                  + path + ')!')
        
        _checkDir(self.buildDir, 'build', requireExist = False)
        _checkDir(self.outputDir, 'output', requireExist = False)
        _checkDir(self.templateDir, 'template', requireExist = False)
        _checkDir(self.sdkPath, 'ndk', allowMissing = True)
        _checkDir(self.ndkPath, 'sdk', allowMissing = True)
        if self.gitPath != None and not os.path.isfile(self.gitPath):
            valid = False
            self.logger.error('Invalid configuration: The path to the git executable' +
                              ' is invalid (' + self.gitPath + ')!')
        return valid
    
    def getSection(self, sectionName):
        if self._parser == None or not self._parser.has_section(sectionName):
            return None
        return self.ConfigSection(self._parser, sectionName)
    
    def evaluatePath(self, path):
        if path == None: return None
        path = os.path.expanduser(os.path.expandvars(path))
        if os.path.isabs(path):
            return path
        return os.path.join(self.currDir, path)
    
    def _loadConfigFile(self, path):
        if self._parser != None: return True
        self._parser = ConfigParser()
        path = self.evaluatePath(path)
        if  not path in self._parser.read(path):
            self.logger.warn('Failed to read the config file from ' + path)
            return False
        return True
        
    
    def _parseLoggingConfig(self, cmdArgs = None):
        cmdHasLevel = cmdHasFile = False
        if cmdArgs is not None:
            if 'logFile' in cmdArgs and cmdArgs.logFile != None:
                if self.logger.setLogFile(self.evaluatePath(cmdArgs.logFile)):
                    cmdHasFile = True
            if 'logLevel' in cmdArgs and cmdArgs.logLevel != None:
                if self._parseLogLevel(cmdArgs.logLevel):
                    cmdHasLevel = True
        if not self._loadConfigFile(cmdArgs.configFile): return
        if not cmdHasFile and self._parser.has_option('Paths', 'logFile'):
            logFile = self.evaluatePath(self._parser.get('Paths', 'logFile'))
            self.logger.setLogFile(logFile)
        if not cmdHasLevel and self._parser.has_option('General', 'logLevel'):
            self._parseLogLevel(self._parser.get('General', 'logLevel'))
    
    def _parseLogLevel(self, logLevel):
        LOG_LEVELS = {
            'verbose': Logger.PRIORITY_VERBOSE,
            'info':    Logger.PRIORITY_INFO,
            'warn':    Logger.PRIORITY_WARN,
            'error':   Logger.PRIORITY_ERROR,
            'none':    Logger.PRIORITY_NONE,
        }
        logLevel = logLevel.strip().lower()
        key = None
        if logLevel in LOG_LEVELS.keys():
            key = logLevel
        elif len(logLevel) == 1: # Allow 'v', 'i', 'w', 'e' and 'n'
            for name in LOG_LEVELS.keys():
                if name[0] == logLevel:
                    key = name
                    break
        if key is not None:
            self.logger.setPriority(LOG_LEVELS[key])
            return True
        self.logger.warn('Failed to parse invalid log level "' + logLevel + '"')
        return False
