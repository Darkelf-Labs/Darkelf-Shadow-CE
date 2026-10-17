import sys
import platform as _platform
from math import cos, sin, radians, pi
from PySide6.QtCore import Qt, QPointF, QRectF

from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QPainter,
    QColor,
    QPen,
    QBrush,
    QPolygonF,
    QPainterPath,
)

_ICON_CACHE = {}

def _get_cached_icon(key, builder):
    """
    Return a cached QIcon or build it once.

    key: tuple, e.g. ("reload", "#00ff88", 22)
    builder: lambda returning QIcon
    """
    icon = _ICON_CACHE.get(key)

    if icon is None:
        icon = builder()
        _ICON_CACHE[key] = icon

    return icon
    
# --- Custom Icon helpers ---
def make_icon(color=None, size=24):

    if color is None:
        color = "#A855F7"

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)

    p.drawEllipse(4, 4, size-8, size-8)

    p.end()
    return QIcon(pix)

def make_nav_arrow_icon(direction: str, color: str, size: int = 22) -> QIcon:

    key = ("nav", direction, color, size)

    if key in _ICON_CACHE:
        return _ICON_CACHE[key]
        
    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    pen = QPen(
        QColor(color),
        max(2.5, size * 0.12),
        Qt.SolidLine,
        Qt.RoundCap,
        Qt.RoundJoin,
    )

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    if direction == "left":

        path = QPainterPath()
        path.moveTo(size * 0.66, size * 0.18)
        path.lineTo(size * 0.36, size * 0.50)
        path.lineTo(size * 0.66, size * 0.82)

    else:

        path = QPainterPath()
        path.moveTo(size * 0.34, size * 0.18)
        path.lineTo(size * 0.64, size * 0.50)
        path.lineTo(size * 0.34, size * 0.82)

    p.drawPath(path)

    p.end()
    
    icon = QIcon(pix)
    _ICON_CACHE[key] = icon

    return icon

def make_reload_icon(color: str, size: int = 22) -> QIcon:
    dpr = 2.0

    pix = QPixmap(int(size * dpr), int(size * dpr))
    pix.setDevicePixelRatio(dpr)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(
        QColor(color),
        max(2.2, size * 0.10),
        Qt.SolidLine,
        Qt.RoundCap,
        Qt.RoundJoin,
    )
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    margin = size * 0.18
    rect = QRectF(
        margin,
        margin,
        size - margin * 2,
        size - margin * 2,
    )

    start_angle = 45
    span_angle = 290

    p.drawArc(rect, start_angle * 16, span_angle * 16)

    #
    # Arrow head positioned exactly at arc end
    #
    cx = rect.center().x()
    cy = rect.center().y()
    r = rect.width() / 2

    end_angle = start_angle + span_angle

    theta = radians(-end_angle)

    tip = QPointF(
        cx + r * cos(theta),
        cy + r * sin(theta),
    )

    # Tangent direction (clockwise arc)
    tx = sin(theta)
    ty = -cos(theta)

    arrow_len = size * 0.22
    arrow_width = size * 0.16

    left = QPointF(
        tip.x() - tx * arrow_len + ty * arrow_width / 2,
        tip.y() - ty * arrow_len - tx * arrow_width / 2,
    )

    right = QPointF(
        tip.x() - tx * arrow_len - ty * arrow_width / 2,
        tip.y() - ty * arrow_len + tx * arrow_width / 2,
    )

    head = QPainterPath()
    head.moveTo(tip)
    head.lineTo(left)
    head.lineTo(right)
    head.closeSubpath()

    p.fillPath(head, QColor(color))
    p.end()

    return QIcon(pix)
    
