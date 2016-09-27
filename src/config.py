import os
from ConfigParser import ConfigParser
from logger import Logger
from utils.files import resolvePath

class Config(object):
    
    class ConfigSection:
        _parser = None
        _sectionName = None
        _currDir = None
        
        def __init__(self, parser, sectionName, currDir):
            self._parser = parser
            self._sectionName = sectionName
            self._currDir = currDir
        
        def hasOption(self, name):
            return self._parser.has_option(self._sectionName, name)
        
        def get(self, name, evaluatePath = False):
            result = self._parser.get(self._sectionName, name)
            if evaluatePath: result = resolvePath(result, self._currDir)
            return result
        
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
            self.buildDir = resolvePath(self._parser.get('Paths', 'buildDir'), self.currDir)
        if self._parser.has_option('Paths', 'outputDir'):
            self.outputDir = resolvePath(self._parser.get('Paths', 'outputDir'), self.currDir)
        if self._parser.has_option('Paths', 'templateDir'):
            self.templateDir = resolvePath(self._parser.get('Paths', 'templateDir'), self.currDir)
        if self._parser.has_option('Paths', 'gitPath'):
            self.gitPath = resolvePath(self._parser.get('Paths', 'gitPath'), self.currDir)
        if self._parser.has_option('Paths', 'sdkPath'):
            self.sdkPath = resolvePath(self._parser.get('Paths', 'sdkPath'), self.currDir)
        if self._parser.has_option('Paths', 'ndkPath'):
            self.ndkPath = resolvePath(self._parser.get('Paths', 'ndkPath'), self.currDir)
        return True
    
    def parseCmdArgs(self, args):
        self._parseLoggingConfig(args)
        self.loadConfigFile(args.configFile, configureLogging = False)
        if 'avoidNetwork' in args and args.avoidNetwork: # Is not specified if False
            self.avoidNetwork = args.avoidNetwork
        if 'buildDir' in args and args.buildDir != None:
            self.buildDir = resolvePath(args.buildDir, self.currDir)
        if 'outputDir' in args and args.outputDir != None:
            self.outputDir = resolvePath(args.outputDir, self.currDir)
        if 'templateDir' in args and args.templateDir != None:
            self.templateDir = resolvePath(args.templateDir, self.currDir)
        if 'gitPath' in args and args.gitPath != None:
            self.gitPath = resolvePath(args.gitPath, self.currDir)
        if 'sdkPath' in args and args.sdkPath != None:
            self.sdkPath = resolvePath(args.sdkPath, self.currDir)
        if 'ndkPath' in args and args.ndkPath != None:
            self.ndkPath = resolvePath(args.ndkPath, self.currDir)
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
        _checkDir(self.sdkPath, 'sdk', allowMissing = True)
        _checkDir(self.ndkPath, 'ndk', allowMissing = True)
        if self.gitPath != None and not os.path.isfile(self.gitPath):
            valid = False
            self.logger.error('Invalid configuration: The path to the git executable' +
                              ' is invalid (' + self.gitPath + ')!')
        return valid
    
    def getSection(self, sectionName):
        if self._parser == None or not self._parser.has_section(sectionName):
            return None
        return self.ConfigSection(self._parser, sectionName, self.currDir)
    
    def _loadConfigFile(self, path):
        if self._parser != None: return True
        self._parser = ConfigParser()
        path = resolvePath(path, self.currDir)
        if  not path in self._parser.read(path):
            self.logger.warn('Failed to read the config file from ' + path)
            return False
        return True
        
    
    def _parseLoggingConfig(self, cmdArgs = None):
        cmdHasLevel = cmdHasFile = False
        if cmdArgs is not None:
            if 'logFile' in cmdArgs and cmdArgs.logFile != None:
                if self.logger.setLogFile(resolvePath(cmdArgs.logFile, self.currDir)):
                    cmdHasFile = True
            if 'logLevel' in cmdArgs and cmdArgs.logLevel != None:
                if self._parseLogLevel(cmdArgs.logLevel):
                    cmdHasLevel = True
        if not self._loadConfigFile(cmdArgs.configFile): return
        if not cmdHasFile and self._parser.has_option('Paths', 'logFile'):
            logFile = resolvePath(self._parser.get('Paths', 'logFile'), self.currDir)
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
