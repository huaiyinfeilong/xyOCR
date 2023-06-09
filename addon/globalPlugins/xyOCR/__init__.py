# coding=utf-8

from logHandler import log
import threading
import globalPluginHandler
import scriptHandler
import addonHandler
import ui
import config
from contentRecog import recogUi
import api
import gui
import wx
from .paddleOcr import PaddleOcr
from .baiduOcr import BaiduGeneralOcr, BaiduAccurateOcr
from .util import is64ProcessorArchitecture
from .imageRecog import ImageRecognizer


addonHandler.initTranslation()


# 配置面板
class XinyiOcrSettingsPanel(gui.SettingsPanel):
	# Translators: Settings panel title
	title = _("Xinyi OCR")

	def makeSettings(self, sizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)
		# Translators: The label for using share key checkbox
		using_share_key_label = _("Using share key")
		self.usingShareKeyCheckBox = helper.addItem(
			wx.CheckBox(self, label=_(using_share_key_label))
		)
		self.usingShareKeyCheckBox.SetValue(config.conf["xinyiOcr"]["baidu"]["usingShareKey"])
		# Translators: The label for my APP key textbox
		my_app_key_label = _("My app key")
		self.myAppKeyTextCtrl = helper.addLabeledControl(
			_(my_app_key_label),
			wx.TextCtrl,
		)
		self.myAppKeyTextCtrl.SetValue(config.conf["xinyiOcr"]["baidu"]["myAppKey"])
		# Translators: The label for my APP secret textbox
		my_app_secret_label = _("My app secret")
		self.myAppSecretTextCtrl = helper.addLabeledControl(
			_(my_app_secret_label),
			wx.TextCtrl,
		)
		self.myAppSecretTextCtrl.SetValue(config.conf["xinyiOcr"]["baidu"]["myAppSecret"])

	def onSave(self):
		# 保存配置
		config.conf["xinyiOcr"]["baidu"]["usingShareKey"] = self.usingShareKeyCheckBox.IsChecked()
		config.conf["xinyiOcr"]["baidu"]["myAppKey"] = self.myAppKeyTextCtrl.GetValue()
		config.conf["xinyiOcr"]["baidu"]["myAppSecret"] = self.myAppSecretTextCtrl.GetValue()


