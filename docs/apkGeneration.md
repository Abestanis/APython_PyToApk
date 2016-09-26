# Generating an apk from your python sources
## What is an apk?
In short, files ending with `.apk` are archives with a special content that are recognized by and can be installed on the Android system.
More information can be found at [Wikipedia](https://en.wikipedia.org/wiki/Android_application_package)

## What is the apk command actually doing?
The apk command takes your Python sources and puts them into a [template application](https://github.com/Abestanis/APython_PyApp). This template is then modified with the provided configuration (see [Configure the apk generation](#configure-the-apk-generation)) and packed into an apk file.
The generated apk contains your Python sources and will be able to execute them on any Android system, provided that the [Python Host app](https://github.com/Abestanis/APython) or any app that provides a similar functionality is installed as well.

## Use the apk command
To pack your Python sources into an apk, you will just need to execute

```build.py apk --sourceDir path/to/your/Python/sources```.

If you created a `setup.cfg` in your source directory and configured it accordingly to the next section, the apk will be configured with the values provided and is ready to be installed.
The resulting apk is referred to as the `Python app`.
*Note that at this time only unsigned apks and apks signed with a debug key can be generated.*

You can customize the build by specifying additional command line arguments when executing the apk command. See 

```build.py apk --help```

for a list of all possible command line options and their description.

## Configure the apk generation
You need to configure the generated apk before you can release it. Otherwise your users might run into some problems when they try to install your app on their device:
For example, the `appId` value needs to be an id unique to your application (see the table below for more information). If this value is not specified, the default value of the template is used and your app will not be installable with an other Python app which made the same mistake.

To configure the apk, you need to create a `setup.cfg` file in your source directory with a section `android_app` that contains the properties you want to configure.
An [example `setup.cfg` can be found here](https://github.com/Abestanis/APython_PyToApk/blob/master/examplePythonProgram/setup.cfg).

This is a table of all available properties that can be changed, their name in the `setup.cfg` file and a description.

Property name | Name in setup.cfg | Description
------------- | ----------------- | -----------
appId | app_id | This specifies the java package name of your application. As such, it needs to be unique to your app and it needs to follow the syntax of a java package name. More information about Java package names and their **naming convention** can be found [here](https://docs.oracle.com/javase/tutorial/java/package/namingpkgs.html).
appName | app_name | This can be any string. It specifies the name of your application that is displayed to the user.
appLogTag | app_tag | This can be any string. It defines the tag of the log messages your app will produce. For more information about logging on android devices visit the [developer docs](https://developer.android.com/reference/android/util/Log.html).
appVersion | app_version | This can be any string, but it should look like a version. `1.0` is valid as well as `0.9-beta`. This version string will be displayed to the user. See the help for `versionName` at the [Android documentation](https://developer.android.com/studio/publish/versioning.html#appversioning).
appNumVersion | app_num_version | This needs to be a positive number (not 0). This number should increase every time you release a new version of your app. The android install system will use this to compute, if the apk you are trying to install is newer than an already installed apk. See the help for `versionCode` at the [Android documentation](https://developer.android.com/studio/publish/versioning.html#appversioning).
appTargetSdk | app_target_sdk | The targeted Android sdk version of your apk. This can be left to the template default for most apks. For information on sdk versions and their corresponding Android versions, look [here](https://developer.android.com/guide/topics/manifest/uses-sdk-element.html#ApiLevels).
appMinSdk | app_min_sdk | The minimum Android sdk version your apk should support. Android will prevent your app from being installed on any device running an older Android than the one specified. The Python app template and the Python host app support a minimal sdk level of 8, but if your app needs a SDL (or tkinter) window, you should set this value to 9, because sdk level 9 is required for SDL to work.
minPyVersion | min_python_version | The minimum python version needed to run your python code.
windowType | app_window_type | The window type your app will use. Supported window types are `NO_WINDOW`, `TERMINAL`, `SDL`, `WINDOW_MANAGER` and `ANDROID`. More information on those window types can be found [at the APython project](https://github.com/Abestanis/APython).
requirements | requirements | This lists all additional dependencies your python code will need to run. These requirements should be specified [in the syntax of a `requirements.txt` file](https://pip.readthedocs.io/en/1.1/requirements.html), e.g. `twisted requests>=1.2 bcrypt==1.0.2`
 | app_icon | Specifies the path to the icon your app should use. This path must either be absolute or relative to the source directory of your Python sources.
 | app_manifest_template | A path to a custom [`AndroidManifest.xml`](https://developer.android.com/guide/topics/manifest/manifest-intro.html) that should be used in the app template. This is usefull because the manifest provides a lot of information about your app to the Android system and the apk command might not be able to fill in all the information you want to be filled in.

### Use a custom template
If the Python app template does not fullfill your needs, you can create your own apk template and specify it to the apk command with the `--templateGit` commandline option (_--templateDir option is planned_).
In order to implement the communication to the Python host, have a look at the [Python app project](https://github.com/Abestanis/APython_PyApp), specifically at the [InterpreterHost class](https://github.com/Abestanis/APython_PyApp/blob/master/app/src/main/java/com.apython.python.apython_pyapp/InterpreterHost.java).
