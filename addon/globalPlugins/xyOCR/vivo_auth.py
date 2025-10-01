# Copyright (C) 2025, Cary-rowen from NVDACN
#
# This module handles the generation of authentication headers required
# for the VIVO API. It interfaces with the NVDACN API to securely
# obtain a signature without exposing the private APP_KEY on the client-side.

import json
import random
import string
import time
import urllib.parse
import urllib.request
import urllib.error
from logHandler import log

__all__ = ["gen_sign_headers", "VivoAuthError", "VivoAuthConnectionError", "VivoAuthCredentialsError"]

# --- Module Constants ---
NVDACN_API_URL = "https://nvdacn.com/api/"
# This is a public App ID for the service, not a user-specific secret.
VIVO_APP_ID = "3046775094"

# --- Custom Exceptions for this module ---


class VivoAuthError(Exception):
	"""Base exception for authentication-related errors in this module."""

	pass


class VivoAuthConnectionError(VivoAuthError):
	"""Raised when connection to the NVDACN server fails after all retries."""

	pass


class VivoAuthCredentialsError(VivoAuthError):
	"""Raised for business logic errors like invalid user/pass from the NVDACN API."""

	pass


# --- Helper Functions ---


def gen_nonce(length=8):
	"""Generates a random alphanumeric string of a given length."""
	chars = string.ascii_lowercase + string.digits
	return "".join(random.choice(chars) for _ in range(length))


def gen_canonical_query_string(params):
	"""Creates a sorted, URL-encoded query string for signature consistency."""
	if not params:
		return ""

	escape = urllib.parse.quote
	# Sort by key to ensure a consistent order for the signature hash.
	sorted_params = sorted(params.items())
	return "&".join(f"{escape(k)}={escape(str(v))}" for k, v in sorted_params)


def gen_signature(nvdacn_user, nvdacn_pass, signing_string_bytes):
	"""Fetches the signature from the NVDACN API."""
	api_params = {"user": nvdacn_user, "pass": nvdacn_pass, "name": "vivo", "action": "signature"}
	url = f"{NVDACN_API_URL}?{urllib.parse.urlencode(api_params)}"
	last_exception = None

	# Retry up to 3 times for transient network issues.
	for attempt in range(3):
		try:
			req = urllib.request.Request(url, data=signing_string_bytes, method="POST")
			with urllib.request.urlopen(req, timeout=10) as response:
				response_body = response.read()
				result = json.loads(response_body)

			if result.get("code") == 200 and "data" in result:
				return result["data"]  # Success
			else:
				# Business logic errors (e.g., invalid credentials) should not be retried.
				error_message = result.get("data", "Unknown API error")
				raise VivoAuthCredentialsError(
					f"NVDACN API Error: {error_message} (Code: {result.get('code')})"
				)

		except (ConnectionError, urllib.error.URLError) as e:
			# Catch retryable network errors.
			log.warning(f"NVDACN auth connection failed on attempt {attempt + 1}: {e}")
			last_exception = e
			time.sleep(attempt + 1)  # Exponential backoff
			continue

		except (json.JSONDecodeError, KeyError, TypeError) as e:
			# Non-retryable parsing errors.
			raise VivoAuthError(f"Invalid response from NVDACN API: {e}") from e

	# If all attempts fail, raise the custom connection exception.
	raise VivoAuthConnectionError("NVDACN API connection failed after 3 attempts") from last_exception


def gen_sign_headers(nvdacn_user, nvdacn_pass, method, uri, query):
	"""Generates the complete set of authentication headers for the VIVO API."""
	method = str(method).upper()
	timestamp = str(int(time.time()))
	nonce = gen_nonce()

	# Step 1: Prepare the canonical string to be signed.
	canonical_query_string = gen_canonical_query_string(query)
	signed_headers_string = (
		f"x-ai-gateway-app-id:{VIVO_APP_ID}\nx-ai-gateway-timestamp:{timestamp}\nx-ai-gateway-nonce:{nonce}"
	)
	signing_string = (
		f"{method}\n{uri}\n{canonical_query_string}\n{VIVO_APP_ID}\n{timestamp}\n{signed_headers_string}"
	)
	signing_string_bytes = signing_string.encode("utf-8")

	# Step 2: Fetch the signature from the remote service.
	signature = gen_signature(nvdacn_user, nvdacn_pass, signing_string_bytes)

	# Step 3: Assemble the final headers dictionary.
	return {
		"X-AI-GATEWAY-APP-ID": VIVO_APP_ID,
		"X-AI-GATEWAY-TIMESTAMP": timestamp,
		"X-AI-GATEWAY-NONCE": nonce,
		"X-AI-GATEWAY-SIGNED-HEADERS": "x-ai-gateway-app-id;x-ai-gateway-timestamp;x-ai-gateway-nonce",
		"X-AI-GATEWAY-SIGNATURE": signature,
	}
