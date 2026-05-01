[app]

# (str) Title of your application
title = Говорящий Глагол 3D

# (str) Package name
package.name = glagol3d

# (str) Package domain (needed for android/ios packaging)
package.domain = com.kiwi12643.glagol

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,obj,mtl,jpg,jpeg,txt,zip,wav,png

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy==2.1.0,pillow

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D

# (bool) Copy library instead of making big libpython.so
android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.arch = arm64-v8a

# (int) Target Android API, should be as high as possible.
android.api = 31

# (int) Minimum API your APK will support.
android.minapi = 21

# (int) Android NDK version to use
android.ndk = 23b

# (list) Permissions
android.permissions = INTERNET

# (str) python-for-android branch to use, defaults to master
p4a.branch = master

# (str) Bootstrap to use (sdl2, webview, service_only, etc.)
p4a.bootstrap = sdl2

# (list) Java classes to add as activities to the manifest
# android.add_activities = 

# (str) OU of the APK
# android.ou = 

# (str) The Android application category (e.g. Game, Communication)
# android.appcategory = Game

# (str) Which Gradle version to use (if using gradle build)
# android.gradle_version = 3.1.4

# (bool) Use AndroidX support library
android.use_androidx = True

# (bool) Enable Android App Bundle (AAB) for Play Store
# android.enable_aab = False

# (str) Android Gradle plugin version to use
# android.gradle_plugin_version = 3.2.0

# (int) Android Jetpack version
# android.jetpack_version = 1.0.0

# (str) AndroidX core version
# android.androidx_core_version = 1.3.2

# (str) AndroidX appcompat version
# android.androidx_appcompat_version = 1.2.0

# (list) Patterns to exclude from source
#source.exclude_patterns = license,images/*.jpg

# (list) List of activities android will integrate
#android.add_activities = 

# (str) Android manifest file to use (optional)
#android.manifest = 

# (bool) Skip the update of Android SDK
#android.skip_update = False

# (bool) Skip the easy configuration of the SDK
#android.skip_easyconfig = False

# (str) The path to an already existing fully-configured SDK
#android.sdk_path = 

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios

# (str) Name of the certificate to use for signing the debug version
#ios.codesign.debug = "iPhone Developer: <lastname> <firstname> (<hexstring>)"

# (str) Name of the certificate to use for signing the release version
#ios.codesign.release = %(ios.codesign.debug)s


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

#    -----------------------------------------------------------------------------
#    List as sections
#
#    You can define all the "list" as [section:key].
#    Each line will be considered as a option to the list.
#    Let's take [app] / source.exclude_patterns.
#    Instead of doing:
#
#[app]
#source.exclude_patterns = license,data/audio/*.wav
#
#    This can be translated into:
#
#[app:source.exclude_patterns]
#license
#data/audio/*.wav
