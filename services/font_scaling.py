from PyQt5.QtGui import QFont, QFontMetrics
from PyQt5.QtWidgets import QCheckBox, QLabel, QPushButton, QRadioButton, QWidget


def capture_widget_fonts(tab: QWidget) -> dict[int, QFont]:
    fonts = {}
    for child in tab.children():
        if isinstance(child, QWidget):
            font = child.font()
            if font.pointSize() > 0:
                fonts[id(child)] = QFont(font)
    return fonts


def scaled_font(base_font: QFont, scale: float, minimum: int = 8) -> QFont:
    font = QFont(base_font)
    font.setPointSize(max(minimum, int(round(font.pointSize() * scale))))
    return font


def fit_font_to_rect(text: str, base_font: QFont, max_width: int, max_height: int, minimum: int = 8) -> QFont:
    if not text or max_width <= 0 or max_height <= 0:
        return scaled_font(base_font, 1.0, minimum)

    start_size = base_font.pointSize() if base_font.pointSize() > 0 else 10
    for point_size in range(start_size, minimum - 1, -1):
        font = QFont(base_font)
        font.setPointSize(point_size)
        metrics = QFontMetrics(font)
        if metrics.horizontalAdvance(text) <= max_width and metrics.height() <= max_height:
            return font
    font = QFont(base_font)
    font.setPointSize(minimum)
    return font


def apply_scaled_fonts(tab: QWidget, fonts: dict[int, QFont], scale: float, minimum: int = 8) -> None:
    for child in tab.children():
        if not isinstance(child, QWidget):
            continue
        base_font = fonts.get(id(child))
        if base_font is None:
            continue
        child.setFont(scaled_font(base_font, scale, minimum))
        if isinstance(child, (QLabel, QPushButton, QCheckBox, QRadioButton)):
            text = child.text()
            if text:
                fitted = fit_font_to_rect(
                    text,
                    child.font(),
                    max(1, child.width() - 4),
                    max(1, child.height() - 2),
                    minimum,
                )
                child.setFont(fitted)
