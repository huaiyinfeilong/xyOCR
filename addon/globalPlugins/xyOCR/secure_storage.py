# coding=utf-8

"""Encrypt and decrypt secrets with Windows DPAPI."""

import base64
import ctypes
from ctypes import wintypes

from logHandler import log


class DATA_BLOB(ctypes.Structure):
	"""Windows DATA_BLOB structure used by DPAPI."""

	_fields_ = [
		("cbData", wintypes.DWORD),
		("pbData", ctypes.POINTER(ctypes.c_ubyte)),
	]


CRYPTPROTECT_UI_FORBIDDEN = 0x01
DATA_DESCRIPTION = "Xinyi OCR Add-on Password"

_crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_CryptProtectData = _crypt32.CryptProtectData
_CryptProtectData.argtypes = [
	ctypes.POINTER(DATA_BLOB),
	wintypes.LPCWSTR,
	ctypes.POINTER(DATA_BLOB),
	wintypes.LPVOID,
	wintypes.LPVOID,
	wintypes.DWORD,
	ctypes.POINTER(DATA_BLOB),
]
_CryptProtectData.restype = wintypes.BOOL

_CryptUnprotectData = _crypt32.CryptUnprotectData
_CryptUnprotectData.argtypes = [
	ctypes.POINTER(DATA_BLOB),
	ctypes.POINTER(wintypes.LPWSTR),
	ctypes.POINTER(DATA_BLOB),
	wintypes.LPVOID,
	wintypes.LPVOID,
	wintypes.DWORD,
	ctypes.POINTER(DATA_BLOB),
]
_CryptUnprotectData.restype = wintypes.BOOL

_LocalFree = _kernel32.LocalFree
_LocalFree.argtypes = [wintypes.HLOCAL]
_LocalFree.restype = wintypes.HLOCAL


def _last_error_message() -> str:
	error_code = ctypes.get_last_error()
	if not error_code:
		return "unknown error"
	return f"{error_code}: {ctypes.FormatError(error_code)}"


def _bytes_to_blob(data: bytes):
	buffer = ctypes.create_string_buffer(data, len(data))
	return DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


def _blob_to_bytes(blob: DATA_BLOB) -> bytes:
	if not blob.pbData or not blob.cbData:
		return b""
	return ctypes.string_at(blob.pbData, blob.cbData)


def _free_blob(blob: DATA_BLOB) -> None:
	if blob.pbData:
		_LocalFree(ctypes.cast(blob.pbData, wintypes.HLOCAL))


def encrypt(plain_text: str) -> str | None:
	"""
	Encrypt a string using Windows DPAPI and return a Base64 encoded string.

	Returns an empty string for an intentionally empty secret, and None if encryption fails.
	"""
	if not plain_text:
		return ""

	blob_out = DATA_BLOB()
	try:
		data_in = plain_text.encode("utf-8")
		blob_in, _buffer_in = _bytes_to_blob(data_in)

		if not _CryptProtectData(
			ctypes.byref(blob_in),
			DATA_DESCRIPTION,
			None,
			None,
			None,
			CRYPTPROTECT_UI_FORBIDDEN,
			ctypes.byref(blob_out),
		):
			log.error(f"DPAPI: CryptProtectData failed: {_last_error_message()}")
			return None

		return base64.b64encode(_blob_to_bytes(blob_out)).decode("ascii")
	except Exception as e:
		log.error(f"DPAPI: An exception occurred during encryption: {e}", exc_info=True)
		return None
	finally:
		_free_blob(blob_out)


def decrypt(encrypted_text: str) -> str | None:
	"""
	Decrypt a Base64 encoded DPAPI value.

	Returns an empty string for an empty stored value, and None if decryption fails.
	"""
	if not encrypted_text:
		return ""

	blob_out = DATA_BLOB()
	try:
		data_in = base64.b64decode(encrypted_text.encode("ascii"), validate=True)
		blob_in, _buffer_in = _bytes_to_blob(data_in)

		if not _CryptUnprotectData(
			ctypes.byref(blob_in),
			None,
			None,
			None,
			None,
			CRYPTPROTECT_UI_FORBIDDEN,
			ctypes.byref(blob_out),
		):
			log.warning(f"DPAPI: CryptUnprotectData failed: {_last_error_message()}")
			return None

		return _blob_to_bytes(blob_out).decode("utf-8")
	except Exception as e:
		log.warning(f"DPAPI: An exception occurred during decryption: {e}", exc_info=True)
		return None
	finally:
		_free_blob(blob_out)
