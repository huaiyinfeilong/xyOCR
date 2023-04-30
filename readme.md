# Xinyi OCR

This is an NVDA OCR recognition add-on developed based on the PaddleOCR_json offline OCR component.

This add-on is currently only connected to the local OCR recognition engine of PaddleOCR_json, and the PaddleOCR_json component will be automatically installed after the add-on is installed. In the future, other offline and online OCR recognition engines will be gradually connected.

## Addon Advantages

* The recognition speed is fast, about 100ms, and the actual situation varies with the performance configuration of the computer.
* Strong recognition accuracy, comparable to online recognition.
* The coordinates of the recognition result text are accurate, and the click response of the result text is accurate.

## Keyboard Shortcuts

* Navigation object recognition: NVDA+ALT+O
* Clipboard recognition: NVDA+ALT+SHIFT+O

Shortcut key settings: You can set shortcut keys for each command under the "Xinyi OCR" category in the "Keys and Gestures" setting.

## Feedback Contact

Any comments and suggestions are welcome to communicate:

* Project address: https://github.com/huaiyinfeilong/xyocr
* E-mail: huaiyinfeilong@163.com
* QQ: 354522977
* WeChat: huaiyinfeilong

## Upgrade log

### Version 1.3

* Fix the problem that the version below NVDA 2023.1 cannot be installed.

### Version 1.2

* Added environment detection during installation, and will give a prompt that the installation cannot be completed for a non-64-bit system environment.
* Fixed the problem that PaddleOCR_json.exe would not exit automatically when NVDA exited abnormally, and continued to survive.
* Fix the problem that OCR recognition takes up too much memory as the number of recognitions increases.
* Fixed NVDA suspended animation problem during OCR recognition.

### Version 1.1

* Add clipboard recognition function, hotkey: NVDA+SHIFT+ALT+O
