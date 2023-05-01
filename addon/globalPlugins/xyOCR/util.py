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
