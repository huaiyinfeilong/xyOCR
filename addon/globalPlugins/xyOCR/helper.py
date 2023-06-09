# coding=utf-8

from ctypes import windll, wintypes, byref, create_unicode_buffer


# 获取剪贴板图片文件列表
def get_clipboard_image_path():
	MAX_PATH = 260
	CF_HDROP = 15
	file_list = list()
	try:
		windll.user32.OpenClipboard(wintypes.HANDLE(None))
		hDrop = windll.user32.GetClipboardData(wintypes.DWORD(CF_HDROP))
		file_count = windll.shell32.DragQueryFileA(
			wintypes.HANDLE(hDrop),
			wintypes.UINT(-1),
			wintypes.LPWSTR(None),
			wintypes.UINT(0))
		if file_count > 0:
			for i in range(file_count):
				filename = create_unicode_buffer(MAX_PATH)
				windll.shell32.DragQueryFileW(
					wintypes.HANDLE(hDrop),
					wintypes.UINT(i),
					byref(filename),
					wintypes.UINT(MAX_PATH))
				file_list.append(filename.value)
	finally:
		windll.user32.CloseClipboard()
	return file_list
