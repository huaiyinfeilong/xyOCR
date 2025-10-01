# coding=utf-8

import base64
import json
import threading
import urllib.parse
import urllib.request
from io import BytesIO

import addonHandler
import config
import ui
from contentRecog import LinesWordsResult, RecogImageInfo
from logHandler import log
from PIL import Image, ImageGrab

from . import helper, ocr

from .secure_storage import decrypt
from .vivo_auth import VivoAuthConnectionError, VivoAuthCredentialsError, VivoAuthError, gen_sign_headers

addonHandler.initTranslation()


class VivoOcr(ocr.Ocr):
	# Translators: The name of the Vivo OCR engine.
	name = _("Vivo OCR (NVDACN)")
	_thread = None
	_domain = "api-ai.vivo.com.cn"
	_uri = "/ocr/general_recognition"
	_method = "POST"

	def initRecognizer(self):
		# No special initialization required for this online engine.
		pass

	def uninitRecognizer(self):
		# No special uninitialization required.
		pass

	def recognize(self, pixels, image_info, on_result):
		"""Recognizes text from navigator object pixels."""
		width = image_info.recogWidth
		height = image_info.recogHeight
		image = Image.frombytes("RGBX", (width, height), pixels, "raw", "BGRX").convert("RGB")
		# Delegate to the helper method to process the image and start the thread.
		self._process_image_and_start_thread(image, image_info, on_result)

	def recognize_clipboard(self, on_result):
		"""Recognizes text from an image in the clipboard."""
		log.debug("Vivo OCR: Starting clipboard recognition.")
		image = ImageGrab.grabclipboard()
		if not isinstance(image, Image.Image):
			log.debug("Clipboard content is not an image, trying file paths.")
			file_list = helper.get_clipboard_image_path()
			if len(file_list) == 1:
				try:
					image = Image.open(file_list[0])
				except IOError:
					image = None

		if not image:
			log.debug("No valid image found on clipboard.")
			ui.message(_("No image on clipboard."))
			return

		log.debug("Successfully got image from clipboard.")
		width, height = image.width, image.height
		image_info = RecogImageInfo(0, 0, width, height, 1)
		# Delegate to the helper method to process the image and start the thread.
		self._process_image_and_start_thread(image, image_info, on_result)

	def _process_image_and_start_thread(self, pil_image, image_info, on_result):
		"""
		Helper method to convert a PIL Image to bytes and start the recognition thread.
		This centralizes the logic previously duplicated in recognize() and recognize_clipboard().
		"""
		output = BytesIO()
		pil_image.save(output, format="PNG")
		image_data = output.getvalue()

		self._start_recognition_thread(image_data, image_info, on_result)

	def _start_recognition_thread(self, image_data, image_info, on_result):
		if self._thread and self._thread.is_alive():
			log.debug("Vivo OCR: A recognition task is already running.")
			return

		self._thread = threading.Thread(target=self._recognize, args=(image_data, image_info, on_result))
		self._thread.start()

	def _recognize(self, image_data, image_info, on_result):
		"""The core recognition logic that runs in a separate thread."""
		try:
			log.debug("Vivo OCR: Recognition thread started.")
			# Step 1: Get NVDACN credentials from config.
			user = config.conf["xinyiOcr"]["nvdacn_account"]["user"]
			encrypted_password = config.conf["xinyiOcr"]["nvdacn_account"]["password"]
			password = decrypt(encrypted_password)

			if not user or not password:
				log.error("Vivo OCR: NVDACN credentials are not configured or failed to decrypt.")
				ui.message(_("Please configure your NVDACN account in Xinyi OCR settings."))
				return

			# Step 2: Generate authentication headers via vivo_auth module.
			headers = gen_sign_headers(user, password, self._method, self._uri, {})
			headers["Content-Type"] = "application/x-www-form-urlencoded"

			# Step 3: Prepare the request body for the Vivo API.
			image_base64 = base64.b64encode(image_data).decode("utf-8")
			post_data = {
				"image": image_base64,
				"pos": 1,  # Request text and absolute coordinates
				"businessid": "1990173156ceb8a09eee80c293135279",  # Advanced recognition mode
			}
			payload = urllib.parse.urlencode(post_data).encode("utf-8")

			# Step 4: Send the request to the Vivo OCR API.
			url = f"https://{self._domain}{self._uri}"
			req = urllib.request.Request(url, data=payload, headers=headers, method=self._method)

			with urllib.request.urlopen(req, timeout=20) as response:
				response_body = response.read()

			response_json = json.loads(response_body)

			# Step 5: Check for errors in the Vivo API response.
			if response_json.get("error_code") != 0:
				error_msg = response_json.get("error_msg", "Unknown Vivo API error")
				log.error(f"Vivo OCR API returned an error: {error_msg}")
				ui.message(_("Vivo API Error: {}").format(error_msg))
				return

			# Step 6: Parse the successful result and call the callback.
			result = self._parse_result(response_json, image_info)
			if result:
				on_result(result)
			else:
				ui.message(_("No text recognized."))

		except VivoAuthCredentialsError as e:
			log.error(f"Vivo Auth Failed: {e}")
			ui.message(_("NVDACN authentication failed. Please check your credentials."))
		except VivoAuthConnectionError as e:
			log.error(f"Vivo Auth Connection Failed: {e}")
			ui.message(_("Could not connect to the authentication server. Please check your network."))
		except VivoAuthError as e:
			log.error(f"An unexpected authentication error occurred: {e}")
			ui.message(_("An unexpected authentication error occurred."))
		except urllib.error.URLError as e:
			log.error(f"Vivo OCR request failed: {e}")
			ui.message(_("Recognition failed: Network error or timeout."))
		except Exception as e:
			log.error(f"An unexpected error occurred during Vivo OCR recognition: {e}", exc_info=True)
			ui.message(_("Recognition failed."))

	def _parse_result(self, result_json, image_info):
		"""Converts the Vivo API JSON response into a LinesWordsResult object."""
		result_data = result_json.get("result", {})
		ocr_items = result_data.get("OCR", [])

		if not ocr_items:
			log.warning("Vivo OCR: No 'OCR' key found in the result payload.")
			return None

		lines = []
		for item in ocr_items:
			text = item.get("words")
			loc = item.get("location")
			if not text or not loc:
				continue

			top_left = loc.get("top_left", {})
			top_right = loc.get("top_right", {})
			down_left = loc.get("down_left", {})

			x = int(top_left.get("x", 0))
			y = int(top_left.get("y", 0))
			width = int(top_right.get("x", 0)) - x
			height = int(down_left.get("y", 0)) - y

			word = {"text": text, "x": x, "y": y, "width": max(0, width), "height": max(0, height)}
			lines.append([word])  # Each recognized item is treated as a line with one word

		return LinesWordsResult(lines, image_info)

	def cancel(self):
		# Currently not implemented for this engine.
		pass
