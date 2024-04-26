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
from sparkImageRecog import SparkImageRecognizer


addonHandler.initTranslation()


# 配置面板
class XinyiOcrSettingsPanel(gui.settingsDialogs.SettingsPanel):
	# Translators: Settings panel title
	title = _("Xinyi OCR")

	def makeSettings(self, sizer):
		helper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)
		# Translators: the label for groupbox of Baidu OCR
		ocrGroupLabel = _("Baidu OCR")
		ocrGroupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, ocrGroupLabel)
		ocrGroupBox = ocrGroupSizer.GetStaticBox()
		ocrGroup = gui.guiHelper.BoxSizerHelper(ocrGroupBox, sizer=ocrGroupSizer)
		helper.addItem(ocrGroup)
		# Translators: The label for using share key checkbox
		usingOcrShareKeyLabel = _("Using share key")
		self.usingOcrShareKeyCheckBox = ocrGroup.addItem(
			wx.CheckBox(ocrGroupBox, label=_(usingOcrShareKeyLabel))
		)
		self.usingOcrShareKeyCheckBox.SetValue(config.conf["xinyiOcr"]["OCR"]["baidu"]["usingShareKey"])
		# Translators: The label for my APP key textbox
		myOcrAppKeyLabel = _("My app key")
		self.myOcrAppKeyTextCtrl = ocrGroup.addLabeledControl(
			_(myOcrAppKeyLabel),
			wx.TextCtrl,
		)
		self.myOcrAppKeyTextCtrl.SetValue(config.conf["xinyiOcr"]["OCR"]["baidu"]["myAppKey"])
		# Translators: The label for my APP secret textbox
		myOcrAppSecretLabel = _("My app secret")
		self.myOcrAppSecretTextCtrl = ocrGroup.addLabeledControl(
			_(myOcrAppSecretLabel),
			wx.TextCtrl,
		)
		self.myOcrAppSecretTextCtrl.SetValue(config.conf["xinyiOcr"]["OCR"]["baidu"]["myAppSecret"])
		# Translators: Periodically refresh recognized content
		autoOcrRefreshLabel = _("Periodically refresh recognized content")
		self.autoOcrRefreshCheckBox = ocrGroup.addItem(
			wx.CheckBox(ocrGroupBox, label=_(autoOcrRefreshLabel))
		)
		self.autoOcrRefreshCheckBox.SetValue(config.conf["xinyiOcr"]["OCR"]["autoRefresh"])
		# Translators: the label for groupbox of image description generation
		idgGroupLabel = _("Ifly image understanding")
		idgGroupSizer = wx.StaticBoxSizer(wx.HORIZONTAL, self, idgGroupLabel)
		idgGroupBox = idgGroupSizer.GetStaticBox()
		idgGroup = gui.guiHelper.BoxSizerHelper(idgGroupBox, sizer=idgGroupSizer)
		helper.addItem(idgGroup)
		# Translators: The label for APP ID textbox
		myIdgAppIdLabel = _("My APP ID")
		self.myIdgAppIdTextCtrl = idgGroup.addLabeledControl(
			_(myIdgAppIdLabel),
			wx.TextCtrl,
		)
		self.myIdgAppIdTextCtrl.SetValue(config.conf["xinyiOcr"]["IDG"]["spark"]["appId"])
		# Translators: The label for API secret textbox
		myIdgApiSecretLabel = _("My API secret")
		self.myIdgApiSecretTextCtrl = idgGroup.addLabeledControl(
			_(myIdgApiSecretLabel),
			wx.TextCtrl,
		)
		self.myIdgApiSecretTextCtrl.SetValue(config.conf["xinyiOcr"]["IDG"]["spark"]["apiSecret"])
		# Translators: The label for API key textbox
		myIdgApiKeyLabel = _("My API key")
		self.myIdgApiKeyTextCtrl = idgGroup.addLabeledControl(
			_(myIdgApiKeyLabel),
			wx.TextCtrl,
		)
		self.myIdgApiKeyTextCtrl.SetValue(config.conf["xinyiOcr"]["IDG"]["spark"]["apiKey"])

	def onSave(self):
		# 保存配置
		config.conf["xinyiOcr"]["OCR"]["baidu"]["usingShareKey"] = self.usingOcrShareKeyCheckBox.IsChecked()
		config.conf["xinyiOcr"]["OCR"]["baidu"]["myAppKey"] = self.myOcrAppKeyTextCtrl.GetValue()
		config.conf["xinyiOcr"]["OCR"]["baidu"]["myAppSecret"] = self.myOcrAppSecretTextCtrl.GetValue()
		config.conf["xinyiOcr"]["OCR"]["autoRefresh"] = self.autoOcrRefreshCheckBox.IsChecked()
		config.conf["xinyiOcr"]["IDG"]["spark"]["appId"] = self.myIdgAppIdTextCtrl.GetValue()
		config.conf["xinyiOcr"]["IDG"]["spark"]["apiSecret"] = self.myIdgApiSecretTextCtrl.GetValue()
		config.conf["xinyiOcr"]["IDG"]["spark"]["apiKey"] = self.myIdgApiKeyTextCtrl.GetValue()

# Translators: Script description
CATEGORY_NAME = _("Xinyi OCR")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	imageRecognizer = SparkImageRecognizer()
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
			"OCR": {
				"engine": "integer(default=0)",
				"baidu": {
					"usingShareKey": "boolean(default=True)",
					"shareAppKey": "string(default='QQbo1PCfCxh51snrOw0xVpzp')",
					"shareAppSecret": "string(default='91CTiEsiET4KKN5LrhT6MGS3fCjGSkS1')",
					"myAppKey": "string(default='')",
					"myAppSecret": "string(default='')"
				},
				"autoRefresh": "boolean(default=False)"
			},
			"IDG": {
				"engine": "integer(default=0)",
				"spark": {
				"appId": "string(default='')",
				"apiSecret": "string(default='')",
				"apiKey": "string(default='')"
			},
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
			index = config.conf["xinyiOcr"]["OCR"]["engine"] \
			if config.conf["xinyiOcr"]["OCR"]["engine"] < len(self.ocr_list) else 0
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
		config.conf["xinyiOcr"]["OCR"]["engine"] = index
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
			self.ocr.allowAutoRefresh = True
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
			self.ocr.allowAutoRefresh = False
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
