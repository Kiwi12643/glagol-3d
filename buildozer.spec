[app]
title = Говорящий Глагол 3D
package.name = glagol3d
package.domain = com.youboss.glagol
source.dir = .
source.include_exts = py,obj,mtl,jpg,jpeg,txt,zip,wav,png
requirements = python3,kivy==2.1.0,pillow
orientation = portrait
fullscreen = 1
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,RECORD_AUDIO
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.arch = arm64-v8a
p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1