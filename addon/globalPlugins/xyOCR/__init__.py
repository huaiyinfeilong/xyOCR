import globalPluginHandler
import scriptHandler
import addonHandler
import ui
from contentRecog import recogUi
import api
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

    @scriptHandler.script(
        # Translators: Text recognition
        description=_("Text recognition"),
        category=CATEGORY_NAME,
        gesture="kb:NVDA+ALT+O"
    )
    def script_recognize_image(self, gesture):
        if self.ocr is None:
            # Translators: Recognition failed
            ui.message(_("Recognition failed"))
        recogUi.recognizeNavigatorObject(self.ocr)

    @scriptHandler.script(
        # Translators: Clipboard recognition
        description=_("Clipboard recognition"),
        category=CATEGORY_NAME,
        gesture="kb:NVDA+SHIFT+ALT+O"
    )
    def script_recognize_clipboard(self, gesture):
        # Translators: Virtual document title: Recognition result
        title = _("Recognition result")
        if api.getFocusObject().name == title \
        or isinstance(api.getFocusObject(), recogUi.RecogResultNVDAObject):
            # Translators: Already in a content recognition result
            ui.message(_("Already in a content recognition result"))
            return
        # Translators: Recognizing
        ui.message(_("Recognizing"))
        result = self.ocr.recognize_clipboard()
        ui.browseableMessage(result, title=title)

    def terminate(self):
        if self.ocr is not None:
            self.ocr.uninitRecognizer()
            self.ocr = None
