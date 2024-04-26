#-*- coding=utf-8 -*-

""" 讯飞星火图片理解（Image understanding）功能到 ImageRecognizer 的业务封装
	详见： https://www.xfyun.cn/doc/spark/ImageUnderstanding.html
"""


from logHandler import log
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
		self.appId = ""
		self.apiSecret = ""
		self.apiKey = ""
		self.answer = ""
		self.imageData = None
		self.text = []
		# Update authentication configuration
		self.updateAuthenticationConfiguration(
			config.conf["xinyiOcr"]["IDG"]["spark"]["appId"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiSecret"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiKey"]
		)
		log.debug("【讯飞图片识别】构造函数执行完成")

	# 收到websocket错误的处理
	def on_error(self, ws, error):
		log.debug(f"【讯飞图片识别】WebSocket传输收到错误：{error}")
		raise ImageRecognitionException(error)

	# 收到websocket关闭的处理
	def on_close(self, ws, one, two):
		log.debug("【讯飞图片识别】WebSocket关闭")
		pass

	# 收到websocket连接建立的处理
	def on_open(self, ws):
		log.debug("【讯飞图片识别】处理收到的WebSocket连接")
		thread.start_new_thread(self.run, (ws,))

	def run(self, ws, *args):
		log.debug("【讯飞图片识别】处理WebSocket接收到的数据")
		data = json.dumps(self.gen_params(appId=ws.appId, question=ws.question))
		ws.send(data)

	# 收到websocket消息的处理
	def on_message(self, ws, message):
		log.debug("【讯飞图片识别】收到websocket消息的处理")
		data = json.loads(message)
		code = data['header']['code']
		if code != 0:
		# raise ImageRecognitionException(f"请求错误： {code}, {data}"")
			ws.close()
		else:
			choices = data["payload"]["choices"]
			status = choices["status"]
			content = choices["text"][0]["content"]
			self.answer += content
			if status == 2:
				ws.close()

	def gen_params(self, appId, question):
		log.debug("【讯飞图片识别】生成请求问题")
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
		log.debug("【讯飞图片识别】执行图片识别")
		log.debug("【讯飞图片识别】获取API密钥")
		# Update authentication configuration
		self.updateAuthenticationConfiguration(
			config.conf["xinyiOcr"]["IDG"]["spark"]["appId"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiSecret"],
			config.conf["xinyiOcr"]["IDG"]["spark"]["apiKey"]
		)
		self.answer = ""
		self.imageData = imageData
		question = self.checklen(self.getText("user", "概要的描述下这张图片"))
		if not self.appId or not self.apiSecret or not self.apiKey:
		# Translators: authencation empty
			log.debug("【讯飞图片识别】API密钥为空")
			raise AuthenticationException(_("Please setup Ifly image understanding API key first"))

		try:
			wsParam = Ws_Param(self.appId, self.apiKey, self.apiSecret, SparkImageRecognizer.imageUnderstandingUrl)
			websocket.enableTrace(False)
			wsUrl = wsParam.createUrl()
			ws = websocket.WebSocketApp(
				wsUrl,
				on_message=self.on_message,
				on_error=self.on_error,
				on_close=self.on_close,
				on_open=self.on_open)
			ws.appId = self.appId
			ws.imageData = imageData
			ws.question = question
			ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
		except Exception as e:
			log.error(f"【讯飞图片识别】请求API出错：{str(e)}")
			return None
		self.getText("assistant", self.answer)
		log.debug(f"【讯飞图片识别】识别结果：{self.answer}")
		return self.answer

	def getText(self, role, content):
		self.text = [{"role": "user", "content": str(base64.b64encode(self.imageData), 'utf-8'), "content_type":"image"}]
		jsoncon = {}
		jsoncon["role"] = role
		jsoncon["content"] = content
		self.text.append(jsoncon)
		return self.text

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
		self.appId = appId
		self.apiSecret = apiSecret
		self.apiKey = apiKey
