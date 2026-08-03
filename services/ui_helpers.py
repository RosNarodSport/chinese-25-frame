import math

from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QFontMetrics, QPainter, QPixmap, QColor
from PyQt5.QtWidgets import QLabel


def _rotated_bounds(text_w: int, text_h: int, angle: int, pad: int) -> tuple[int, int]:
    rad = math.radians(angle)
    cos_a = abs(math.cos(rad))
    sin_a = abs(math.sin(rad))
    box_w = int(text_w * cos_a + text_h * sin_a) + pad * 2
    box_h = int(text_w * sin_a + text_h * cos_a) + pad * 2
    return max(box_w, 1), max(box_h, 1)


def _fit_pixmap(pixmap: QPixmap, max_w: int, max_h: int) -> QPixmap:
    if max_w <= 0 or max_h <= 0:
        return pixmap
    if pixmap.width() <= max_w and pixmap.height() <= max_h:
        return pixmap
    return pixmap.scaled(max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def set_hieroglyph_label(
    label: QLabel,
    text: str,
    font_family: str,
    font_size: int,
    color: str,
    angle: int = 0,
) -> None:
    label.setScaledContents(False)

    if not text:
        label.clear()
        label.setPixmap(QPixmap())
        return

    font = QFont(font_family, font_size)
    if angle == 0:
        label.setPixmap(QPixmap())
        label.setFont(font)
        label.setStyleSheet(f'color: {color}; background: transparent;')
        label.setText(text)
        label.setAlignment(Qt.AlignCenter)
        return

    metrics = QFontMetrics(font)
    bounds = metrics.boundingRect(text)
    pad = max(12, font_size // 3)
    envelope = max(bounds.width(), bounds.height()) + pad
    box_w, box_h = _rotated_bounds(envelope, envelope, abs(angle), pad)

    pixmap = QPixmap(box_w, box_h)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)
    painter.setFont(font)
    painter.setPen(QColor(color))
    painter.translate(box_w / 2, box_h / 2)
    painter.rotate(angle)
    draw_rect = QRect(-envelope // 2, -envelope // 2, envelope, envelope)
    painter.drawText(draw_rect, Qt.AlignCenter, text)
    painter.end()

    pixmap = _fit_pixmap(pixmap, label.width(), label.height())

    label.setText('')
    label.setStyleSheet('background: transparent;')
    label.setPixmap(pixmap)
    label.setAlignment(Qt.AlignCenter)
