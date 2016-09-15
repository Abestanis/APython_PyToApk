# The PyToApk script
## About the APython project

The APython project enables the usage of Python programs on the Android platform in a more efficient way than current implementations.
A detailed description of this project can be found [here](https://github.com/Abestanis/APython#user-content-about-the-project).

## The PyToApk-Tool

This scipt automates many processes neccessary to bring your Python code to the Android platform.
For a list of possible commands and arguments type ```build.py -h``` or type ```build.py [command] -h``` to get a help message for the specified command.

### Generating an apk

To pack your Python sources into an apk, that is executable by the [Python host](https://github.com/Abestanis/APython#user-content-about-the-project) on the Android platform, run

```build.py apk --sourceDir path/to/your/Python/source/directory```.

If you wish to create a debug apk (signed with an debug key, [usable for testing, not for deployment](https://developer.android.com/studio/build/building-cmdline.html#DebugMode)), add the ```--buildDebug``` parameter. Generating an apk signed with a custom key is currently *not supported*.

It is currently *not supported* to configure the generated apk file, but this will be possible with values in a [setup.cfg](examplePythonProgram/setup.cfg) file.

The apk command needs a path to an [Android SDK](https://www.droidwiki.de/wiki/Android_SDK) installation (either via command line (```--sdkPath```) or config file). If you have [Android Studio](https://developer.android.com/studio/index.html) installed, the SDK is most likely already installed on your system (you can find the path by navigating to `Settings > Appearance & Behaviour > System Settings > Android SDK` and looking at `Android SDK Location` in the panel), but it can also be downloaded and installed from the [SDK website](https://developer.android.com/studio/index.html) (scroll all the way down until you see `Get just the command line tools`).

### Generating a Python module for Android

*Currently not implemented*