def make_inspector_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)

    p.setRenderHint(QPainter.Antialiasing, True)

    accent = QColor(color)

    pen = QPen(
        accent,
        max(2, int(size * 0.085)),
        Qt.SolidLine,
        Qt.RoundCap,
        Qt.RoundJoin
    )

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    cx = size / 2
    cy = size / 2

    outer = size * 0.38
    inner = size * 0.18

    # --- OUTER HEXAGON ---
    outer_hex = QPolygonF([
        QPointF(cx,                     cy - outer),
        QPointF(cx + outer * 0.866,    cy - outer * 0.5),
        QPointF(cx + outer * 0.866,    cy + outer * 0.5),
        QPointF(cx,                     cy + outer),
        QPointF(cx - outer * 0.866,    cy + outer * 0.5),
        QPointF(cx - outer * 0.866,    cy - outer * 0.5),
    ])

    p.drawPolygon(outer_hex)

    # --- INNER HEXAGON ---
    inner_hex = QPolygonF([
        QPointF(cx,                     cy - inner),
        QPointF(cx + inner * 0.866,    cy - inner * 0.5),
        QPointF(cx + inner * 0.866,    cy + inner * 0.5),
        QPointF(cx,                     cy + inner),
        QPointF(cx - inner * 0.866,    cy + inner * 0.5),
        QPointF(cx - inner * 0.866,    cy - inner * 0.5),
    ])

    p.drawPolygon(inner_hex)

    p.end()

    return QIcon(pix)
    
def make_cut_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    pen = QPen(
        QColor(color),
        max(2.0, size * 0.10),
        Qt.SolidLine,
        Qt.RoundCap,
        Qt.RoundJoin,
    )

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    # Handles
    r = size * 0.12

    upper = QPointF(size * 0.30, size * 0.34)
    lower = QPointF(size * 0.30, size * 0.66)

    p.drawEllipse(upper, r, r)
    p.drawEllipse(lower, r, r)

    # Pivot
    pivot = QPointF(size * 0.47, size * 0.50)

    p.drawLine(upper, pivot)
    p.drawLine(lower, pivot)

    # Blades
    p.drawLine(pivot, QPointF(size * 0.82, size * 0.22))
    p.drawLine(pivot, QPointF(size * 0.82, size * 0.78))

    p.end()

    return QIcon(pix)

def make_copy_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(1.8, size*0.10))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    p.drawRoundedRect(
        QRectF(size*0.18, size*0.18, size*0.44, size*0.52),
        2,2
    )

    p.drawRoundedRect(
        QRectF(size*0.36, size*0.34, size*0.44, size*0.52),
        2,2
    )

    p.end()

    return QIcon(pix)
    
def make_paste_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(1.8, size*0.10))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    p.drawRoundedRect(
        QRectF(size*0.22, size*0.22, size*0.56, size*0.60),
        2,2
    )

    p.drawRoundedRect(
        QRectF(size*0.36, size*0.10, size*0.28, size*0.16),
        2,2
    )

    p.drawLine(size*0.34,size*0.42,size*0.66,size*0.42)
    p.drawLine(size*0.34,size*0.56,size*0.60,size*0.56)

    p.end()

    return QIcon(pix)
    
def make_delete_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(1.8, size*0.10))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    p.drawRect(
        QRectF(size*0.28,size*0.30,size*0.44,size*0.48)
    )

    p.drawLine(size*0.22,size*0.30,size*0.78,size*0.30)
    p.drawLine(size*0.40,size*0.22,size*0.60,size*0.22)

    p.drawLine(size*0.42,size*0.40,size*0.42,size*0.68)
    p.drawLine(size*0.58,size*0.40,size*0.58,size*0.68)

    p.end()

    return QIcon(pix)
    
def make_select_all_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(1.8, size*0.10))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    p.drawRoundedRect(
        QRectF(size*0.18,size*0.18,size*0.64,size*0.64),
        2,2
    )

    path = QPainterPath()

    path.moveTo(size*0.30,size*0.52)
    path.lineTo(size*0.44,size*0.66)
    path.lineTo(size*0.72,size*0.34)

    p.drawPath(path)

    p.end()

    return QIcon(pix)
    
