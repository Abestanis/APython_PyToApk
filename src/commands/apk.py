from __future__ import absolute_import

import os
import shutil
import subprocess
from argparse import REMAINDER

from ..logger import Logger
from ..utils import git
from ..utils.apktemplate import ApkTemplateFiller
from ..utils.argparser import SubCmdArgParser, ArgumentParserError, InfoActionProcessed
from ..utils.files import deleteDir, mkDirs, resolvePath


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
    sourceConfig = None
    buildDebug = False
    doInstall = False
    installArgs = None

    def __init__(self, config):
        self.config = config
        self.apkBuildDir = os.path.join(config.buildDir, 'apk')
        self.apkTemplateDir = os.path.join(config.templateDir, 'apk')
        self.apkOutputDir = os.path.join(config.outputDir, 'apk')
        self.readConfig()

    def readConfig(self):
        section = self.config.getSection('apk')
        if section is None:
            self.config.logger.warn('Failed to read any config for the apk command '
                                    'from the config file.')
            return
        if section.hasOption('templateGit'):
            self.templateGit = section.get('templateGit')
        if section.hasOption('sourceDir'):
            self.sourceDir = section.get('sourceDir', evaluatePath=True)
        if section.hasOption('sourceConfig'):
            self.sourceConfig = section.get('sourceConfig', evaluatePath=True)
        if not self.buildDebug and section.hasOption('buildDebug'):
            self.buildDebug = section.getBoolean('buildDebug')
        if not self.doInstall and section.hasOption('install'):
            self.doInstall = section.getBoolean('install')

    def parseCommandArgs(self, args):
        parser = SubCmdArgParser(prog='build.py apk')  # TODO: Description
        parser.add_argument('--templateGit', help='The url to the git file of repository that '
                                                  'provides the template for the app.')
        parser.add_argument('--sourceDir', help='The path to the directory that '
                                                'contains the source code of your python program.')
        parser.add_argument('--sourceConfig',
                            help='The path to the file that contains the configuration of your '
                                 'python program. For more information on the app configuration, '
                                 'visit https://github.com/Abestanis/APython_PyToApk/blob/main'
                                 '/docs/apkGeneration.md. Defaults to setup.cfg in the sourceDir.')
        parser.add_argument('--buildDebug', action='store_true', default=self.buildDebug,
                            help='If specified, the generated apk will be '
                                 'signed with a debug key and will not be optimized '
                                 '(see https://developer.android.com/studio/build/'
                                 'building-cmdline.html#DebugMode).')
        parser.add_argument('--install', nargs=REMAINDER,
                            help='If specified, the install command will be '
                                 'executed after the build command with the arguments provided.')
        cmdArgs = parser.parse_args(args)
        if 'templateGit' in cmdArgs and cmdArgs.templateGit is not None:
            self.templateGit = cmdArgs.templateGit
        if 'sourceDir' in cmdArgs and cmdArgs.sourceDir is not None:
            self.sourceDir = resolvePath(cmdArgs.sourceDir, self.config.currDir)
        if 'sourceConfig' in cmdArgs and cmdArgs.sourceConfig is not None:
            self.sourceConfig = resolvePath(cmdArgs.sourceConfig, self.config.currDir)
        if 'buildDebug' in cmdArgs and cmdArgs.buildDebug is not None:
            self.buildDebug = cmdArgs.buildDebug
        if 'install' in cmdArgs and cmdArgs.install is not None:
            self.doInstall = True
            self.installArgs = cmdArgs.install

    def validateConfig(self):
        valid = True
        if self.config.sdkPath is None:
            valid = False
            self.config.logger.error('The path to the sdk directory was not specified!')
        if self.templateGit is None:
            valid = False
            self.config.logger.error('The url to the template repository git file '
                                     'was not specified!')
        if self.sourceDir is None:
            valid = False
            self.config.logger.error('The path to the source directory of your python program '
                                     'was not specified!')
        elif not os.path.isdir(self.sourceDir):
            valid = False
            self.config.logger.error('The path to the source directory of your python program '
                                     'does not point to an existing directory: ' + self.sourceDir)
        if self.sourceConfig is None:
            if self.sourceDir is not None:
                self.sourceConfig = os.path.join(self.sourceDir, 'setup.cfg')
                if not os.path.isfile(self.sourceConfig):
                    self.sourceConfig = None
        elif os.path.isdir(self.sourceConfig):
            valid = False
            self.config.logger.error('The path to the source configuration file of your python '
                                     'program points to an existing directory: {path}'
                                     .format(path=self.sourceConfig))
        return valid

    def ensureTemplate(self, allowUpdate=True):
        self.config.logger.info('Checking template from {path}...'.format(path=self.templateGit))
        if git.isInitalized(self.apkTemplateDir):
            return (not allowUpdate) or git.update(self.config.gitPath,
                                                   self.apkTemplateDir, self.config.logger)
        return git.initialize(self.config.gitPath, self.templateGit,
                              self.apkTemplateDir, self.config.logger)

    def fillTemplate(self):
        self.config.logger.info('Copying template to build directory...')
        shutil.copytree(self.apkTemplateDir, self.apkBuildDir,
                        ignore=lambda src, names: ['.git'])
        apkTemplateFiller = ApkTemplateFiller(self.apkBuildDir, self.config.logger)
        if self.sourceConfig is not None:
            if not apkTemplateFiller.loadConfigFile(self.sourceConfig):
                return False
        self.config.logger.info('Filling template...')
        return apkTemplateFiller.fillTemplate(self.config.sdkPath)

    def copyPythonSources(self):
        pythonSourceDest = os.path.join(self.apkBuildDir, self.pythonSubPath)
        self.config.logger.info('Cleaning examplePython sources from the template from {path}...'
                                .format(path=pythonSourceDest))
        shutil.rmtree(pythonSourceDest)
        self.config.logger.info('Copying Python sources from {path}...'.format(path=self.sourceDir))
        shutil.copytree(self.sourceDir, pythonSourceDest)
        return True

    def build(self, debug=False):
        self.config.logger.info('Building apk...')
        self.config.logger.verbose('debug = ' + str(debug))
        gradleScript = 'gradlew.bat' if os.name == 'nt' else 'gradlew'
        cmd = 'assembleDebug' if debug else 'assembleRelease'
        args = [os.path.join(self.apkBuildDir, gradleScript), cmd]
        if self.config.logger.getLogPriority() == Logger.PRIORITY_VERBOSE:
            args += ['--info', '--stacktrace']
        self.config.logger.verbose('Calling ' + subprocess.list2cmdline(args))
        if not subprocess.call(args, cwd=self.apkBuildDir) == 0:
            self.config.logger.error('Generating the apk failed!')
            return None
        apkPath = os.path.join(self.apkBuildDir, self.apkSubPath,
                               'debug' if debug else 'release', self.DEBUG_APK if debug else self.RELEASE_APK)
        if not os.path.exists(apkPath):
            return None
        return apkPath

    def run(self, cmdArgs):
        try:
            self.parseCommandArgs(cmdArgs)
        except InfoActionProcessed:
            return True
        except ArgumentParserError as e:
            return e.code == 0
        if not self.validateConfig():
            return False
        if not deleteDir(self.apkBuildDir):
            self.config.logger.error('Failed to delete the contents of the specified build '
                                     'directory "{dir}"!'.format(dir=self.apkBuildDir))
            return False
        if not self.ensureTemplate(not self.config.avoidNetwork):
            return False
        if not self.fillTemplate():
            return False
        if not self.copyPythonSources():
            return False
        apkPath = self.build(self.buildDebug)
        if apkPath is None:
            return False
        outputApkPath = None
        if mkDirs(self.apkOutputDir):
            shutil.copy(apkPath, self.apkOutputDir)
            outputApkPath = os.path.join(self.apkOutputDir, os.path.basename(apkPath))
            deleteDir(self.apkBuildDir)
        if outputApkPath is None or not os.path.exists(outputApkPath):
            self.config.logger.warn('Failed to copy the generated apk to the output directory.')
            outputApkPath = apkPath
        self.config.logger.info('The apk was successfully build and is stored at:\n{path}'
                                .format(path=outputApkPath))
        if self.doInstall:
            from .install import run as run_install
            return run_install(self.config, self.installArgs)
        return True


def run(config, cmdArgs):
    apkBuilder = ApkBuilder(config)
    return apkBuilder.run(cmdArgs)