# Translators: Script description
CATEGORY_NAME = _("Xinyi OCR")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	imageRecognizer = ImageRecognizer()
	ocr_list = []
	ocr = None
	thread = None

	# 检测穆连平是否开启
	def isScreenCurtainRunning(self):
		import vision
		from visionEnhancementProviders.screenCurtain import ScreenCurtainProvider
		screen_curtain_provider_info = vision.handler.getProviderInfo(
			ScreenCurtainProvider.getSettings().getId()
		)
		return bool(vision.handler.getProviderInstance(screen_curtain_provider_info))

	# 插件初始化
	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		# 初始化配置
		confspec = {
			"engine": "integer(default=0)",
			"baidu": {
				"usingShareKey": "boolean(default=True)",
				"shareAppKey": "string(default='QQbo1PCfCxh51snrOw0xVpzp')",
				"shareAppSecret": "string(default='91CTiEsiET4KKN5LrhT6MGS3fCjGSkS1')",
				"myAppKey": "string(default='')",
				"myAppSecret": "string(default='')"
			}
		}
		config.conf.spec["xinyiOcr"] = confspec
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(XinyiOcrSettingsPanel)
		try:
			if is64ProcessorArchitecture():
				self.ocr_list.append(PaddleOcr())
			self.ocr_list.append(BaiduGeneralOcr())
			self.ocr_list.append(BaiduAccurateOcr())
			for ocr in self.ocr_list:
				try:
					ocr.initRecognizer()
				except Exception as e:
					# 初始化引擎失败，从引擎列表中移除有问题的引擎，并继续初始化后续引擎
					log.debug(f"初始化OCR引擎失败：{e}")
					self.ocr_list.remove(ocr)
					continue
			# 配置文件中的引擎索引若大于实际索引范围，则设置引擎索引为0，这种超出情况可能出现于拷贝用户配置到另一台不支持x64环境的机器中运行
			index = config.conf["xinyiOcr"]["engine"] \
			if config.conf["xinyiOcr"]["engine"] < len(self.ocr_list) else 0
			self.ocr = self.ocr_list[index]
		except Exception as e:
			log.debug(f"初始化失败：\n{e}")
			self.ocr = None

	@scriptHandler.script(
		# Translators: Choose OCR engine
		description=_("Switch OCR engine"),
		category=CATEGORY_NAME,
		gesture="kb:NVDA+ALT+9"
	)
	def script_switchOcr(self, gesture):
		if self.ocr is None:
			return
		count = len(self.ocr_list)
		current_ocr_name = self.ocr.name
		# 获取当前OCR对象在列表中的索引下标
		index = [ocr.name for ocr in self.ocr_list].index(current_ocr_name)
		index = (index + count + 1) % count
		config.conf["xinyiOcr"]["engine"] = index
		self.ocr = self.ocr_list[index]
		current_ocr_name = self.ocr.name
		ui.message(_(current_ocr_name))

	@scriptHandler.script(
		# Translators: Text recognition
		description=_("Text recognition"),
		category=CATEGORY_NAME,
		gesture="kb:NVDA+ALT+O"
	)
	def script_recognize_image(self, gesture):
		if self.ocr is None:
			log.error("没有可用的OCR引擎。")
			# Translators: Recognition failed
			ui.message(_("Recognition failed"))
			return
		if self.isScreenCurtainRunning():
			# Translators: Please turn off the screen curtain before recognition
			log.debug("幕帘屏处于开启状态，无法进行识别。")
			ui.message(_("Please turn off the screen curtain before recognition"))
			return
		try:
			recogUi.recognizeNavigatorObject(self.ocr)
		except Exception as e:
			log.error(f"识别失败：\n{e}")
			ui.message(_("Recognition failed"))

	@scriptHandler.script(
		# Translators: Clipboard recognition
		description=_("Clipboard recognition"),
		category=CATEGORY_NAME,
		gesture="kb:NVDA+SHIFT+ALT+O"
	)
	def script_recognize_clipboard(self, gesture):
		if self.ocr is None:
			return
		if not self.thread or not self.thread.is_alive():
			self.thread = threading.Thread(target=self.recognize_clipboard)
			self.thread.start()

	def recognize_clipboard(self):
		if isinstance(api.getFocusObject(), recogUi.RecogResultNVDAObject):
			# Translators: Already in a content recognition result
			ui.message(_("Already in a content recognition result"))
			return
		# Translators: Recognizing
		ui.message(_("Recognizing"))
		self.ocr.recognize_clipboard(self.onRecognizeClipboardResult)

	def onRecognizeClipboardResult(self, result):
		if not result:
			ui.message(_("Recognition failed"))
			return
		result_obj = CustomRecogResultNVDAObject(result=result)
		result_obj.setFocus()

	def terminate(self):
		if self.ocr is not None:
			self.ocr.uninitRecognizer()
			self.ocr = None

	@scriptHandler.script(
		# Translators: Image description
		description=_("Image description"),
		category=CATEGORY_NAME,
		gesture="kb:NVDA+ALT+P"
	)
	def script_imageRecognize(self, gesture):
		if self.isScreenCurtainRunning():
			# Translators: Please turn off the screen curtain before recognition
			log.debug("幕帘屏处于开启状态，无法进行识别。")
			ui.message(_("Please turn off the screen curtain before recognition"))
			return
		recogUi.recognizeNavigatorObject(self.imageRecognizer)

	@scriptHandler.script(
		# Translators: Clipboard image description
		description=_("Clipboard image description"),
		category=CATEGORY_NAME,
		gesture="kb:NVDA+ALT+SHIFT+P"
	)
	def script_clipboardImageRecognize(self, gesture):
		if isinstance(api.getFocusObject(), recogUi.RecogResultNVDAObject):
			# Translators: Already in a content recognition result
			ui.message(_("Already in a content recognition result"))
			return
		# Translators: Recognizing
		ui.message(_("Recognizing"))
		self.imageRecognizer.recognize_clipboard()


class CustomRecogResultNVDAObject(recogUi.RecogResultNVDAObject):
	def script_activatePosition(self, gesture):
		# 屏蔽激活事件，因为剪贴板识别结果是只读的
		pass