def make_bookmark_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), max(2, size // 10))
    pen.setJoinStyle(Qt.RoundJoin)
    pen.setCapStyle(Qt.RoundCap)

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    path = QPainterPath()

    left = size * 0.28
    right = size * 0.72
    top = size * 0.14
    bottom = size * 0.88
    notch = size * 0.68

    path.moveTo(left, top)
    path.lineTo(right, top)
    path.lineTo(right, bottom)
    path.lineTo(size * 0.50, notch)
    path.lineTo(left, bottom)
    path.closeSubpath()

    p.drawPath(path)

    p.end()

    return QIcon(pix)
    
def make_bookmark_filled_icon(
    color: str,
    size: int = 18
) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    pen = QPen(
        QColor(color),
        max(2, size // 10)
    )

    pen.setJoinStyle(Qt.RoundJoin)
    pen.setCapStyle(Qt.RoundCap)

    p.setPen(pen)
    p.setBrush(QColor(color))

    path = QPainterPath()

    left = size * 0.28
    right = size * 0.72
    top = size * 0.14
    bottom = size * 0.88
    notch = size * 0.68

    path.moveTo(left, top)
    path.lineTo(right, top)
    path.lineTo(right, bottom)
    path.lineTo(size * 0.50, notch)
    path.lineTo(left, bottom)
    path.closeSubpath()

    p.drawPath(path)

    # subtle highlight
    highlight = QColor(255, 255, 255, 45)
    p.setPen(Qt.NoPen)
    p.setBrush(highlight)

    p.drawRoundedRect(
        QRectF(
            left + 2,
            top + 2,
            (right - left) - 4,
            size * 0.14
        ),
        2,
        2
    )

    p.end()

    return QIcon(pix)
    
def make_find_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    pen = QPen(
        QColor(color),
        max(2, size // 10),
        Qt.SolidLine,
        Qt.RoundCap,
        Qt.RoundJoin
    )

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    p.drawEllipse(
        QRectF(
            size * 0.15,
            size * 0.15,
            size * 0.45,
            size * 0.45
        )
    )

    p.drawLine(
        QPointF(size * 0.52, size * 0.52),
        QPointF(size * 0.82, size * 0.82)
    )

    p.end()
    return QIcon(pix)
    
def make_source_icon(color="#A855F7", size=18):
    if isinstance(color, QColor):
        color = color.name()

    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color))
    pen.setWidthF(max(1.5, size / 10))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)

    # <
    p.drawLine(
        int(size * 0.42), int(size * 0.24),
        int(size * 0.20), int(size * 0.50)
    )
    p.drawLine(
        int(size * 0.20), int(size * 0.50),
        int(size * 0.42), int(size * 0.76)
    )

    # >
    p.drawLine(
        int(size * 0.58), int(size * 0.24),
        int(size * 0.80), int(size * 0.50)
    )
    p.drawLine(
        int(size * 0.80), int(size * 0.50),
        int(size * 0.58), int(size * 0.76)
    )

    p.end()
    return QIcon(pix)
    
def make_keyboard_icon(color: str, size: int = 18) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    pen = QPen(
        QColor(color),
        max(2, size // 10),
        Qt.SolidLine,
        Qt.RoundCap,
        Qt.RoundJoin
    )

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    # keyboard outer shell
    rect = QRectF(
        size * 0.12,
        size * 0.22,
        size * 0.76,
        size * 0.56
    )

    p.drawRoundedRect(rect, 3, 3)

    # keys
    key_w = size * 0.09
    key_h = size * 0.09

    start_x = size * 0.22
    start_y = size * 0.34

    gap = size * 0.05

    for row in range(2):
        for col in range(5):

            x = start_x + col * (key_w + gap)
            y = start_y + row * (key_h + gap)

            p.drawRoundedRect(
                QRectF(x, y, key_w, key_h),
                1.5,
                1.5
            )

    # space bar
    p.drawRoundedRect(
        QRectF(
            size * 0.30,
            size * 0.58,
            size * 0.40,
            key_h
        ),
        1.5,
        1.5
    )

    p.end()

    return QIcon(pix)
    
def make_java_icon(color: str, size: int = 48) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    accent = QColor(color)

    pen = QPen(
        accent,
        int(size * 0.08),
        Qt.PenStyle.SolidLine,
        Qt.PenCapStyle.RoundCap,
        Qt.PenJoinStyle.RoundJoin
    )

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    for i, offset in enumerate([-0.15, 0, 0.15]):

        path = QPainterPath()

        cx = size * 0.5 + offset * size
        top = size * 0.16 + i * size * 0.05

        path.moveTo(cx, top)

        path.cubicTo(
            cx + size * 0.08,
            top + size * 0.04,
            cx - size * 0.08,
            top + size * 0.10,
            cx,
            top + size * 0.18
        )

        p.drawPath(path)

    cup_rect = QRectF(size*0.20, size*0.53, size*0.60, size*0.23)
    body_rect = QRectF(size*0.28, size*0.63, size*0.44, size*0.18)
    saucer_rect = QRectF(size*0.17, size*0.78, size*0.66, size*0.14)
    handle_rect = QRectF(size*0.68, size*0.62, size*0.18, size*0.22)

    p.drawArc(cup_rect, 0, 16 * 180)
    p.drawArc(body_rect, 0, 16 * 180)
    p.drawArc(saucer_rect, 0, 16 * 180)
    p.drawArc(handle_rect, 16 * 40, 16 * 175)

    p.end()

    return QIcon(pix)

def make_settings_icon(color: str, size: int = 18) -> QIcon:
    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing, True)

    pen = QPen(
        QColor(color),
        max(1.8, size * 0.09),
        Qt.SolidLine,
        Qt.RoundCap,
        Qt.RoundJoin,
    )

    p.setPen(pen)
    p.setBrush(Qt.NoBrush)

    cx = size / 2
    cy = size / 2

    # Slightly smaller gear
    outer = size * 0.28
    inner = size * 0.16
    tooth = size * 0.09

    for i in range(8):
        angle = i * pi / 4

        x1 = cx + cos(angle) * outer
        y1 = cy + sin(angle) * outer

        x2 = cx + cos(angle) * (outer + tooth)
        y2 = cy + sin(angle) * (outer + tooth)

        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    p.drawEllipse(QPointF(cx, cy), outer, outer)
    p.drawEllipse(QPointF(cx, cy), inner, inner)

    p.end()
    return QIcon(pix)
    
