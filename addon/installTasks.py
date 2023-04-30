import addonHandler
addonHandler.initTranslation()
# coding=utf-8

from ctypes import (
	windll,
	POINTER,
	wintypes,
	Structure,
	CDLL,
	byref
						)


# 处理器架构类型定义
class ProcessorArchitecture(object):
	# x64 (AMD or Intel)
	PROCESSOR_ARCHITECTURE_AMD64 = 9
	# ARM
	PROCESSOR_ARCHITECTURE_ARM = 5
	# ARM64
	PROCESSOR_ARCHITECTURE_ARM64 = 12
	# Intel Itanium-based
	PROCESSOR_ARCHITECTURE_IA64 = 6
	# x86
	PROCESSOR_ARCHITECTURE_INTEL = 0
	# Unknown architecture.
	PROCESSOR_ARCHITECTURE_UNKNOWN = 0xffff


# WIN32 SystemInformation结构体定义
class SystemInfo(Structure):
	_fields_ = [
		("wProcessorArchitecture", wintypes.WORD),
		("wReserved", wintypes.WORD),
		("dwPageSize", wintypes.DWORD),
		("lpMinimumApplicationAddress", wintypes.LPVOID),
		("lpMaximumApplicationAddress", wintypes.LPVOID),
		("dwActiveProcessorMask", wintypes.LPDWORD),
		("dwNumberOfProcessors", wintypes.DWORD),
		("dwProcessorType", wintypes.DWORD),
		("dwAllocationGranularity", wintypes.DWORD),
		("wProcessorLevel", wintypes.DWORD),
		("wProcessorRevision", wintypes.WORD)
	]


def is64ProcessorArchitecture():
	"""检查是否x64系统
		@return: 如果为x64系统返回True，否则返回False
		@rtype: bool
	"""
	sysInfo = SystemInfo()
	GetNativeSystemInfo = windll.kernel32.GetNativeSystemInfo
	GetNativeSystemInfo(byref(sysInfo))
	return sysInfo.wProcessorArchitecture == ProcessorArchitecture.PROCESSOR_ARCHITECTURE_AMD64


def onInstall():
	if is64ProcessorArchitecture():
		return
	import gui
	import wx
	import globalVars
	# Translators: title of the error dialog shown when trying to install the add-on in unsupported systems.
	unsupportedArchitectureTitle = _("Unable to complete installation")
	unsupportedArchitectureText = _(
		# Translators: Dialog text shown when trying to install the add-on on an unsupported processor architecture.
		"This addon can only run on 64-bit systems, but you are currently using a 32-bit system, so the installation cannot be completed."
	)
	# Do not present error dialog if minimal mode is set.
	if not globalVars.appArgs.minimal:
		gui.messageBox(unsupportedArchitectureText, unsupportedArchitectureTitle, wx.OK | wx.ICON_ERROR)
	raise RuntimeError(f"xyOCR does not support {currentWinVer})")
