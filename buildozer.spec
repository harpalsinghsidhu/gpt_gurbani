[app]
presplash.filename = presplash.png
presplash.color = #FFFFFF
title = SGGS Paath Reader
icon.filename = icon.png
package.name = sggspaathreader
package.domain = org.paathreader
source.dir = .
source.include_exts = py,kv,ttf,db,csv,txt,png
version = 0.1.0
requirements = hostpython3==3.11.5,python3==3.11.5,kivy==2.3.0
orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
