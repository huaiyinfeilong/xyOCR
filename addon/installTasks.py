import addonHandler
addonHandler.initTranslation()


def onInstall():
	import winVersion
	currentWinVer = winVersion.getWinVer()
	currentProcessorArchitecture = currentWinVer.processorArchitecture
	# Optimization: report success (return early) if running a supported architecture.
	if currentProcessorArchitecture == 'AMD64':
		return
	import gui
	import wx
	import globalVars
	# Translators: title of the error dialog shown when trying to install the add-on in unsupported systems.
	unsupportedArchitectureTitle = _("Unable to complete installation")
	unsupportedArchitectureText = _(
		# Translators: Dialog text shown when trying to install the add-on on an unsupported processor architecture.
		"This addon can only run on 64-bit systems, but you are currently using a 32-bit system, so the installation cannot be completed."
	).format(
		Architecture=currentProcessorArchitecture,
	)
	# Do not present error dialog if minimal mode is set.
	if not globalVars.appArgs.minimal:
		gui.messageBox(unsupportedArchitectureText, unsupportedArchitectureTitle, wx.OK | wx.ICON_ERROR)
	raise RuntimeError(f"xyOCR does not support {currentWinVer})")
