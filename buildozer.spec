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

# (int) Android SDK version to use
android.sdk = 31

# (list) Permissions
android.permissions = INTERNET

# (str) python-for-android branch to use, defaults to master
p4a.branch = develop

# (str) Bootstrap to use (sdl2, webview, service_only, etc.)
p4a.bootstrap = sdl2

#
# OSX Specific
#
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
