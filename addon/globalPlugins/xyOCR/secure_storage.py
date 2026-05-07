# coding=utf-8

# A module for encrypting and decrypting data using
# the Windows Data Protection API (DPAPI).

import base64
from ctypes import byref, create_string_buffer, c_void_p, Structure, windll, cast
from ctypes.wintypes import DWORD
from logHandler import log

# --- CTypes Setup for Windows API ---


class DATA_BLOB(Structure):
	"""Represents the Windows DATA_BLOB structure."""

	_fields_ = [("cbData", DWORD), ("pbData", c_void_p)]


# Define function prototypes for the Windows API calls
CryptProtectData = windll.crypt32.CryptProtectData
CryptUnprotectData = windll.crypt32.CryptUnprotectData
LocalFree = windll.kernel32.LocalFree

# Constants
CRYPTPROTECT_UI_FORBIDDEN = 0x01
# A description for the encrypted data, useful for debugging.
DATA_DESCRIPTION = "Xinyi OCR Add-on Password"


def encrypt(plain_text: str) -> str:
	"""
	Encrypts a string using the Windows DPAPI and returns a Base64 encoded string.
	If encryption fails for any reason, returns an empty string.
	"""
	if not plain_text:
		return ""

	try:
		data_in = plain_text.encode("utf-8")
		buffer_in = create_string_buffer(data_in)
		pointer_in = cast(buffer_in, c_void_p)
		blob_in = DATA_BLOB(len(data_in), pointer_in)
		blob_out = DATA_BLOB()

		if CryptProtectData(
			byref(blob_in), DATA_DESCRIPTION, None, None, None, CRYPTPROTECT_UI_FORBIDDEN, byref(blob_out)
		):
			encrypted_data = create_string_buffer(blob_out.cbData)
			windll.kernel32.RtlMoveMemory(encrypted_data, blob_out.pbData, blob_out.cbData)
			LocalFree(blob_out.pbData)
			# Return as a Base64 encoded string for safe storage in config files
			return base64.b64encode(encrypted_data.raw).decode("utf-8")
		else:
			log.error("DPAPI: CryptProtectData failed.")
			return ""
	except Exception as e:
		log.error(f"DPAPI: An exception occurred during encryption: {e}", exc_info=True)
		return ""


def decrypt(encrypted_text: str) -> str:
	"""
	Decrypts a Base64 encoded string that was encrypted using the Windows DPAPI.
	If decryption fails (e.g., data is corrupt, from another user/machine),
	returns an empty string.
	"""
	if not encrypted_text:
		return ""

	try:
		data_in = base64.b64decode(encrypted_text.encode("utf-8"))
		buffer_in = create_string_buffer(data_in)
		pointer_in = cast(buffer_in, c_void_p)
		blob_in = DATA_BLOB(len(data_in), pointer_in)
		blob_out = DATA_BLOB()

		if CryptUnprotectData(
			byref(blob_in), None, None, None, None, CRYPTPROTECT_UI_FORBIDDEN, byref(blob_out)
		):
			decrypted_data = create_string_buffer(blob_out.cbData)
			windll.kernel32.RtlMoveMemory(decrypted_data, blob_out.pbData, blob_out.cbData)
			LocalFree(blob_out.pbData)
			return decrypted_data.raw.decode("utf-8")
		else:
			# This is an expected failure if config is moved to another machine.
			log.warning("DPAPI: CryptUnprotectData failed. This is normal if config was migrated.")
			return ""
	except Exception as e:
		# This can happen if the data is corrupt or not valid Base64.
		log.warning(f"DPAPI: An exception occurred during decryption: {e}")
		return ""
