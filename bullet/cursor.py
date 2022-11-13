import os
import sys
from contextlib import contextmanager

# Show and hide cursors

if os.system == 'nt':
    import ctypes
    import msvcrt

    class _CursorInfo(ctypes.Structure):
        _fields_ = [("size", ctypes.c_int),
                    ("visible", ctypes.c_byte)]

@contextmanager
def hide():
    try:
        _hide_cursor()
        yield
    finally:
        _show_cursor()

def _hide_cursor():
    if os.system == 'nt':
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = False
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.system == 'posix':
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

def _show_cursor():
    if os.system == 'nt':
        ci = _CursorInfo()
        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        ctypes.windll.kernel32.GetConsoleCursorInfo(handle, ctypes.byref(ci))
        ci.visible = True
        ctypes.windll.kernel32.SetConsoleCursorInfo(handle, ctypes.byref(ci))
    elif os.system == 'posix':
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
