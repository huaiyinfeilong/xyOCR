# coding=utf-8

from contentRecog import ContentRecognizer
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


# 图片内容识别基础类
class ImageRecognizer(ContentRecognizer):
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

	# 获取缩放因子
	def getResizeFactor(self, width, height):
		if width < 100 or height < 100:
			return 4
		return 1

	# 导航对象识别
	def recognize(self, pixels, imageInfo, onResult):
		width = imageInfo.recogWidth
		height = imageInfo.recogHeight
		image = Image.frombytes("RGBX", (width, height), pixels, "raw", "BGRX")
		image = image.convert("RGB")
		from io import BytesIO
		output = BytesIO()
		image.save(output, "jpeg")
		url = "http://8.130.94.216:6751/img_process_normal"
		data = []
		boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
		data.append("--" + boundary)
		data.append('Content-disposition: form-data; name="file"; filename="image.jpg"')
		data.append("")
		data.append(output.getvalue())
		data.append("--" + boundary + "--")
		data.append("")
		payload = b"\r\n".join(str(item).encode("utf-8") if isinstance(item, str) else item for item in data)
		headers = {
			"Content-type": f"multipart/form-data; boundary={boundary}"
		}
		response = self._http_request(url, headers, payload, "POST")
		ui.message(response.get("msg"))

	def cancel(self):
		# 什么也不做
		pass
