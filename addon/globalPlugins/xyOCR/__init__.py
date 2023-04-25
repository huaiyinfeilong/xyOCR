import globalPluginHandler
import scriptHandler
import addonHandler
import api
from logHandler import log
import ui
import tones
from datetime import datetime
from contentRecog import recogUi
from .paddleOcr import PaddleOcr

addonHandler.initTranslation()

    # Translators: Script description
CATEGORY_NAME = _("Xinyi OCR")

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
    ocr = PaddleOcr()

    def __init__(self):
        super(globalPluginHandler.GlobalPlugin, self).__init__()
        if self.ocr is not None:
            self.ocr.initRecognizer()

    # Translators: Category name
    @scriptHandler.script(description = _("Text recognition"), category = CATEGORY_NAME, gesture = "kb:NVDA+ALT+O")
    def script_doOcr(self, gesture):
        if self.ocr is None:
            # Translators: Recognition failed
            ui.message(_("Recognition failed"))
        recogUi.recognizeNavigatorObject(self.ocr)

    def terminate(self):
        if self.ocr is not None:
            self.ocr.uninitRecognizer()
            self.ocr = None
