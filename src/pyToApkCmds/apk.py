import os
import shutil
from utils import git
from utils.apkTemplateCommands import runTemplateCommands
from utils.files import deleteDir, mkdirs
import subprocess
from logger import Logger
from argparse import ArgumentParser


class ApkBuilder(object):
    DEBUG_APK = 'app-debug.apk'
    RELEASE_APK = 'app-release-unsigned.apk'
    apkSubPath = os.path.join('app', 'build', 'outputs', 'apk')
    pythonSubPath = os.path.join('app', 'src', 'main', 'python')
    
    config = None
    apkBuildDir = None
    apkTemplateDir = None
    apkOutputDir = None
    templateGit = None
    sourceDir = None
    buildDebug = False
    
    def __init__(self, config):
        self.config = config
        self.apkBuildDir = os.path.join(config.buildDir, 'apk')
        self.apkTemplateDir = os.path.join(config.templateDir, 'apk')
        self.apkOutputDir = os.path.join(config.outputDir, 'apk')
        self.readConfig()
    
    def readConfig(self):
        section = self.config.getSection('apk')
        if section == None:
            self.config.logger.warn('Failed to read any config for the apk ' +
                                    'command from the config file.')
            return
        if section.hasOption('templateGit'):
            self.templateGit = section.get('templateGit')
        if section.hasOption('sourceDir'):
            self.sourceDir = self.config.evaluatePath(section.get('sourceDir'))
        if section.hasOption('buildDebug'):
            self.buildDebug = section.getBoolean('buildDebug')
    
    def parseCommandArgs(self, args):
        parser = ArgumentParser() # TODO: Description
        parser.add_argument('--templateGit', help = 'The url to the git file of ' +
                            'repository that provides the template for the app.')
        parser.add_argument('--sourceDir', help = 'The path to the directory that ' +
                            'contains the source code of your python program.')
        parser.add_argument('--buildDebug', action = 'store_true', default = self.buildDebug,
                            help = 'If specified, the generated apk will be ' +
                            'signed with a debug key and will not be optimized ' +
                            '(see https://developer.android.com/studio/build/' +
                            'building-cmdline.html#DebugMode).')
        cmdArgs = parser.parse_args(args)
        if 'templateGit' in cmdArgs and cmdArgs.templateGit != None:
            self.templateGit = cmdArgs.templateGit
        if 'sourceDir' in cmdArgs and cmdArgs.sourceDir != None:
            self.sourceDir = self.config.evaluatePath(cmdArgs.sourceDir)
        print(cmdArgs)
        if 'buildDebug' in cmdArgs and cmdArgs.buildDebug != None:
            self.buildDebug = cmdArgs.buildDebug
    
    def validateConfig(self):
        valid = True
        if self.templateGit == None:
            valid = False
            self.config.logger.error('The url to the template repository git ' +
                                     'file was not specified!')
        if self.sourceDir == None:
            valid = False
            self.config.logger.error('The path to the source directory of your ' +
                                     'python program was not specified!')
        elif not os.path.isdir(self.sourceDir):
            valid = False
            self.config.logger.error('The path to the source directory of your ' +
                                     'python program does not point to an ' +
                                     'existing directory: ' + self.sourceDir)
        return valid
    
    def ensureTemplate(self, allowUpdate = True):
        self.config.logger.info('Checking template from ' + self.templateGit + '...')
        if git.isInitalized(self.apkTemplateDir):
            return (not allowUpdate) or git.update(self.config.gitPath,
                                                   self.apkTemplateDir, self.config.logger)
        return git.initialize(self.config.gitPath, self.templateGit,
                              self.apkTemplateDir, self.config.logger)
    
    def fillTemplate(self):
        self.config.logger.info('Filling template...')
        formatArgs = {
            'appLogTag': 'MyPythonApp',
            'windowType': 'SDL',
            'minPyVersion': '3.5',
            'requirements': 'twisted',
        }
        shutil.copytree(self.apkTemplateDir, self.apkBuildDir,
                        ignore = lambda src, names: ['.git'])
        for dirpath, dirnames, filenames in os.walk(self.apkBuildDir):
            if '.git' in dirnames:
                del(dirnames[dirnames.index('.git')])
            javaFiles = [os.path.join(dirpath, filename) for filename in filenames
                         if filename[-5:] == '.java']
            for javaFile in javaFiles:
                lines = []
                with open(javaFile) as f:
                    lines = f.readlines()
                with open(javaFile, 'w') as f:
                    for i in range(len(lines)):
                        f.write(runTemplateCommands(lines[i], formatArgs))
        return self.createPropertiesFile()
    
    def createPropertiesFile(self):
        with open(os.path.join(self.apkBuildDir, 'local.properties'), 'w') as propertiesFile:
            sdkPath = self.config.sdkPath.replace('\\', '\\\\').replace(':', '\\:')
            propertiesFile.write('sdk.dir=' + sdkPath)
        return True
    
    def copyPythonSources(self):
        pythonSourceDest = os.path.join(self.apkBuildDir, self.pythonSubPath)
        self.config.logger.info('Cleaning examplePython sources from the template from ' +
                                pythonSourceDest + '...')
        shutil.rmtree(pythonSourceDest)
        self.config.logger.info('Copying Python sources from ' + self.sourceDir + '...')
        shutil.copytree(self.sourceDir, pythonSourceDest)
        return True
    
    def build(self, debug = False):
        self.config.logger.info('Building apk...')
        self.config.logger.verbose('debug = ' + str(debug))
        gradleScript = 'gradlew.bat' if os.name == 'nt' else 'gradlew'
        cmd = 'assembleDebug' if debug else 'assembleRelease'
        args = [os.path.join(self.apkBuildDir, gradleScript), cmd]
        if self.config.logger.getLogPriority() == Logger.PRIORITY_VERBOSE:
            args += ['--info', '--stacktrace']
        self.config.logger.verbose('Calling ' + subprocess.list2cmdline(args))
        if not subprocess.call(args, cwd = self.apkBuildDir) == 0:
            return None
        apkPath = os.path.join(self.apkBuildDir, self.apkSubPath, self.DEBUG_APK if debug else self.RELEASE_APK)
        if not os.path.exists(apkPath):
            return None
        return apkPath
    
    def run(self, cmdArgs):
        self.parseCommandArgs(cmdArgs)
        if not self.validateConfig():
            return False
        if not deleteDir(self.apkBuildDir):
            self.config.logger.error('Failed to delete the contents of the ' +
                                     'specified build directory "' +
                                     self.apkBuildDir + '"!')
            return False
        if not self.ensureTemplate(not self.config.avoidNetwork):
            return False
        if not self.fillTemplate():
            return False
        if not self.copyPythonSources():
            return False
        apkPath = self.build(self.buildDebug)
        if apkPath == None:
            return False
        outputApkPath = None
        if mkdirs(self.apkOutputDir):
            shutil.copy(apkPath, self.apkOutputDir)
            outputApkPath = os.path.join(self.apkOutputDir, os.path.basename(apkPath))
            deleteDir(self.apkBuildDir)
        if outputApkPath is None or not os.path.exists(outputApkPath):
            self.config.logger.warn('Failed to copy the generated apk to the ' +
                                    'output directory.')
            outputApkPath = apkPath
        self.config.logger.info('The apk was successfully build and is stored at\n' +
                                outputApkPath)
        return True


def run(config, cmdArgs):
    apkBuilder = ApkBuilder(config)
    return apkBuilder.run(cmdArgs)
