"""Визуальная тема приложения — светлый dashboard в стиле «Вариант 1»."""

from PyQt5.QtCore import Qt

BG = '#F0F4F8'
SURFACE = '#FFFFFF'
BORDER = '#E2E8F0'
PRIMARY = '#4E81FB'
PRIMARY_HOVER = '#3B6FE8'
PRIMARY_PRESSED = '#2F5FD4'
TEXT = '#1E293B'
TEXT_MUTED = '#64748B'
SUCCESS = '#22C55E'
ERROR = '#EF4444'
PREVIEW_BG = '#F8FAFC'

APP_FONT = 'Segoe UI'
GLYPH_FONT = 'Segoe UI'


def build_dialog_stylesheet() -> str:
    return f"""
QDialog {{
    background-color: {BG};
    color: {TEXT};
}}
QDialog QWidget {{
    background-color: {BG};
    color: {TEXT};
}}
QDialog QLabel {{
    background-color: {BG};
    color: {TEXT};
    font-size: 13px;
}}
QDialog QCheckBox,
QDialog QRadioButton {{
    background-color: {BG};
    color: {TEXT};
    font-size: 13px;
    spacing: 8px;
}}
QDialog QPushButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 6px 14px;
    min-width: 72px;
}}
QDialog QPushButton:hover {{
    border-color: {PRIMARY};
    color: {PRIMARY};
}}
QDialog QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background: {SURFACE};
}}
QDialog QCheckBox::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}
QDialog QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid {BORDER};
    background: {SURFACE};
}}
QDialog QRadioButton::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}
"""


def apply_dialog_theme(dialog) -> None:
    from PyQt5.QtGui import QColor, QPalette

    dialog.setStyleSheet(build_dialog_stylesheet())
    dialog.setAutoFillBackground(True)
    palette = dialog.palette()
    palette.setColor(QPalette.Window, QColor(BG))
    palette.setColor(QPalette.WindowText, QColor(TEXT))
    palette.setColor(QPalette.Text, QColor(TEXT))
    palette.setColor(QPalette.ButtonText, QColor(TEXT))
    dialog.setPalette(palette)


def build_stylesheet() -> str:
    return f"""
QMainWindow, QDialog {{
    background-color: {BG};
    color: {TEXT};
}}

QWidget {{
    background: transparent;
    color: {TEXT};
}}

QTabWidget::pane {{
    border: none;
    background: {BG};
    top: -1px;
}}

QTabBar::tab {{
    background: transparent;
    color: {TEXT_MUTED};
    padding: 10px 28px;
    margin: 10px 6px 0 6px;
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background: {SURFACE};
    color: {PRIMARY};
}}

QTabBar::tab:hover:!selected {{
    background: rgba(255, 255, 255, 0.65);
    color: {TEXT};
}}

QFrame#panelCard, QFrame#showCard {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 16px;
}}

QLabel#valueField {{
    background: #E8F0FE;
    border: 1px solid #C7D7F7;
    border-radius: 6px;
    padding: 2px 8px;
    color: {TEXT};
}}

QLabel#gridHeader {{
    color: {TEXT};
    font-weight: 600;
}}

QLabel#fieldLabel {{
    color: {TEXT_MUTED};
}}

QLabel#chipLabel {{
    background: {PREVIEW_BG};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 4px 10px;
    color: {TEXT_MUTED};
    font-weight: 600;
}}

QLabel#previewGlyph {{
    background: {PREVIEW_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

QLabel#footerLabel {{
    color: {TEXT_MUTED};
}}

QPushButton#primaryButton {{
    background-color: {PRIMARY};
    color: white;
    border: none;
    border-radius: 20px;
    padding: 8px 22px;
    font-weight: 600;
}}

QPushButton#primaryButton:hover {{
    background-color: {PRIMARY_HOVER};
}}

QPushButton#primaryButton:pressed {{
    background-color: {PRIMARY_PRESSED};
}}

QPushButton#secondaryButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 20px;
    padding: 8px 18px;
    font-weight: 500;
}}

QPushButton#secondaryButton:hover {{
    border-color: {PRIMARY};
    color: {PRIMARY};
}}

QPushButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 6px 14px;
}}

QPushButton:hover {{
    border-color: {PRIMARY};
    color: {PRIMARY};
}}

QLineEdit, QComboBox {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 6px 12px;
    color: {TEXT};
    min-height: 20px;
}}

QLineEdit:focus, QComboBox:focus, QComboBox:on {{
    border-color: {PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QComboBox QAbstractItemView {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    selection-background-color: {PRIMARY};
    selection-color: white;
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    width: 18px;
    height: 18px;
    margin: -6px 0;
    background: {PRIMARY};
    border-radius: 9px;
    border: 2px solid white;
}}

QSlider::sub-page:horizontal {{
    background: {PRIMARY};
    border-radius: 3px;
}}

QCheckBox, QRadioButton {{
    spacing: 8px;
    color: {TEXT};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background: {SURFACE};
}}

QCheckBox::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 1px solid {BORDER};
    background: {SURFACE};
}}

QRadioButton::indicator:checked {{
    background: {PRIMARY};
    border-color: {PRIMARY};
}}

QProgressBar {{
    border: none;
    background: {BORDER};
    border-radius: 8px;
    min-height: 12px;
    text-align: center;
    color: {TEXT_MUTED};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {PRIMARY}, stop:1 #6B9AFF);
    border-radius: 8px;
}}

QTableWidget {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
    gridline-color: {BORDER};
    alternate-background-color: {PREVIEW_BG};
}}

QHeaderView::section {{
    background: {PREVIEW_BG};
    color: {TEXT_MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px;
    font-weight: 600;
}}

QScrollBar:vertical {{
    width: 8px;
    background: transparent;
    margin: 4px;
}}

QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QMessageBox {{
    background-color: {BG};
    color: {TEXT};
}}
QMessageBox QLabel {{
    background-color: {BG};
    color: {TEXT};
    font-size: 13px;
    min-width: 280px;
}}
QMessageBox QPushButton {{
    background-color: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 18px;
    padding: 6px 14px;
    min-width: 72px;
}}
"""


