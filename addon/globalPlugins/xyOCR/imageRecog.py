# coding=utf-8

from contentRecog import ContentRecognizer
from . import helper
import urllib.request
import urllib.parse
import json
import os
import sys
sys.path.insert(0, "\\".join(os.path.dirname(__file__).split("\\")[:-1]) + "\\_py3_contrib")
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageGrab
import ui
import base64
import threading


# 图片内容识别基础类
class ImageRecognizer(ContentRecognizer):
	# 图片识别线程对象
	thread = None

	# 网络请求封装
	def _http_request(self, url=None, headers=None, payload=None, method=None):
		if not url or not method:
			return
		# 不使用代理
		proxy = urllib.request.ProxyHandler({})
		opener = urllib.request.build_opener(proxy)
		# 构建Request请求对象
		request = urllib.request.Request(url=url, headers=headers, data=payload, method=method)
		return json.loads(opener.open(request).read())

	def _getImageDescription(self, image):
		url = "http://8.130.94.216:6751/img_process_normal"
		data = []
		boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
		data.append("--" + boundary)
		data.append('Content-disposition: form-data; name="file"; filename="image.png"')
		data.append("")
		data.append(image)
		data.append("--" + boundary + "--")
		data.append("")
		payload = b"\r\n".join(str(item).encode("utf-8") if isinstance(item, str) else item for item in data)
		headers = {
			"Content-type": f"multipart/form-data; boundary={boundary}"
		}
		response = self._http_request(url, headers, payload, "POST")
		return response.get("msg")

	# 获取缩放因子
	def getResizeFactor(self, width, height):
		if width < 100 or height < 100:
			return 4
		return 1

	# 导航对象图片内容识别
	def recognize(self, pixels, imageInfo, onResult):
		# 如果有识别任务正在进行则返回
		if self.thread and self.thread.is_alive():
			return
		self.thread = threading.Thread(target=self._recognize, kwargs={
			"pixels": pixels,
			"imageInfo": imageInfo,
			"onResult": onResult
		})
		self.thread.start()

	# 导航对象图片识别线程
	def _recognize(self, pixels, imageInfo, onResult):
		width = imageInfo.recogWidth
		height = imageInfo.recogHeight
		image = Image.frombytes("RGBX", (width, height), pixels, "raw", "BGRX")
		image = image.convert("RGB")
		from io import BytesIO
		output = BytesIO()
		image.save(output, "png")
		result = self._getImageDescription(output.getvalue())
		ui.message(result)

	# 剪贴板图片内容识别
	def recognize_clipboard(self):
		# 如果有识别任务正在进行则返回
		if self.thread and self.thread.is_alive():
			return
		self.thread = threading.Thread(target=self._recognize_clipboard)
		self.thread.start()

	# 剪贴板图片内容识别线程
	def _recognize_clipboard(self):
		image = ImageGrab.grabclipboard()
		if not isinstance(image, Image.Image):
			# 剪贴板中不是图片，判断是否图片文件
			file_list = helper.get_clipboard_image_path()
			if file_list != [] and len(file_list) == 1:
				try:
					image = Image.open(file_list[0])
				except IOError:
					image = None
			else:
				# 如果剪贴板中超过了1个图片文件
				image = None
		if not image:
			# 剪贴板中既不是图片内容也不是图片文件
			ui.message(_("Recognition failed"))
			return
		from io import BytesIO
		output = BytesIO()
		image.save(output, "png")
		result = self._getImageDescription(output.getvalue())
		ui.message(result)

	def cancel(self):
		# 什么也不做
		pass
