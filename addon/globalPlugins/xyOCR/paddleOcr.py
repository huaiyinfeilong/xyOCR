# coding=utf-8

import os
import sys
import threading
import tempfile
import ui
import winKernel
from contentRecog import ContentRecognizer, LinesWordsResult, RecogImageInfo
import addonHandler
from .PPOCR_api import PPOCR
from ctypes import wintypes
sys.path.append("\\".join(os.path.dirname(__file__).split("\\")[:-1]) + "\\_py3_contrib")
from PIL import Image


addonHandler.initTranslation()

# PaddleOCR-json.exe path
MODEL_ENGINE = os.path.abspath(
	os.path.join(
		os.path.dirname(__file__),
		"..",
		"models",
		"PaddleOCR-json",
		"PaddleOCR_json.exe"
	)
)


class PaddleOcr(ContentRecognizer):
	# Translators: Offline OCR
	name = _("Offline OCR")
	onResult = None
	ocr = None
	mutex = None
	# OCR counter
	counter = 0

	def __init__(self, *args, **kwargs):
		super(ContentRecognizer, self).__init__(*args, **kwargs)
		self._thread = None

	def getResizeFactor(self, width, height):
		if width < 100 or height < 100:
			return 4
		return 1

	def initRecognizer(self):
		self.onResult = None
		# Initialize OCR counter
		self.counter = 0
		# Create a mutex object for PaddleOCR_json.exe
		self.mutex = winKernel.kernel32.CreateMutexA(
			wintypes.DWORD(0),
			wintypes.BOOL(True),
			wintypes.LPSTR(bytes("{EFB13F9C-E93B-4135-A31C-F15E3DED8640}".encode("utf-8")))
		)
		# Initialize the PaddleOCR engine
		if self.ocr is None:
			self.ocr = PPOCR(MODEL_ENGINE)

	def uninitRecognizer(self):
		if self.ocr is not None:
			self.ocr.stop()
			self.ocr = None
		if self.mutex is not None:
			winKernel.kernel32.CloseHandle(wintypes.HANDLE(self.mutex))
			self.mutex = None

	def recognize(self, pixels, image_info, on_result):
		if self._thread is None or not self._thread.is_alive():
			self._thread = threading.Thread(
				target=self._recognize,
				kwargs={"pixels": pixels, "image_info": image_info, "on_result": on_result}
			)
			self._thread.start()

	def _recognize(self, pixels, image_info, on_result):
		self.onResult = on_result
		# Create a temporary file of BMP image
		f = tempfile.TemporaryFile(suffix=".bmp")
		image_filename = f.name
		f.close()
		width = image_info.recogWidth
		height = image_info.recogHeight
		image = Image.frombytes("RGBX", (width, height), pixels, "raw", "BGRX")
		image = image.convert("RGB")
		image.save(image_filename)
		# Recognize image files
		res = self.ocr.run(image_filename)
		# The code=100 success
		if res["code"] != 100:
			# Translators: Recognition failed
			ui.message(_("Recognition failed"))
			return
		data = res["data"]
		# Convert recognition result data to LWR
		lines = list()
		for item in data:
			box = item["box"]
			text = item["text"]
			word = {
				"x": box[0][0],
				"y": box[0][1],
				"width": box[1][0] - box[0][0],
				"height": box[2][1] - box[0][1],
				"text": text}
			words = list()
			words.append(word)
			lines.append(words)
		result = LinesWordsResult(lines, image_info)
		if self.onResult:
			self.onResult(result)
		self.auto_restart()

	def recognize_clipboard(self, on_result):
		if self._thread is None or not self._thread.is_alive():
			self._thread = threading.Thread(target=self._recognize_clipboard, kwargs={"on_result": on_result})
			self._thread.start()

	def _recognize_clipboard(self, on_result):
		self.onResult = on_result
		res = self.ocr.runClipboard()
		# The code=100 success
		if res.get("code") != 100:
			# Translators: Recognition failed
			ui.message(_("Recognition failed"))
			return
		data = res.get("data")
		result = [item.get("text") for item in data]
		result = [[{"x": 0, "y": 0, "width": 1, "height": 1, "text": item}] for item in result]
		image_info = RecogImageInfo(0, 0, 1, 1, 1)
		result = LinesWordsResult(result, image_info)
		if self.onResult is not None:
			self.onResult(result)
		self.auto_restart()

	def cancel(self):
		if self.onResult is not None:
			self.onResult = None

	def auto_restart(self):
		self.counter += 1
		if self.counter >= 5:
			self.uninitRecognizer()
			self.initRecognizer()
