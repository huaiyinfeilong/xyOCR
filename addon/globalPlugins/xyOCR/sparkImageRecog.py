#-*- coding=utf-8 -*-

""" 讯飞星火图片理解（Image understanding）功能到 ImageRecognizer 的业务封装
	详见： https://www.xfyun.cn/doc/spark/ImageUnderstanding.html
"""


import config
import imageRecog
import addonHandler
import _thread as thread
import base64
import datetime
import hashlib
import hmac
import json
from urllib.parse import urlparse
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlencode
from recogExceptions import AuthenticationException, ImageRecognitionException
import os
import sys
sys.path.insert(0, "\\".join(os.path.dirname(__file__).split("\\")[:-1]) + "\\_py3_contrib")
from wsgiref.handlers import format_date_time
import websocket  # 使用websocket_client


addonHandler.initTranslation()


class Ws_Param(object):
	# 初始化
	def __init__(self, appId, apiKey, apiSecret, imageUnderstandingUrl):
		self.appId = appId
		self.apiKey = apiKey
		self.apiSecret = apiSecret
		self.host = urlparse(imageUnderstandingUrl).netloc
		self.path = urlparse(imageUnderstandingUrl).path
		self.imageUnderstandingUrl = imageUnderstandingUrl

	# 生成url
	def createUrl(self):
		# 生成RFC1123格式的时间戳
		now = datetime.now()
		date = format_date_time(mktime(now.timetuple()))

		# 拼接字符串
		signatureOrigin = "host: " + self.host + "\n"
		signatureOrigin += "date: " + date + "\n"
		signatureOrigin += "GET " + self.path + " HTTP/1.1"

		# 进行hmac-sha256进行加密
		signatureSha = hmac.new(self.apiSecret.encode('utf-8'), signatureOrigin.encode('utf-8'),
								 digestmod = hashlib.sha256).digest()

		signatureShaBase64 = base64.b64encode(signatureSha).decode(encoding='utf-8')

		authorizationOrigin = f'api_key="{self.apiKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signatureShaBase64}"'

		authorization = base64.b64encode(authorizationOrigin.encode('utf-8')).decode(encoding='utf-8')

		# 将请求的鉴权参数组合为字典
		v = {
			"authorization": authorization,
			"date": date,
			"host": self.host
		}
		# 拼接鉴权参数，生成url
		url = self.imageUnderstandingUrl + '?' + urlencode(v)
		return url


class SparkImageRecognizer(imageRecog.ImageRecognizer):
	imageUnderstandingUrl = "wss://spark-api.cn-huabei-1.xf-yun.com/v2.1/image"  # 云端环境的服务地址

	def __init__(self, *args, **kwargs):
		# Update authentication configuration
		self.updateAuthenticationConfiguration(
			config.conf["xinyiOcr"]["IDG"]["spark"]["appId"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiSecret"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiKey"]
		)

	# 收到websocket错误的处理
	def on_error(self, ws, error):
		raise ImageRecognitionException(error)

	# 收到websocket关闭的处理
	def on_close(self, ws, one, two):
		pass

	# 收到websocket连接建立的处理
	def on_open(self, ws):
		thread.start_new_thread(self.run, (ws,))

	def run(self, ws, *args):
		data = json.dumps(self.gen_params(appId=ws.appId, question=ws.question))
		self.ws.send(data)

	# 收到websocket消息的处理
	def on_message(self, ws, message):
		data = json.loads(message)
		code = data['header']['code']
		if code != 0:
		# raise ImageRecognitionException(f"请求错误： {code}, {data}"")
			ws.close()
		else:
			choices = data["payload"]["choices"]
			status = choices["status"]
			content = choices["text"][0]["content"]
			self.answer = ""
			answer += content
			if status == 2:
				ws.close()

	def gen_params(self, appId, question):
		"""
		通过appId和用户的提问来生成请求参数
		"""
		data = {
			"header": {
				"app_id": appId
			},
			"parameter": {
				"chat": {
					"domain": "image",
					"temperature": 0.5,
					"top_k": 4,
					"max_tokens": 2028,
					"auditing": "default"
				}
			},
			"payload": {
				"message": {
					"text": question
				}
			}
		}
		return data

	def _getImageDescription(self, imageData):
		# Update authentication configuration
		self.updateAuthenticationConfiguration(
			config.conf["xinyiOcr"]["IDG"]["spark"]["appId"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiSecret"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiKey"]
		)
		question = self.checklen(self.getText("user", "概要的描述下这张图片"))
		if not self.appId or not self.apiSecret or not self.apiKey:
		# Translators: authencation empty
			raise AuthenticationException(_("Please setup Ifly image understanding API key first"))

		wsParam = Ws_Param(self.appId, self.apiKey, self.apiSecret, SparkImageRecognizer.imageUnderstandingUrl)
		websocket.enableTrace(False)
		wsUrl = wsParam.create_url()
		ws = websocket.WebSocketApp(
			wsUrl,
			on_message=self.on_message,
			on_error=self.on_error,
			on_close=self.on_close,
			on_open=self.on_open)
		ws.appId = self.appId
		self.imageData = imageData
		ws.imageData = imageData
		ws.question = ""
		ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

	def getText(self, role, content):
		text = [{"role": "user", "content": str(base64.b64encode(self.imageData), 'utf-8'), "content_type":"image"}]
		jsoncon = {}
		jsoncon["role"] = role
		jsoncon["content"] = content
		text.append(jsoncon)
		return text

	def getlength(self, text):
		length = 0
		for content in text:
			temp = content["content"]
			leng = len(temp)
			length += leng
		return length

	def checklen(self, text):
		while (self.getlength(text[1:])> 8000):
			del text[1]
		return text

	def updateAuthenticationConfiguration(self, appId, apiSecret, apiKey):
		"""
Update authentication configuration
		@param appId: APP ID
		@param appSecret: API secret
		@param apiKey: API key
		"""
		self.app_id = appId
		self.api_secret = apiSecret
		self.api_key = apiKey
