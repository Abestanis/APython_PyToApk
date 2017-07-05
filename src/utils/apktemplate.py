from __future__ import absolute_import

import os
import re

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser
from .files import resolvePath
from shutil import copy as copyFile


class ApkTemplateFiller(object):
    """Handles the filling of the apk template."""
    templateDir = None
    logger = None
    _PY_VERSION_REGEX = re.compile(r'\A\d+(\.\d+){0,2}\Z')
    _JAVA_PACKAGE_REGEX = re.compile(r'\A[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*\Z')
    FORMAT_ARG_VERIFIERS = {
        'appLogTag': lambda val: type(val) == str,  # any string
        'windowType': lambda val: val in ['NO_WINDOW', 'TERMINAL', 'SDL',
                                          'WINDOW_MANAGER', 'ANDROID'],
        'minPyVersion':
            lambda val: val is None or ApkTemplateFiller._PY_VERSION_REGEX.search(val) is not None,
        # any Python version or None
        'requirements': lambda val: type(val) == str,  # any string
        'appId': lambda val: ApkTemplateFiller._JAVA_PACKAGE_REGEX.search(val) is not None,
        # any valid java package path
        'appName': lambda val: type(val) == str,  # any string
        'appTargetSdk': lambda val: val.isdigit() and int(val) > 0,  # any positive int
        'appMinSdk': lambda val: val.isdigit() and int(val) > 0,  # any positive int
        'appNumVersion': lambda val: val.isdigit() and 0 < int(val) <= 2100000000,
        # The greatest value Google Play allows for versionCode is 2100000000.
        'appVersion': lambda val: type(val) == str,  # any string
    }
    # These are the values for format arguments that don't have to be specified
    FORMAT_ARG_DEFAULTS = {
        'requirements': '',  # No requirements
        'minPyVersion': '',  # Support all Python versions? Nice! :-)
        'appTargetSdk': None,  # The default target sdk version of the template
    }
    formatArgs = None
    appIcon = None
    appManifestTemplate = None
    FORMAT_FILES_EXT = ['.java', '.xml', '.gradle']
    JAVA_PACKAGE_DIR_PATH = 'app/src/main/java'.replace('/', os.path.sep)
    TEMPLATE_ICON_PATH = 'app/src/main/res/drawable-mdpi/app_launcher_icon.png'.\
        replace('/', os.path.sep)
    TEMPLATE_MANIFEST_PATH = 'app/src/main/AndroidManifest.xml'.replace('/', os.path.sep)

    def __init__(self, templateDir, logger):
        self.templateDir = templateDir
        self.logger = logger

    def validateValues(self):
        """>>> validateValues() -> boolean
        Validate all formatting arguments and fill
        in defaults for some if they are missing.
        """
        valid = True
        for key in self.formatArgs:
            if key not in self.FORMAT_ARG_VERIFIERS:
                self.logger.warn('Found an unknown formatting argument: "{name}"'.format(name=key))
        for argName, validator in self.FORMAT_ARG_VERIFIERS.items():
            if argName not in self.formatArgs:
                if argName in self.FORMAT_ARG_DEFAULTS:
                    self.formatArgs[argName] = self.FORMAT_ARG_DEFAULTS[argName]
                else:
                    self.logger.warn('Missing formatting argument {name}, the default value '
                                     'provided by the template will be used'.format(name=argName))
                    self.formatArgs[argName] = None
            else:
                if not validator(self.formatArgs[argName]):
                    self.logger.error('Invalid value for formatting argument {name}: "{value}"'
                                      .format(name=argName, value=self.formatArgs[argName]))
                    valid = False
        if not valid:
            self.logger.error('See https://github.com/Abestanis/APython_PyToApk/'
                              'blob/master/docs/apkGeneration.md for more information.')
        if self.appIcon is None:
            self.logger.warn('There was no icon specified, the default icon provided by '
                             'the template will be used.')
        elif not os.path.isfile(self.appIcon):
            valid = False
            self.logger.error('The specified icon path does not point to an existing file: {path}'
                              .format(path=self.appIcon))
        if self.appManifestTemplate is not None and not os.path.isfile(self.appManifestTemplate):
            valid = False
            self.logger.error('The specified manifest template path does not point to an '
                              'existing file: {path}'.format(path=self.appManifestTemplate))
        return valid

    def loadConfigFile(self, path):
        """>>> loadConfigFile(path) -> success
        Load formatting arguments from the section
        android_app of configuration file at path.
        """
        parser = ConfigParser()
        if path not in parser.read(path):
            self.logger.error('Failed to read the apps config from {path}'.format(path=path))
            return False
        appDir = os.path.dirname(path)
        if parser.has_section('android_app'):
            if self.formatArgs is None:
                self.formatArgs = {}
            if parser.has_option('android_app', 'app_name'):
                self.formatArgs['appName'] = parser.get('android_app', 'app_name')
            if parser.has_option('android_app', 'app_tag'):
                self.formatArgs['appLogTag'] = parser.get('android_app', 'app_tag')
            if parser.has_option('android_app', 'app_id'):
                self.formatArgs['appId'] = parser.get('android_app', 'app_id')
            if parser.has_option('android_app', 'app_num_version'):
                self.formatArgs['appNumVersion'] = parser.get('android_app', 'app_num_version')
            if parser.has_option('android_app', 'app_icon'):
                self.appIcon = resolvePath(parser.get('android_app', 'app_icon'), appDir)
            if parser.has_option('android_app', 'app_window_type'):
                self.formatArgs['windowType'] = parser.get('android_app', 'app_window_type')
            if parser.has_option('android_app', 'app_min_sdk'):
                self.formatArgs['appMinSdk'] = parser.get('android_app', 'app_min_sdk')
            if parser.has_option('android_app', 'app_target_sdk'):
                self.formatArgs['appTargetSdk'] = parser.get('android_app', 'app_target_sdk')
            if parser.has_option('android_app', 'min_python_version'):
                self.formatArgs['minPyVersion'] = parser.get('android_app', 'min_python_version')
            if parser.has_option('android_app', 'requirements'):
                self.formatArgs['requirements'] = parser.get('android_app', 'requirements')
            if parser.has_option('android_app', 'app_manifest_template'):
                self.appManifestTemplate = resolvePath(
                    parser.get('android_app', 'app_manifest_template'), appDir)
            if len(self.formatArgs) == 0:
                if self.appIcon is None and self.appManifestTemplate is None:
                    self.logger.warn('No configuration found in the setup.py at ' + path)
                self.formatArgs = None
        else:
            self.logger.warn('No configuration found in the setup.py at {path}: '
                             'No configuration found called "android_app".'.format(path=path))
        return True

    def loadConfigFromSetupPy(self, path):
        pass

    def copyIcon(self):
        """>>> copyIcon() -> success
        Copy the custom icon of the Python program
        into the template, if one was specified.
        """
        if self.appIcon is None:
            return True
        self.logger.info('Copying icon file...')
        templateIconPath = os.path.join(self.templateDir, self.TEMPLATE_ICON_PATH)
        if not os.path.exists(templateIconPath):
            self.logger.error('Could not find the icon file of the template at {path}'
                              .format(path=templateIconPath))
            return False
        os.remove(templateIconPath)
        copyFile(self.appIcon, templateIconPath)
        return True

    def copyCustomManifestTemplate(self):
        """>>> copyCustomManifestTemplate() -> success
        Copy the custom manifest template of the Python
        program into the template, if one was specified.
        """
        if self.appManifestTemplate is None:
            return True
        templateManifestPath = os.path.join(self.templateDir, self.TEMPLATE_MANIFEST_PATH)
        self.logger.info('Copying manifest template...')
        if not os.path.exists(templateManifestPath):
            self.logger.error('Could not find the manifest file of the template at {path}'
                              .format(path=templateManifestPath))
            return False
        os.remove(templateManifestPath)
        copyFile(self.appManifestTemplate, templateManifestPath)
        return True

    def changePackageName(self):
        """>>> changePackageName() -> success
        Rename the directory that makes up the package name.
        """
        parentDirPath = os.path.join(self.templateDir, self.JAVA_PACKAGE_DIR_PATH)
        if not os.path.isdir(parentDirPath):
            self.logger.error('Failed to find the directory that describes the package path: '
                              '{path} is not an existing directory!'.format(path=parentDirPath))
            return False
        packageNameDirs = [path for path in os.listdir(parentDirPath)
                           if os.path.isdir(os.path.join(parentDirPath, path))]
        if len(packageNameDirs) == 0:
            self.logger.error('Failed to find the directory that describes the package path: '
                              '{path} has no child directories!'.format(path=parentDirPath))
            return False
        elif len(packageNameDirs) > 1:
            self.logger.warn('Found multiple possible directories that describe the package path: '
                             '{paths}'.format(paths=', '.join(packageNameDirs)))
        os.rename(os.path.join(parentDirPath, packageNameDirs[0]),
                  os.path.join(parentDirPath, self.formatArgs['appId']))
        return True

    def _fillVarInText(self, text):
        """>>> _fillVarInText(text) -> string
        Replace any default value with the corresponding
        formatting argument, if there is a replace command
        in the text.
        """
        cmdStart = text.find('REPLACE(')
        if cmdStart == -1:
            return text
        cmdData = text[cmdStart + len('REPLACE('):]
        paramEndIndex = cmdData.find(')')
        if paramEndIndex != -1:
            indexes = [index.strip() for index in cmdData[:paramEndIndex].split(',')]
            if len(indexes) == 2 or not all(map(lambda index: index.isdigit(), indexes)):
                indexes = [int(index) for index in indexes]
                key = cmdData[cmdData.find(':', paramEndIndex) + 1:].strip()
                if len(key) > 0:
                    key = key[:key.find(' ')]
                    if key not in self.formatArgs:
                        self.logger.warn('Found unknown formatting variable "{name}"!'
                                         .format(name=key))
                        return text
                    elif self.formatArgs[key] is None:
                        return text
                    self.logger.verbose('Replacing variable "{name}" with " {value}"'
                                        .format(name=key, value=self.formatArgs[key]))
                    return text[:(indexes[0] - 1)] + self.formatArgs[key] + text[(indexes[1] - 1):]
        self.logger.warn('Found invalid formatting command: "{cmd}"'.format(cmd=text))
        return text

    def _fillFileTemplate(self, filePath):
        """_fillFileTemplate(filePath)
        Fill all default values in the provided file
        with their corresponding formatting arguments.
        """
        with open(filePath) as f:
            lines = f.readlines()
        with open(filePath, 'w') as f:
            for line in lines:
                f.write(self._fillVarInText(line))

    def fillTemplate(self, sdkPath):
        """>>> fillTemplate(sdkPath) -> success
        Fill all default values in the template
        with their corresponding formatting arguments.
        Also setts the sdk path of the template
        configuration to the provided one.
        """
        if self.formatArgs is None:
            self.logger.warn('No arguments specified to fill in the apk template. The app will be '
                             'generated using the default configuration! This is most likely not '
                             'what you want and the resulting apk must only be used for testing.')
            return True
        if not self.validateValues():
            return False
        if not (self.copyCustomManifestTemplate() and self.copyIcon()):
            return False
        for dirPath, dirNames, fileNames in os.walk(self.templateDir):
            if '.git' in dirNames:
                dirNames.remove('.git')
            files = [os.path.join(dirPath, filename) for filename in fileNames
                     if os.path.splitext(filename)[-1] in self.FORMAT_FILES_EXT]
            for filePath in files:
                self._fillFileTemplate(filePath)
        return self.createPropertiesFile(sdkPath) and self.changePackageName()

    def createPropertiesFile(self, sdkPath):
        """>>> createPropertiesFile(sdkPath):
        Create a local.properties file in the template
        and set the sdk path to the provided path.
        """
        with open(os.path.join(self.templateDir, 'local.properties'), 'w') as propertiesFile:
            sdkPath = sdkPath.replace('\\', '\\\\').replace(':', '\\:')
            propertiesFile.write('sdk.dir={path}'.format(path=sdkPath))
        return True
