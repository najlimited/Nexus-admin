[app]

title = Nexus Admin
package.name = nexusadmin
package.domain = com.nexusadmin.app

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 1.0.0
requirements = python3,kivy==2.2.0,kivymd==1.1.1,pillow,requests,urllib3,certifi,chardet,idna

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,VIBRATE,WAKE_LOCK

android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.allow_backup = True
android.debug = True
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 0