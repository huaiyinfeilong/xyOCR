# coding=utf-8

import threading
import globalPluginHandler
import scriptHandler
import addonHandler
import ui
import contentRecog
from contentRecog import recogUi
import api
from .paddleOcr import PaddleOcr

addonHandler.initTranslation()

# Translators: Script description
CATEGORY_NAME = _("Xinyi OCR")


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	ocr = PaddleOcr()
	thread = None

	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		if self.ocr is None:
			# Translators: Recognition failed
			ui.message(_("Recognition failed"))
			return
		if self.ocr is not None:
			self.ocr.initRecognizer()

	@scriptHandler.script(
		# Translators: Text recognition
		description=_("Text recognition"),
		category=CATEGORY_NAME,
		gesture="kb:NVDA+ALT+O"
	)
	def script_recognize_image(self, gesture):
		if self.ocr is None:
			# Translators: Recognition failed
			ui.message(_("Recognition failed"))
			return
#        if not self.thread or not self.thread.is_alive():
#            self.thread = threading.Thread(
#                target=recogUi.recognizeNavigatorObject,
#                kwargs={"recognizer": self.ocr})
#            self.thread.start()
		recogUi.recognizeNavigatorObject(self.ocr)

	@scriptHandler.script(
		# Translators: Clipboard recognition
		description=_("Clipboard recognition"),
		category=CATEGORY_NAME,
		gesture="kb:NVDA+SHIFT+ALT+O"
	)
	def script_recognize_clipboard(self, gesture):
		if not self.thread or not self.thread.is_alive():
			self.thread = threading.Thread(target=self.recognize_clipboard)
			self.thread.start()

	def recognize_clipboard(self):
		# Translators: Virtual document title: Recognition result
		if isinstance(api.getFocusObject(), recogUi.RecogResultNVDAObject):
			# Translators: Already in a content recognition result
			ui.message(_("Already in a content recognition result"))
			return
		# Translators: Recognizing
		ui.message(_("Recognizing"))
		self.ocr.recognize_clipboard(self.onRecognizeClipboardResult)

	def onRecognizeClipboardResult(self, result):
		if result is not None and result != []:
			result = [[{"x": 0, "y": 0, "width": 1, "height": 1, "text": item}] for item in result]
			image_info = contentRecog.RecogImageInfo(0, 0, 1, 1, 1)
			result = contentRecog.LinesWordsResult(result, image_info)
			result_obj = CustomRecogResultNVDAObject(result=result)
			result_obj.setFocus()

	def terminate(self):
		if self.ocr is not None:
			self.ocr.uninitRecognizer()
			self.ocr = None


class CustomRecogResultNVDAObject(recogUi.RecogResultNVDAObject):
	def script_activatePosition(self, gesture):
		# 屏蔽激活事件，因为剪贴板识别结果是只读的
		pass
