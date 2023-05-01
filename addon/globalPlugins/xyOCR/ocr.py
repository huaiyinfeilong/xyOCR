# coding=utf-8

from contentRecog import ContentRecognizer

# OCR接口
class Ocr(ContentRecognizer):
	# 抽象方法被调用时抛出的异常信息
	_attribute_error_message = "This method unsupported direct called."

	# 初始化方法
	def initRecognize(self):
		raise AttributeError(self._attribute_error_message)

	# 逆初始化方法
	def uninitRecognize(self):
		raise AttributeError(self._attribute_error_message)

	# 剪贴板识别方法
	def recognize(self, on_result):
		raise AttributeError(self._attribute_error_message)