def make_shield_icon(color, size=18):

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QColor(color))
    painter.setPen(Qt.NoPen)

    path = QPainterPath()

    w = size
    h = size

    path.moveTo(w * 0.5, h * 0.05)
    path.lineTo(w * 0.1, h * 0.25)
    path.lineTo(w * 0.1, h * 0.55)

    path.cubicTo(w * 0.1, h * 0.75, w * 0.3, h * 0.9, w * 0.5, h * 0.95)
    path.cubicTo(w * 0.7, h * 0.9, w * 0.9, h * 0.75, w * 0.9, h * 0.55)

    path.lineTo(w * 0.9, h * 0.25)
    path.closeSubpath()

    painter.drawPath(path)
    painter.end()

    return QIcon(pix)

def make_nuke_icon(hex_color: str, size: int) -> QIcon:

    pix = QPixmap(size * 2, size * 2)
    pix.setDevicePixelRatio(2)
    pix.fill(Qt.transparent)

    p = QPainter(pix)

    # turn AA back on for circles
    p.setRenderHint(QPainter.Antialiasing, True)

    accent = QColor(hex_color)
    black = QColor("#111412")

    # IMPORTANT FIX
    cx = size / 2
    cy = size / 2

    radius = size * 0.42
    border_width = max(2, int(size * 0.08))

    p.setPen(QPen(black, border_width))
    p.setBrush(QBrush(accent))

    p.drawEllipse(
        QRectF(
            cx - radius,
            cy - radius,
            radius * 2,
            radius * 2
        )
    )

    hub_r = size * 0.12

    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(black))

    p.drawEllipse(
        QRectF(
            cx - hub_r,
            cy - hub_r,
            hub_r * 2,
            hub_r * 2
        )
    )

    # radiation blades
    blade_len = size * 0.30
    blade_w = size * 0.11

    p.setBrush(QBrush(black))
    p.setPen(Qt.NoPen)

    for i in range(3):

        p.save()

        p.translate(cx, cy)
        p.rotate(i * 120)

        polygon = QPolygonF([
            QPointF(-blade_w, -hub_r * 1.2),
            QPointF(blade_w,  -hub_r * 1.2),
            QPointF(blade_w * 0.55, -blade_len),
            QPointF(-blade_w * 0.55, -blade_len),
        ])

        p.drawPolygon(polygon)

        p.restore()
        
    p.end()

    return QIcon(pix)
    
def detect_nav_platform():
    system = _platform.system()
    machine = _platform.machine().lower()

    if system == "Darwin":
        return "MacIntel"

    if system == "Windows":
        return "Win32"

    if system == "Linux":
        if "aarch64" in machine or "arm" in machine:
            return "Linux aarch64"
        if "x86_64" in machine or "amd64" in machine:
            return "Linux x86_64"
        return "Linux"

    return sys.platform