def apply_theme(app, form) -> None:
    app.setStyleSheet(build_stylesheet())
    _tag_widget_roles(form)


def _tag_widget_roles(form) -> None:
    value_fields = (
        'label_hsk_group',
        'label_speed_show',
        'label_color_scheme',
        'label_tilt_show',
        'label_num_hieroglyphs_in_show',
        'label_hieroglyph_size',
    )
    for name in value_fields:
        widget = getattr(form, name, None)
        if widget:
            widget.setObjectName('valueField')
            widget.setAlignment(Qt.AlignCenter)

    for name in (
        'label_hsk_group_label',
        'label_speed_show_label',
        'label_label_color_scheme_label',
        'label_tilt_show_label',
        'label_num_hieroglyphs_in_show_label',
        'label_hieroglyph_size_label',
        'label_preset_name_title',
        'label_enter_user_name',
        'label_enter_user_password',
    ):
        widget = getattr(form, name, None)
        if widget:
            widget.setObjectName('fieldLabel')

    for name in (
        'label_col3_hsk',
        'label_col3_color',
        'label_col3_speed',
        'label_col3_show',
        'label_col3_tilt',
        'label_col3_size',
    ):
        widget = getattr(form, name, None)
        if widget:
            widget.setObjectName('gridHeader')

    for name in ('label_17', 'label_16', 'label_about_title'):
        widget = getattr(form, name, None)
        if widget:
            widget.setObjectName('sectionTitle')

    for name in ('label_last_date_label', 'label_work_time_total_label', 'label_name_of_show_complect_label'):
        widget = getattr(form, name, None)
        if widget:
            widget.setObjectName('footerLabel')

    form.label_preview_hieroglyph.setObjectName('previewGlyph')
    form.label_HSK.setObjectName('chipLabel')
    form.label_number.setObjectName('chipLabel')
    form.label_HSK.setAlignment(Qt.AlignCenter)
    form.label_number.setAlignment(Qt.AlignCenter)

    primary_buttons = (
        'pushButton_launch',
        'pushButton_save_new_settings',
        'pushButton_start_all',
        'pushButton_login',
        'pushButton_pause',
    )
    secondary_buttons = (
        'pushButton_sign_up',
        'pushButton_guest',
        'pushButton_exit',
        'pushButton_load_excel',
        'pushButton_template',
        'pushButton_metronome',
        'pushButton_preset_delete',
        'pushButton_preset_rename',
        'pushButton_end',
        'pushButton_admin_refresh',
        'pushButton_admin_delete_user',
        'pushButton_admin_update_user',
        'pushButton_admin_delete_list',
        'pushButton_metronome',
        'pushButton_timer',
    )
    for name in primary_buttons:
        btn = getattr(form, name, None)
        if btn:
            btn.setObjectName('primaryButton')
    for name in secondary_buttons:
        btn = getattr(form, name, None)
        if btn:
            btn.setObjectName('secondaryButton')
