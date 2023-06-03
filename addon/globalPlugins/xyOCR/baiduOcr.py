# coding=utf-8

from logHandler import log
import threading
import ui
import config
from contentRecog import LinesWordsResult, RecogImageInfo
import addonHandler
import urllib.request
import urllib.parse
import json
import base64
from . import ocr
from . import helper
import os
import sys
sys.path.insert(0, "\\".join(os.path.dirname(__file__).split("\\")[:-1]) + "\\_py3_contrib")
sys.path.insert(0, os.path.dirname(__file__))
from PIL import Image, ImageGrab


addonHandler.initTranslation()

# 百度在线识别引擎
class BaiduOcr(ocr.Ocr):
	_app_key = ""
	_app_secret = ""
	_access_token = ""
	_thread = None

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

	# 获取access_token
	def _fetch_access_token(self):
		self._access_token = ""
		# 获取app key和app secret
		self._app_key = config.conf["xinyiOcr"]["baidu"]["shareAppKey"] \
		if config.conf["xinyiOcr"]["baidu"]["usingShareKey"] else config.conf["xinyiOcr"]["baidu"]["myAppKey"]
		self._app_secret = config.conf["xinyiOcr"]["baidu"]["shareAppSecret"] \
		if config.conf["xinyiOcr"]["baidu"]["usingShareKey"] else config.conf["xinyiOcr"]["baidu"]["myAppSecret"]
		# 获取access_token的URL
		url = "https://aip.baidubce.com/oauth/2.0/token" \
		"?grant_type=client_credentials" \
		"&client_id={0}" \
		"&client_secret={1}" \
		.format(
			self._app_key,
			self._app_secret
		)
		headers = {
			"Content-type": "application/json;charset=utf-8",
			"Accept": "application/json"
		}
		try:
			response = self._http_request(url=url, headers=headers, method="POST")
		except Exception as e:
			log.error(f"获取access_token失败：\n{e}")
			if str(e) == "HTTP Error 401: Unauthorized":
				# Translators: Message: the app key or app secret is incorrect.
				ui.message(_("The app key or app secret is incorrect."))
				return
		if response:
			self._access_token = response.get("access_token")

	# 获取缩放因子
	def getResizeFactor(self, width, height):
		if width < 100 or height < 100:
			return 4
		return 1

	# 初始化识别引擎
	def initRecognizer(self):
		pass

	# 逆初始化识别引擎
	def uninitRecognizer(self):
		pass

	# 导航对象识别
	def recognize(self, pixels, image_info, on_result):
		width = image_info.recogWidth
		height = image_info.recogHeight
		image = Image.frombytes("RGBX", (width, height), pixels, "raw", "BGRX")
		image = image.convert("RGB")
		from io import BytesIO
		output = BytesIO()
		image.save(output, format="png")
	# 启动识别线程
		log.debug("启动导航对象识别线程。")
		if not self._thread or not self._thread.is_alive():
			log.debug("准备启动识别线程。")
			self._thread = threading.Thread(
				target=self._recognize,
				kwargs={
					"pixels": output.getvalue(),
					"image_info": image_info,
					"on_result": on_result
				}
			)
			self._thread.start()

		# 剪贴板识别
	def recognize_clipboard(self, on_result):
		log.debug("剪贴板识别启动。")
		image = ImageGrab.grabclipboard()
		if not isinstance(image, Image.Image):
			# 剪贴板中不是图片，判断是否图片文件
			log.debug("剪贴板中不是图片内容，尝试判断是否图片文件。")
			file_list = helper.get_clipboard_image_path()
			if file_list != [] and len(file_list) == 1:
				log.debug("剪贴板中为图片文件。")
				try:
					image = Image.open(file_list[0])
				except IOError:
					image = None
			else:
				# 如果剪贴板中超过了1个图片文件
				log.debug("剪贴板中有多个图片文件。")
				image = None
		if not image:
			# 剪贴板中既不是图片内容也不是图片文件
			log.debug("剪贴板中既不是图片内容也不是图片文件。")
			ui.message(_("Recognition failed"))
			return
		log.debug("获取剪贴板图片成功。")
		from io import BytesIO
		output = BytesIO()
		image.save(output, format="png")
		width = image.width
		height = image.height
		image_info = RecogImageInfo(0, 0, width, height, self.getResizeFactor(width, height))
		if not self._thread or not self._thread.is_alive():
			log.debug("准备启动识别线程。")
			self._thread = threading.Thread(
				target=self._recognize,
				kwargs={
					"pixels": output.getvalue(),
					"image_info": image_info,
					"on_result": on_result
				}
			)
			self._thread.start()

	# 内部识别函数，供导航对象识别和剪贴板识别调用
	def _recognize(self, pixels, image_info, on_result):
		try:
			log.debug("开始识别线程。")
			if not self._access_token:
				# 获取access_token
				self._fetch_access_token()
			# 判断是否用户更换了app key和app secret，如果配置中的参数与当前self._app_key和self._app_secret不一致，则说明用户做了更换操作
			app_key = config.conf["xinyiOcr"]["baidu"]["shareAppKey"] \
			if config.conf["xinyiOcr"]["baidu"]["usingShareKey"] else config.conf["xinyiOcr"]["baidu"]["myAppKey"]
			app_secret = config.conf["xinyiOcr"]["baidu"]["shareAppSecret"] \
			if config.conf["xinyiOcr"]["baidu"]["usingShareKey"] else config.conf["xinyiOcr"]["baidu"]["myAppSecret"]
			if app_key != self._app_key or app_secret != self._app_secret:
				self._fetch_access_token()
			if not self._access_token or not pixels or not image_info or not on_result:
				log.debug("参数错误。")
				return
			# 针对图片二进制数据进行base64编码
			b64img = base64.b64encode(pixels)
			# 调用百度在线OCR识别接口识别图片中文字
			url = f"{self.url}?access_token={self._access_token}"
			headers = {"Content-type": "application/x-www-form-urlencoded"}
			payload = bytes(urllib.parse.urlencode({"image": b64img}).encode("utf-8"))
			response = self._http_request(url=url, headers=headers, payload=payload, method="POST")
			if not response or response.get("error_code") is not None:
				log.debug(f"调用识别API失败：\n{response.get('error_msg')}")
				# Translators: Recognition failed
				ui.message(_("Recognition failed"))
				return
			lines = list()
			words_result = response.get("words_result")
			for item in words_result:
				words = list()
				location = item.get("location")
				word = {
					"text": item.get("words"),
					"x": location.get("left"),
					"y": location.get("top"),
					"width": location.get("width"),
					"height": location.get("height")
				}
				words.append(word)
				lines.append(words)
			result = LinesWordsResult(lines, image_info)
			log.debug("调用识别回调。")
			on_result(result)
		except Exception as e:
			log.error(f"识别失败：\n{e}")
			ui.message(_("Recognition failed"))
			return

	# 取消识别方法
	def cancel(self):
		# 暂不实现此功能
		pass


# 百度通用文字识别高精度版接口
class BaiduAccurateOcr(BaiduOcr):
	# Translators: Baidu Accurate OCR
	name = _("Baidu Accurate OCR")
	url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate"


# 百度通用文字识别标准版接口
class BaiduGeneralOcr(BaiduOcr):
	# Translators: Baidu General OCR
	name = _("Baidu General OCR")
	url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general"
