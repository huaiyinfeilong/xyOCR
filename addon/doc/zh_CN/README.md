# 新翼OCR

这是基于PaddleOCR_json离线OCR组件而开发的一个NVDA OCR识别插件。

本插件目前仅接入PaddleOCR_json的本地OCR识别引擎，安装插件后会自动安装PaddleOCR_json组件。后续会逐步接入其他离线、在线OCR识别引擎。

## 插件优点

* 识别速度快，大约100ms左右，实际情况因计算机性能配置而异。
* 强悍的识别准确度，媲美在线识别。
* 识别结果文字坐标精准，结果文字点击响应准确。

## 键盘快捷键

* 导航对象识别：NVDA+ALT+O
* 剪贴板识别：NVDA+ALT+SHIFT+O

快捷键设置：可在“按键与手势”设置中针对“新翼OCR”分类下各命令设置快捷键。

## 反馈联络

有任何意见建议欢迎沟通：

* 项目地址：https://github.com/huaiyinfeilong/xyocr
* 电子邮箱：huaiyinfeilong@163.com
* QQ：354522977
* 微信：huaiyinfeilong

## 升级日志

### Version 1.3

* 修复在NVDA2023.1以下版本无法安装的问题。

### Version 1.2

* 新增安装时环境检测，对于非64位系统环境给出无法完成安装提示。
* 修复当NVDA异常退出后，PaddleOCR_json.exe不会自动退出，继续存活的问题。
* 修复OCR识别随着识别次数增加而占用内存过大的问题。
* 修复OCR识别过程中NVDA假死问题。

### Version 1.1

* 增加剪贴板识别功能，热键：NVDA+SHIFT+ALT+O
