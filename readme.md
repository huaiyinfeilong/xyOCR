# Xinyi OCR

This is an NVDA addon that provides offline and online OCR recognition. Offline recognition is developed based on the PaddleOCR_json component.

This add-on currently provides PaddleOCR_json's offline OCR recognition engine and the online Baidu general version and accurate version of the recognition engine. After installing the add-on, the PaddleOCR_json component will be automatically installed. More other offline and online OCR recognition engines will be gradually connected in the future.

In addition, this plugin also provides image description function, which can identify image content.

## Addon Advantages

* The recognition speed is fast, and the offline recognition is about 100ms. The actual situation varies with the performance configuration of the computer.
* Powerful offline recognition accuracy, comparable to online recognition.
* The coordinates of the recognition result text are accurate, and the click response of the result text is accurate.

## Keyboard Shortcuts

* Navigation object OCR recognition: NVDA+ALT+O
* Clipboard OCR recognition: NVDA+ALT+SHIFT+O
* Switch OCR recognition engine: NVDA+ALT+9
* Image description: NVDA+ALT+P
* Clipboard image description: NVDA+ALT+SHIFT+P

Shortcut key settings: You can set shortcut keys for each command under the "Xinyi OCR" category in the "Keys and Gestures" setting.

## Feedback Contact

Any comments and suggestions are welcome to communicate:

* Project address: https://github.com/huaiyinfeilong/xyocr
* E-mail: huaiyinfeilong@163.com
* QQ: 354522977
* WeChat: huaiyinfeilong

## Upgrade log

### Version 3.0.1

* New image description black screen detection function: If the image description operation is performed while the Mu Lianping function is on, a prompt will be given.

### Version 3.0

* Add image content recognition function, which can identify and describe the images browsed and the images in the clipboard.

### Version 2.0.2

*Fix the issue where online OCR may also be unavailable on machines where offline OCR is not available.

### Version 2.0.1

* Fix instability in network proxy environment.

### Version 2.0

* Added Baidu online OCR recognition engine, supports general recognition and accurate version recognition, and can use shared key and own private key. If you use your own private key, you need to configure it in the settings.
* Added screen curtain detection function, if OCR recognition is performed when the screen curtain is turned on, a prompt will be given.
* Remove the 64-bit system detection during installation, but after the non-64-bit system is installed, only online OCR recognition can be used and offline recognition cannot be used.

### Version 1.3

* Fix the problem that the version below NVDA 2023.1 cannot be installed.

### Version 1.2

* Added environment detection during installation, and will give a prompt that the installation cannot be completed for a non-64-bit system environment.
* Fixed the problem that PaddleOCR_json.exe would not exit automatically when NVDA exited abnormally, and continued to survive.
* Fix the problem that OCR recognition takes up too much memory as the number of recognitions increases.
* Fixed NVDA suspended animation problem during OCR recognition.

### Version 1.1

* Add clipboard recognition function, hotkey: NVDA+SHIFT+ALT+O
