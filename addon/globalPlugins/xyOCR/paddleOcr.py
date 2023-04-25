from contentRecog import ContentRecognizer
from .PPOCR_api import PPOCR
from datetime import datetime
import tempfile
from contentRecog import LinesWordsResult, RecogImageInfo
import ui
import os
import sys
sys.path.append("\\".join(os.path.dirname(__file__).split("\\")[:-1]) + "\\_py3_contrib")
from PIL import Image
import winUser
import winKernel
from ctypes import *


# PaddleOCR-json.exe path
MODEL_ENGINE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "PaddleOCR-json", "PaddleOCR_json.exe"))

class PaddleOcr(ContentRecognizer):
    ocr = None

    def __init__(self, *args, **kwargs):
        super(ContentRecognizer, self).__init__(*args, **kwargs)
        pid = 0
        try:
            pid = self._get_pid()
            if pid != 0:
                self._terminate_process(pid)
        except:
            pass

    def initRecognizer(self):
        # Initialize the PaddleOCR engine
        if self.ocr is None:
            self.ocr = PPOCR(MODEL_ENGINE)
            self._write_pid()

    def uninitRecognizer(self):
        if self.ocr is not None:
            self.ocr.stop()
            self.ocr = None
            self._delete_pidfile()

    def recognize(self, pixels, imageInfo, onResult):
        # Create a temporary file of BMP image
        f = tempfile.TemporaryFile(suffix = ".bmp")
        image_filename = f.name
        f.close()
        width = imageInfo.recogWidth
        height = imageInfo.recogHeight
        image = Image.frombytes("RGBX", (width, height), pixels, "raw", "BGRX")
        image = image.convert("RGB")
        image.save(image_filename)
        # Identify image files
        res = self.ocr.run(image_filename)
        # The code=100 success
        if res["code"] != 100:
            # Translators: Recognition failed
            ui.message(_("Recognition failed"))
            return
        data = res["data"]
        # Convert recognition result data to LWR
        lines = list()
        for item in data:
            box = item["box"]
            text = item["text"]
            word = {
                "x": box[0][0],
                "y": box[0][1],
                "width": box[1][0] - box[0][0],
                "height": box[2][1] - box[0][1],
                "text": text                }
            words = list()
            words.append(word)
            lines.append(words)
        result = LinesWordsResult(lines, imageInfo)
        onResult(result)

    def recognize_clipboard(self):
        res = self.ocr.runClipboard()
        # The code=100 success
        if res.get("code") != 100:
            # Translators: Recognition failed
            ui.message(_("Recognition failed"))
            return
        data = res.get("data")
        result = "\r\n".join([item.get("text") for item in data])
        return result

    def cancel(self):
        pass

    def _get_pidfilename(self):
        return os.path.join(tempfile.gettempdir(), "PaddleOCR_json.pid")

    def _write_pid(self):
        if self.ocr is None:
            return
        # Get thePID of PaddleOCR_json.exe
        pid = self.ocr.ret.pid
        # Save PID to the file: PaddleOCR_json.pid
        pidfilename = self._get_pidfilename()
        with open(pidfilename, "w") as f:
            f.write(str(pid))
        f.close()

    def _get_pid(self):
        pidfilename = self._get_pidfilename()
        pid = 0
        with open(pidfilename, "r") as f:
            pid = f.read()
            f.close()
        return int(pid)

    def _delete_pidfile(self):
        pidfilename = self._get_pidfilename()
        os.remove(pidfilename)

    def _terminate_process(self, pid):
        hProcess = None
        try:
            PROCESS_QUERY_INFORMATION = 0x0400
            PROCESS_TERMINATE = 0x0001
            hProcess = winKernel.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_TERMINATE, 0, pid)
            if hProcess == None:
                return
            max_length = wintypes.DWORD(256)
            imageName = create_string_buffer(max_length.value)
            winKernel.kernel32.QueryFullProcessImageNameA(hProcess, 0, imageName, byref(max_length))
            imageName = imageName.value
            imageName = imageName.decode("GBK")
            if MODEL_ENGINE == imageName:
                winKernel.kernel32.TerminateProcess(hProcess, 0)
        finally:
            if hProcess is not None:
                winKernel.kernel32.CloseHandle(hProcess)
