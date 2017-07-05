import os, sys, subprocess
from time import sleep
from utils.argparser import SubCmdArgParser, InfoActionProcessed, ArgumentParserError
from utils.files import resolvePath

class ADBHandler(object):
    
    config = None
    adbPath = None
    apkPath = None
    emulatorPath = None
    emulator = None
    preferEmulator = False
    device = None
    
    def __init__(self, config):
        self.config = config
        self.readConfig()
    
    def verifyArguments(self):
        valid = True
        if self.config.sdkPath == None:
            self.config.logger.error('The path to the sdk directory was not specified!')
            valid = False
        else:
            self.adbPath = os.path.join(self.config.sdkPath, 'platform-tools',
                                        'adb.exe' if sys.platform == 'win32' else 'adb')
            self.emulatorPath = os.path.join(self.config.sdkPath, 'tools',
                                             'emulator.exe' if sys.platform == 'win32'
                                             else 'emulator')
            if not os.path.isfile(self.adbPath):
                self.config.logger.error('Failed to find the adb executable in ' +
                                         self.adbPath)
                valid = False
            if not os.path.isfile(self.emulatorPath):
                self.config.logger.error('Failed to find the emulator executable ' +
                                         'in ' + self.emulatorPath)
                valid = False
        if self.apkPath == None:
            self.apkPath = self.getNewestGeneratedApk()
        if self.apkPath == None:
            self.config.logger.error('The path to the app apk was not specified!')
            valid = False
        elif not os.path.isfile(self.apkPath):
            self.config.logger.error('The path to the app apk does not point to ' +
                                     'an existing file: ' + self.apkPath)
            valid = False
        return valid
    
    def readConfig(self):
        section = self.config.getSection('install')
        if section == None:
            self.config.logger.warn('Failed to read any config for the install ' +
                                    'command from the config file.')
            return
        if section.hasOption('emulator'):
            self.emulator = section.get('emulator')
        if not self.preferEmulator and section.hasOption('preferEmulator'):
            self.preferEmulator = section.getBoolean('preferEmulator')
        if section.hasOption('apkPath'):
            self.apkPath = section.get('apkPath', evaluatePath = True)
        if section.hasOption('device'):
            self.device = section.get('device')
    
    def parseCmdArgs(self, args):
        parser = SubCmdArgParser(prog='build.py install') # TODO: Description
        parser.add_argument('--emulator', help = 'The name of the emulator that ' +
                            'should be started, if no device is connected and no ' +
                            'emulator is running.')
        parser.add_argument('--device', help = 'If specified, the apk will be ' +
                            'installed on that exact device. The name must be ' +
                            'the exact name shown by "adb devices". If no ' +
                            'connected device / running emulator is found with ' +
                            'this name, but an emulator is specified via the ' +
                            '--emulator option, that emulator is started and ' +
                            'if its name matches the required name, it is used.')
        parser.add_argument('--apkPath', help = 'The path to the apk file of the ' +
                            'app that should be installed on the targeted device.')
        parser.add_argument('--preferEmulator', action = 'store_true',
                            default = self.preferEmulator,
                            help = 'If specified and --device is not specified, ' +
                            'the install command will prefer an emulator as the ' +
                            'installation target.')
        cmdArgs = parser.parse_args(args)
        if 'emulator' in cmdArgs and cmdArgs.emulator != None:
            self.emulator = cmdArgs.emulator
        if 'device' in cmdArgs and cmdArgs.device != None:
            self.device = cmdArgs.sourceDir
        if 'apkPath' in cmdArgs and cmdArgs.apkPath != None:
            self.apkPath = resolvePath(cmdArgs.apkPath, self.config.currDir)
        if 'preferEmulator' in cmdArgs and cmdArgs.preferEmulator != None:
            self.preferEmulator = cmdArgs.preferEmulator
    
    def getNewestGeneratedApk(self):
        apkOutputDir = os.path.join(self.config.outputDir, 'apk')
        if os.path.isdir(apkOutputDir):
            apkFiles = [os.path.join(apkOutputDir, apk) for apk in
                        os.listdir(apkOutputDir) if os.path.splitext(apk)[1] == '.apk']
            if len(apkFiles) > 0:
                newestApk = apkFiles[0]
                modTime = os.path.getmtime(newestApk)
                for apkFile in apkFiles[1:]:
                    apkModTime = os.path.getmtime(apkFile)
                    if apkModTime > modTime:
                        modTime = apkModTime
                        newestApk = apkFile
                return newestApk
        return None
    
    def getConnectedDevices(self):
        args = [self.adbPath, 'devices']
        self.config.logger.verbose('Calling ' + subprocess.list2cmdline(args))
        output = None
        try:
            output = subprocess.check_output(args)
        except subprocess.CalledProcessError as e:
            self.config.logger.error('Calling "' + subprocess.list2cmdline(args) +
                                     '" failed: ' + str(e))
            return None
        devices = []
        for line in output.split('\n'):
            content = line.split()
            if len(content) == 2:
                devices.append(content[0])
        return devices
    
    def startEmulator(self):
        if self.emulator == None:
            self.config.logger.error('No emulator to start was specified.')
            return None
        args = [self.emulatorPath, '-avd', self.emulator.replace(' ', '_')]
        self.config.logger.info('Starting emulator ' + self.emulator + '...')
        self.config.logger.verbose('Calling ' + subprocess.list2cmdline(args))
        emulatorProcess = subprocess.Popen(args, stdout = subprocess.PIPE)
        self.config.logger.info('Waiting for emulator ' + self.emulator + '...')
        for line in iter(emulatorProcess.stdout.readline,''):
            start = line.find('emulator-')
            end = start + len('emulator-')
            if start == -1 or len(line) < end: continue
            if line[end].isdigit():
                while len(line) > end and line[end].isdigit():
                    end += 1
                return line[start:end]
        self.config.logger.error('Failed to start emulator ' + self.emulator)
        return None
    
    def ensureDeviceOnline(self, device):
        self.config.logger.info('Waiting for device ' + device + ' to come online...')
        args = [self.adbPath, '-s', device, 'wait-for-device']
        self.config.logger.verbose('Calling ' + subprocess.list2cmdline(args))
        if not subprocess.call(args) == 0:
            self.config.logger.error('Failed to wait for online state of device ' +
                                     device)
            return False
        args = [self.adbPath, '-s', device, 'shell', 'getprop', 'sys.boot_completed']
        try:
            numTries = 0
            while subprocess.check_output(args)[0] != '1':
                sleep(1)
                numTries += 1
                if numTries > 3 * 60:
                    self.config.logger.error('Boot time out: Device ' + device +
                                             ' took too long to boot!')
                    return False
        except subprocess.CalledProcessError as e:
            self.config.logger.error('Failed to call "' + subprocess.list2cmdline(args) +
                                     '": ' + str(e))
            return False
        return True
    
    def install(self, cmdArgs):
        try:
            self.parseCmdArgs(cmdArgs)
        except InfoActionProcessed:
            return True
        except ArgumentParserError as e:
            return e.code == 0
        if not self.verifyArguments(): return False
        devices = self.getConnectedDevices()
        installTarget = None
        if devices == None:
            self.config.logger.error('Failed to detect connected devices!')
            return False
        if len(devices) == 0 or self.device != None and self.device not in devices:
            device = self.startEmulator()
            if device == None:
                return False
            elif self.device != None and device != self.device:
                self.config.logger.error('The device name of the started emulator ' +
                                         'is not the specified device name: ' +
                                         self.device)
                return False
            installTarget = device
        elif self.device != None:
            installTarget = self.device
        else:
            physicalDevices = [device for device in devices
                               if not device.startswith('emulator')]
            if len(physicalDevices) > 1:
                self.config.logger.error('Multiple devices are connected, but no ' +
                                         'device name was specified.')
                return False
            elif len(physicalDevices) == 1 and not (len(devices) == 2 and self.preferEmulator):
                installTarget = physicalDevices[0]
            else:
                if len(devices) - len(physicalDevices) > 1:
                    self.config.logger.error('Multiple emulators are started, but ' +
                                             'no device name was specified.')
                    return False
                installTarget = [device for device in devices
                                 if device not in physicalDevices][0]
        if not self.ensureDeviceOnline(installTarget): return False
        args = [self.adbPath, '-s', installTarget, 'install', '-rtd', self.apkPath]
        self.config.logger.info('Installing apk ' + self.apkPath + ' on device ' +
                         installTarget)
        self.config.logger.verbose('Calling ' + subprocess.list2cmdline(args))
        try:
            output = subprocess.check_output(args, universal_newlines = True)
            if 'Success' in output:
                self.config.logger.verbose(output)
                return True
            if 'Failure' in output:
                self.config.logger.error([line for line in output.split('\n')
                                          if 'Failure' in line][0])
            else:
                self.config.logger.error(output)
        except subprocess.CalledProcessError as e:
            self.config.logger.error('Command "' + subprocess.list2cmdline(args) +
                                     '" failed on device ' + installTarget + ': ' +
                                     str(e))
        self.config.logger.error('Failed to install apk ' + self.apkPath +
                                 ' on device ' + installTarget)
        return False

def run(config, cmdArgs):
    adbHandler = ADBHandler(config)
    return adbHandler.install(cmdArgs)
