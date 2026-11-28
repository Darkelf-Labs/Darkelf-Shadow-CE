"""Qt-only rounded window masks without native view or layout changes."""
from functools import lru_cache
from math import sqrt, ceil
from PySide6.QtCore import QRect
from PySide6.QtGui import QRegion


def rounded_window_region(width, height, radius):
    """Rasterize circular corners directly at logical pixel centers."""
    radius = min(max(0, int(radius)), width // 2, height // 2)
    region = QRegion(QRect(0, radius, width, height - 2 * radius))
    for y in range(radius):
        dy = radius - y - 0.5
        inset = max(0, ceil(radius - sqrt(radius * radius - dy * dy) - 0.5))
        region = region.united(QRegion(QRect(inset, y, width - 2 * inset, 1)))
        region = region.united(QRegion(QRect(inset, height - 1 - y, width - 2 * inset, 1)))
    return region



def apply_macos_window_corners(widget, radius, border_color=None):
    """Clip the native content layer, preserving the frameless Qt title bar."""
    import sys
    if sys.platform != "darwin":
        return False
    try:
        import ctypes as C
        # Cache the runtime bridge across resize events.
        bridge = _macos_bridge()
        send, sel, cls = bridge
        ptr = C.c_void_p
        view = int(widget.winId())
        window = send(ptr, view, "window")
        if not window:
            return False
        content = send(ptr, window, "contentView")
        if not content:
            return False
        send(None, content, "setWantsLayer:", (C.c_bool, True))
        layer = send(ptr, content, "layer")
        if not layer:
            return False
        clear = send(ptr, cls("NSColor"), "clearColor")
        send(None, window, "setOpaque:", (C.c_bool, False))
        send(None, window, "setBackgroundColor:", (ptr, clear))
        send(None, layer, "setCornerRadius:", (C.c_double, float(radius)))
        send(None, layer, "setMasksToBounds:", (C.c_bool, True))
        if send(C.c_bool, layer, "respondsToSelector:", (ptr, sel("setCornerCurve:"))):
            curve = send(ptr, cls("NSString"), "stringWithUTF8String:", (C.c_char_p, b"continuous"))
            send(None, layer, "setCornerCurve:", (ptr, curve))
        if border_color is not None:
            from PySide6.QtGui import QColor
            color = QColor(border_color)
            native_color = send(ptr, cls("NSColor"),
                "colorWithSRGBRed:green:blue:alpha:",
                (C.c_double, color.redF()), (C.c_double, color.greenF()),
                (C.c_double, color.blueF()), (C.c_double, color.alphaF()))
            cg_color = send(ptr, native_color, "CGColor")
            if not cg_color:
                return False
            send(None, layer, "setBorderColor:", (ptr, cg_color))
            send(None, layer, "setBorderWidth:", (C.c_double, 1.0))
        send(None, window, "setHasShadow:", (C.c_bool, True))
        send(None, window, "invalidateShadow")
        return True
    except Exception:
        return False

@lru_cache(maxsize=1)
def _macos_bridge():
    import ctypes as C
    objc = C.CDLL("/usr/lib/libobjc.A.dylib")
    ptr = C.c_void_p
    objc.sel_registerName.argtypes = [C.c_char_p]
    objc.sel_registerName.restype = ptr
    objc.objc_getClass.argtypes = [C.c_char_p]
    objc.objc_getClass.restype = ptr
    address = C.cast(objc.objc_msgSend, ptr).value

    def sel(name):
        return objc.sel_registerName(name.encode())

    def cls(name):
        return objc.objc_getClass(name.encode())

    def send(result, target, name, *args):
        fn = C.CFUNCTYPE(result, ptr, ptr, *(t for t, _ in args))(address)
        return fn(target, sel(name), *(v for _, v in args))

    return send, sel, cls
