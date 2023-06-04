# The PyToApk script
## About the APython project

The APython project enables the usage of Python programs on the Android platform in a more efficient way than current implementations.
A detailed description of this project can be found [here](https://github.com/Abestanis/APython#user-content-about-the-project).

## The PyToApk-Tool

This scipt automates many processes neccessary to bring your Python code to the Android platform.
For a list of possible commands and arguments type ```build.py -h``` or type ```build.py [command] -h``` to get a help message for the specified command.

### Generating an apk

To pack your Python sources into an apk, that is executable by the [Python host](https://github.com/Abestanis/APython#user-content-about-the-project) on the Android platform, run

`build.py apk --sourceDir path/to/your/Python/source/directory`.

If you wish to create a debug apk (signed with an debug key, [usable for testing, not for deployment](https://developer.android.com/studio/build/building-cmdline.html#DebugMode)), add the `--buildDebug` parameter. Generating an apk signed with a custom key is currently *not supported*.

You need to configure the generated apk file, see [Configure the apk generation](https://github.com/Abestanis/APython_PyToApk/blob/main/docs/apkGeneration.md#configure-the-apk-generation) for more information.

It is possible to install the generated apk by calling the install command after the apk command finishes, or you can supply the `--install` argument to the apk command. See the next section for more information about installing.

This command **requires** the Android sdk to be installed. See [Requirements](#requirements) for more information.

### Installing your apk

You can install your generated apk by executing

`build.py install --apkPath path/to/apk`.

If you omit the `--apkPath` option, the last output of the build command is used.

By default, the install command preferres physical devices over emulators. This behaviour can be changed with the `--preferEmulator` option. If multiple emulators or devices are present, you need to specify your targeted device/emulator with the `--device` option. You can also specify an emulator to start with the `--emulator` argument in case there is no device connected and no emulator running or the device specified by `--device` is not found. 

This command **requires** the Android sdk to be installed. See [Requirements](#requirements) for more information.

### Generating a Python module for Android

*Currently not implemented*

### Requirements

The apk command needs a path to an [Android SDK](https://www.droidwiki.de/wiki/Android_SDK) installation (either via command line (```--sdkPath```) or config file). If you have [Android Studio](https://developer.android.com/studio/index.html) installed, the SDK is most likely already installed on your system (you can find the path by navigating to `Settings > Appearance & Behaviour > System Settings > Android SDK` and looking at `Android SDK Location` in the panel), but it can also be downloaded and installed from the [SDK website](https://developer.android.com/studio/index.html) (scroll all the way down until you see `Get just the command line tools`).
