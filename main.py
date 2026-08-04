import datetime
import os
import subprocess
import sys
import traceback


def _configure_runtime() -> None:
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', '')
        if base:
            os.environ.setdefault(
                'QT_QPA_PLATFORM_PLUGIN_PATH',
                os.path.join(base, 'PyQt5', 'Qt5', 'plugins', 'platforms'),
            )
            os.environ.setdefault(
                'QT_PLUGIN_PATH',
                os.path.join(base, 'PyQt5', 'Qt5', 'plugins'),
            )


_configure_runtime()

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from models.database import ensure_database
from models.show_settings import (
    COLOR_LABELS,
    ShowSettings,
    SPEED_DELAY_MAX,
    SPEED_DELAY_MIN,
    delay_to_slider,
    slider_to_delay,
)
from services.admin import delete_user, get_admin_metrics, list_users, update_user_credentials
from services.auth import UserSession, login_guest, login_user, register_user
from services.excel_import import delete_custom_list, ensure_template, import_excel, list_all_custom_lists, template_path
from services.session import record_app_open
from services.settings_manager import (
    auto_preset_name,
    delete_preset,
    get_latest_preset,
    get_preset,
    list_presets,
    preset_to_settings,
    rename_preset,
    save_preset,
)
from services.slideshow import SlideshowController
from services.ui_helpers import set_hieroglyph_label
from services.app_theme import APP_FONT, GLYPH_FONT, ERROR, SUCCESS, apply_theme

DESIGN_TAB = (1522, 962)
FONT_SCALE = 1.0
UI_SCALE = {'x': 1.0, 'y': 1.0, 'font': FONT_SCALE}
SHOW_TEXT_GAP = max(4, int(10 * 0.65))
SHOW_CTRL_GAP1 = max(6, int(20 * 0.65))
SHOW_CTRL_GAP2 = max(6, int(20 * 0.65))

HSK_CHECKBOXES = {
    'checkBox_show_hsk1': 'HSK1',
    'checkBox_show_hsk1_2': 'HSK2',
    'checkBox_show_hsk1_3': 'HSK3',
    'checkBox_show_hsk1_4': 'HSK4',
}

COLOR_RADIO = {
    'radioButton_black': '#000000',
    'radioButton_green': '#008000',
    'radioButton_blue': '#0000FF',
    'radioButton_red': '#FF0000',
}


def resource_path(relative_path: str) -> str:
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


def load_ui():
    return uic.loadUiType(resource_path(os.path.join('views', 'main_window.ui')))


def scale_font(widget, factor=FONT_SCALE):
    font = widget.font()
    if font.pointSize() > 0:
        widget.setFont(QFont(APP_FONT, max(8, int(font.pointSize() * factor))))


def _place(widget, x, y, w, h, font_size=None):
    widget.setGeometry(int(x), int(y), max(1, int(w)), max(1, int(h)))
    if font_size is not None:
        widget.setFont(QFont(APP_FONT, font_size))


def _create_panel_frames(form):
    form._panel_col1 = QFrame(form.tab_2)
    form._panel_col2 = QFrame(form.tab_2)
    form._panel_col3 = QFrame(form.tab_2)
    for panel in (form._panel_col1, form._panel_col2, form._panel_col3):
        panel.setObjectName('panelCard')
    form._show_card = QFrame(form.tab)
    form._show_card.setObjectName('showCard')
    form._show_controls = QFrame(form.tab)
    form._show_controls.setObjectName('panelCard')
    form.label_show_controls_title = QLabel('Управление показом', form.tab)
    form.label_show_controls_title.setObjectName('sectionTitle')
    form.label_show_progress_pct = QLabel('0%', form.tab)
    form.label_show_progress_pct.setObjectName('mutedLabel')
    form.label_show_progress_pct.setAlignment(Qt.AlignCenter)


def _lower_panels(form):
    for panel in (
        getattr(form, '_panel_col1', None),
        getattr(form, '_panel_col2', None),
        getattr(form, '_panel_col3', None),
        getattr(form, '_show_card', None),
        getattr(form, '_show_controls', None),
    ):
        if panel is not None:
            panel.lower()
            panel.show()
    title = getattr(form, 'label_show_controls_title', None)
    if title is not None:
        title.raise_()
        title.show()
    pct = getattr(form, 'label_show_progress_pct', None)
    if pct is not None:
        pct.raise_()
        pct.show()


def apply_start_tab_layout(form, tab_w, tab_h):
    """Трёхколоночная раскладка вкладки СТАРТ на всю высоту окна."""
    m = 14
    bottom_h = 52
    top = 40
    content_h = tab_h - bottom_h - top
    card_pad = 8

    col1_w = int(tab_w * 0.22)
    col2_w = int(tab_w * 0.34)
    col3_w = tab_w - col1_w - col2_w - 5 * m

    c1 = m
    c2 = c1 + col1_w + m
    c3 = c2 + col2_w + m

    fh, fn, fs = 14, 10, 9
    f = form

    if hasattr(f, '_panel_col1'):
        _place(f._panel_col1, c1 - card_pad, top - card_pad, col1_w + card_pad * 2, content_h + card_pad * 2)
        _place(f._panel_col2, c2 - card_pad, top - card_pad, col2_w + card_pad * 2, content_h + card_pad * 2)
        _place(f._panel_col3, c3 - card_pad, top - card_pad, col3_w + card_pad * 2, content_h + card_pad * 2)

    f.line.hide()
    f.line_3.hide()
    f.line_4.hide()
    f.line_5.hide()

    def col1_y_positions(count):
        step = content_h / max(count, 1)
        return [top + int(step * i) for i in range(count)]

    def col3_y_positions(count):
        step = (content_h - 20) / max(count - 1, 1)
        return [top + int(step * i) for i in range(count)]

    # --- Колонка 1 ---
    y = top
    _place(f.label_17, c1, y, col1_w - 100, 28, fh)
    _place(f.label_current_date, c1 + col1_w - 95, y, 90, 22, fs)
    y += 34
    _place(f.label_enter_user_name, c1, y, col1_w, 24, fn)
    _place(f.lineEdit_user_name, c1, y + 24, col1_w, 30)
    y += 62
    _place(f.label_enter_user_password, c1, y, col1_w, 24, fn)
    _place(f.lineEdit_user_password, c1, y + 24, col1_w, 30)
    y += 62
    btn_h = 36
    btn_gap = 8
    _place(f.pushButton_login, c1, y, col1_w, btn_h, fn)
    _place(f.pushButton_sign_up, c1, y + btn_h + btn_gap, col1_w, btn_h, fn)
    _place(f.pushButton_guest, c1, y + 2 * (btn_h + btn_gap), col1_w, btn_h, fn)
    y += 3 * (btn_h + btn_gap) + 10
    _place(f.label_info_for_user, c1, y, col1_w, 40, fn)
    _place(f.label_user_name, c1, y + 44, col1_w, 28, fn)
    _place(f.label_user_level, c1, y + 76, col1_w, 26, fn)

    # --- Колонка 2 ---
    y2 = col1_y_positions(12)
    _place(f.label_16, c2, y2[0], col2_w, 28, fh)
    label_w = int(col2_w * 0.56)
    val_x = c2 + label_w + 4
    val_w = col2_w - label_w - 4
    summary_rows = [
        (f.label_hsk_group_label, f.label_hsk_group),
        (f.label_speed_show_label, f.label_speed_show),
        (f.label_label_color_scheme_label, f.label_color_scheme),
        (f.label_show_new_start_point_label, f.label_show_new_start_point_2),
        (f.label_num_hieroglyphs_in_show_label, f.label_num_hieroglyphs_in_show),
        (f.label_hieroglyph_size_label, f.label_hieroglyph_size),
    ]
    for i, (lbl, val) in enumerate(summary_rows):
        _place(lbl, c2, y2[1 + i], label_w, 26, fn)
        _place(val, val_x, y2[1 + i], val_w, 26, fn)
    _place(f.label, c2, y2[7], col2_w, 24, fn)
    _place(f.label_history_title, c2, y2[8], 85, 26, fn)
    _place(f.label_login_count, c2 + 90, y2[8], col2_w - 90, 26, fn)
    combo_w = col2_w - 84
    _place(f.comboBox_presets, c2, y2[9], combo_w, 28)
    _place(f.pushButton_preset_delete, c2 + combo_w + 4, y2[9], 34, 28)
    _place(f.pushButton_preset_rename, c2 + combo_w + 40, y2[9], 34, 28)
    _place(f.pushButton_launch, c2, y2[10], 140, 36, fn)

    # --- Колонка 3 ---
    ys = col3_y_positions(13)
    _place(f.label_26, c3, ys[0], col3_w, 28, fh)

    cb_w = max(58, (col3_w - 12) // 4)
    for i, name in enumerate(HSK_CHECKBOXES):
        _place(getattr(f, name), c3 + i * (cb_w + 4), ys[1], cb_w, 24, fn)

    slider_w = col3_w - 110
    val_w = 105
    _place(f.horizontalSlider_speed, c3, ys[2], slider_w, 24)
    _place(f.label_for_horizontalSlider_speed, c3 + slider_w + 5, ys[2], val_w, 24, fn)

    rb_w = max(65, (col3_w - 9) // 4)
    for i, name in enumerate(COLOR_RADIO):
        _place(getattr(f, name), c3 + i * (rb_w + 3), ys[3], rb_w, 24, fn)

    _place(f.horizontalSlider_show_new_start_point, c3, ys[4], slider_w, 24)
    _place(f.label_check_new_start_point, c3 + slider_w + 5, ys[4], val_w, 24, fn)

    _place(f.label_num_hieroglyphs_in_show_label_2, c3, ys[5], slider_w - 10, 26, fn)
    _place(f.lineEdit, c3 + slider_w - 10, ys[5], val_w + 15, 26)

    _place(f.horizontalSlider_size, c3, ys[6], slider_w, 24)
    _place(f.label_for_horizontalSlider_size, c3 + slider_w + 5, ys[6], val_w, 24, fn)

    gap = 6
    load_w = max(130, (col3_w - 2 * gap) // 3)
    tpl_w = load_w
    shuf_w = col3_w - 2 * load_w - 2 * gap
    _place(f.pushButton_load_excel, c3, ys[7], load_w, 28, fn)
    _place(f.pushButton_template, c3 + load_w + gap, ys[7], tpl_w, 28, fn)
    _place(f.checkBox_shuffle, c3 + 2 * (load_w + gap), ys[7], shuf_w, 28, fn)

    tilt_label_w = 55
    _place(f.horizontalSlider_tilt, c3, ys[8], slider_w - tilt_label_w, 24)
    _place(f.label_tilt_value, c3 + slider_w - tilt_label_w + 5, ys[8], val_w, 24, fn)

    y_after_tilt = ys[8] + 30
    preview_h = max(90, int(content_h * 0.18))
    _place(f.label_preview_hieroglyph, c3, y_after_tilt, col3_w, preview_h)

    y_show = y_after_tilt + preview_h + 8
    _place(f.label_4, c3, y_show, col3_w, 24, fn)

    y_checks = y_show + 28
    vis_w = max(72, (col3_w - 9) // 4)
    for i, name in enumerate(
        ('checkBox_show_hieroglyph', 'checkBox_show_translation', 'checkBox_show_pinyin', 'checkBox_show_phrase')
    ):
        _place(getattr(f, name), c3 + i * (vis_w + 3), y_checks, vis_w, 24, fn)

    y_save = y_checks + 30
    _place(f.pushButton_save_new_settings, c3, y_save, col3_w, 34, fn)

    by = tab_h - bottom_h + 10
    _place(f.pushButton_exit, m, by, 100, 32, fn)
    _place(f.label_last_date_label, m + 108, by, 175, 26, fn)
    _place(f.label_last_date, m + 285, by, 100, 26, fn)
    _place(f.label_work_time_total_label, m + 395, by, 120, 26, fn)
    _place(f.label_work_time_total, m + 518, by, 80, 26, fn)
    _place(f.label_name_of_show_complect_label, c2, by, 160, 26, fn)
    _place(f.label_name_of_show_complect, c2 + 165, by, col2_w - 165, 26, fn)

    _lower_panels(f)


def apply_show_tab_layout(form, tab_w, tab_h):
    """Раскладка вкладки ПОКАЗ — карточка с иероглифом и панель управления."""
    m = 20
    top_bar_h = 48
    bottom_h = 92
    card_pad = 10
    controls_h = 56

    pause_w = 170
    _place(form.pushButton_pause, (tab_w - pause_w) // 2, 12, pause_w, 40, 11)

    chip_w = 90
    _place(form.label_HSK, m, top_bar_h, chip_w, 34, 10)
    _place(form.label_number, tab_w - m - chip_w, top_bar_h, chip_w, 34, 10)

    card_y = top_bar_h + 44
    card_h = max(180, int(tab_h * 0.30))
    if hasattr(form, '_show_card'):
        _place(form._show_card, m - card_pad, card_y - card_pad, tab_w - 2 * m + card_pad * 2, card_h + card_pad * 2)

    inner_m = m + 12
    _place(form.label_hieroglyph, inner_m, card_y + 8, tab_w - 2 * inner_m, card_h - 16)

    y = card_y + card_h + max(8, int(20 * 0.65))
    remaining = tab_h - y - bottom_h - 8
    row_h = max(32, remaining // 3)
    _place(form.label_pinyin, m, y, tab_w - 2 * m, row_h, 15)
    _place(form.label_translation, m, y + row_h + SHOW_TEXT_GAP, tab_w - 2 * m, row_h, 14)
    _place(form.label_phrase, m, y + 2 * (row_h + SHOW_TEXT_GAP), tab_w - 2 * m, row_h)

    panel_y = tab_h - bottom_h + 4
    if hasattr(form, '_show_controls'):
        _place(form._show_controls, m - 8, panel_y, tab_w - 2 * m + 16, bottom_h - 8)

    _place(form.label_show_controls_title, m, panel_y + 6, 220, 22, 11)

    row_y = panel_y + 30
    btn_h = 40
    btn_end_w = 158
    btn_start_w = 132
    pct_w = 46
    bar_pct_gap = 8

    end_x = tab_w - m - btn_end_w
    start_x = end_x - SHOW_CTRL_GAP2 - btn_start_w
    pct_x = start_x - SHOW_CTRL_GAP1 - pct_w
    prog_w = max(200, pct_x - m - bar_pct_gap)

    _place(form.progressBar, m, row_y + 4, prog_w, 28)
    _place(form.label_show_progress_pct, pct_x, row_y + 4, pct_w, 28, 11)
    _place(form.pushButton_start_all, start_x, row_y, btn_start_w, btn_h, 10)
    _place(form.pushButton_end, end_x, row_y, btn_end_w, btn_h, 10)

    _lower_panels(form)


def relayout_window(window, form, scale_other_tabs=False):
    menu_h = window.menuBar().height() if window.menuBar() else 0
    client_w = window.width()
    client_h = window.height() - menu_h
    tab_scale_x = client_w / DESIGN_TAB[0]
    tab_scale_y = client_h / DESIGN_TAB[1]
    UI_SCALE['x'] = tab_scale_x
    UI_SCALE['y'] = tab_scale_y
    form.tabWidget.setGeometry(0, 0, client_w, client_h)
    apply_start_tab_layout(form, client_w, client_h)
    apply_show_tab_layout(form, client_w, client_h)
    if scale_other_tabs:
        for tab_name in ('tab_admin',):
            tab = getattr(form, tab_name, None)
            if tab is None:
                continue
            for widget in tab.findChildren(QWidget):
                geometry = widget.geometry()
                widget.setGeometry(
                    int(geometry.x() * tab_scale_x),
                    int(geometry.y() * tab_scale_y),
                    max(1, int(geometry.width() * tab_scale_x)),
                    max(1, int(geometry.height() * tab_scale_y)),
                )
                scale_font(widget)
    if window.menuBar():
        window.menuBar().setGeometry(0, 0, client_w, window.menuBar().height())


def apply_screen_layout(window, form):
    window.setMinimumSize(1024, 700)
    window.resize(1400, 900)
    relayout_window(window, form, scale_other_tabs=True)


class SavePresetDialog(QDialog):
    def __init__(self, default_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Сохранить настройки')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel('Имя набора настроек (до 15 символов):'))
        self.name_edit = QLineEdit(default_name[:15])
        layout.addWidget(self.name_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def preset_name(self) -> str:
        return self.name_edit.text().strip()[:15]


class MainApp:
    def __init__(self):
        ensure_database()
        ensure_template()
        self.app_opens = record_app_open()

        Form, Window = load_ui()
        self.app = QApplication(sys.argv)
        self.window = Window()
        self.form = Form()
        self.form.setupUi(self.window)

        _create_panel_frames(self.form)
        apply_theme(self.app, self.form)

        base_font = QFont(APP_FONT, 10)
        QApplication.setFont(base_font)
        for label in self.window.findChildren(QLabel):
            label.setWordWrap(False)
        for name in ('label_phrase', 'label_translation', 'label_pinyin'):
            getattr(self.form, name).setWordWrap(True)

        apply_screen_layout(self.window, self.form)
        self.form.tabWidget.setTabText(0, 'СТАРТ')
        self.form.tabWidget.setTabText(1, 'ПОКАЗ')
        self._admin_tab_index = -1

        self.session: UserSession = login_guest()
        self.current_settings = ShowSettings.defaults()
        self.settings_dirty = False
        self._login_widgets = [
            self.form.lineEdit_user_name,
            self.form.lineEdit_user_password,
            self.form.pushButton_login,
            self.form.pushButton_sign_up,
            self.form.pushButton_guest,
            self.form.label_enter_user_name,
            self.form.label_enter_user_password,
        ]

        self.slideshow = SlideshowController(self._on_slideshow_update, self._on_slideshow_finished)
        self.form.label_hieroglyph.setScaledContents(False)
        self.form.label_preview_hieroglyph.setScaledContents(False)
        self.form.progressBar.setMinimum(0)
        self.form.progressBar.setMaximum(100)
        self.form.progressBar.setFormat('')
        self.form.progressBar.setTextVisible(False)
        self.form.pushButton_start_all.setText('Старт показа')
        self.form.pushButton_end.setText('Закончить показ')
        self.form.pushButton_pause.setText('ПАУЗА')
        self._wire_signals()
        self._setup_admin_tables()
        self._hide_admin_tab()
        self._reset_profile_labels()
        self._load_settings_to_form(self.current_settings)
        self._update_preview()

        self.window.setWindowTitle('25-й кадр. Китайский язык')
        self.window.resizeEvent = self._window_resize_event
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    def _window_resize_event(self, event):
        from PyQt5.QtWidgets import QMainWindow
        QMainWindow.resizeEvent(self.window, event)
        relayout_window(self.window, self.form)
        self._update_preview()
        if self.slideshow.get_current_card():
            card = self.slideshow.get_current_card()
            self._display_card(
                card,
                int((self.slideshow.current_index + 1) / max(1, self.slideshow.total) * 100),
                self.slideshow.settings,
                self.slideshow.current_index,
            )

    def _wire_signals(self):
        f = self.form
        f.pushButton_login.clicked.connect(self._user_login)
        f.pushButton_sign_up.clicked.connect(self._user_register)
        f.pushButton_guest.clicked.connect(self._user_guest)
        f.pushButton_launch.clicked.connect(self._launch_show)
        f.pushButton_start_all.clicked.connect(self._start_show)
        f.pushButton_pause.clicked.connect(self._toggle_pause)
        f.pushButton_end.clicked.connect(self._end_show)
        f.pushButton_save_new_settings.clicked.connect(self._save_settings)
        f.pushButton_exit.clicked.connect(self._exit_app)
        f.pushButton_load_excel.clicked.connect(self._load_excel)
        f.pushButton_template.clicked.connect(self._open_template)
        f.comboBox_presets.currentIndexChanged.connect(self._preset_selected)
        f.pushButton_preset_delete.clicked.connect(self._delete_preset)
        f.pushButton_preset_rename.clicked.connect(self._rename_preset)
        f.horizontalSlider_size.valueChanged.connect(self._update_preview)
        f.horizontalSlider_speed.valueChanged.connect(self._speed_changed)
        f.horizontalSlider_show_new_start_point.valueChanged.connect(self._start_point_changed)
        f.horizontalSlider_tilt.valueChanged.connect(self._tilt_changed)
        f.checkBox_shuffle.stateChanged.connect(self._mark_dirty)
        for name in HSK_CHECKBOXES:
            checkbox = getattr(f, name)
            checkbox.stateChanged.connect(
                lambda state, active=checkbox: self._hsk_changed(state, active)
            )
        for name in COLOR_RADIO:
            getattr(f, name).toggled.connect(self._update_preview)
        for cb in ('checkBox_show_hieroglyph', 'checkBox_show_pinyin', 'checkBox_show_translation', 'checkBox_show_phrase'):
            getattr(f, cb).stateChanged.connect(self._mark_dirty)
        f.lineEdit.textChanged.connect(self._mark_dirty)
        f.pushButton_admin_refresh.clicked.connect(self._refresh_admin)
        f.pushButton_admin_delete_user.clicked.connect(self._admin_delete_user)
        f.pushButton_admin_update_user.clicked.connect(self._admin_update_user)
        f.pushButton_admin_delete_list.clicked.connect(self._admin_delete_list)
        f.tabWidget.currentChanged.connect(self._tab_changed)
        self.window.closeEvent = self._close_event

    def _setup_admin_tables(self):
        self.form.tableWidget_users.setColumnCount(5)
        self.form.tableWidget_users.setHorizontalHeaderLabels(
            ['ID', 'Имя', 'Входов', 'Время', 'Admin']
        )
        self.form.tableWidget_custom_lists.setColumnCount(4)
        self.form.tableWidget_custom_lists.setHorizontalHeaderLabels(
            ['ID', 'Пользователь', 'Название', 'Карточек']
        )

    def _hide_admin_tab(self):
        idx = self.form.tabWidget.indexOf(self.form.tab_admin)
        if idx >= 0:
            self.form.tabWidget.removeTab(idx)
        self._admin_tab_index = -1

    def _show_admin_tab(self):
        if self._admin_tab_index < 0:
            self._admin_tab_index = self.form.tabWidget.addTab(self.form.tab_admin, 'АДМИН')
            self._refresh_admin()

    def _mark_dirty(self, *_args):
        self.settings_dirty = True

    def _show_error(self, message: str):
        self.form.label_info_for_user.setText(
            f"<span style='color:{ERROR};'>{message.replace(chr(10), ' ')}</span>"
        )

    def _show_success(self, message: str):
        self.form.label_info_for_user.setText(
            f"<span style='color:{SUCCESS};'>{message.replace(chr(10), ' ')}</span>"
        )

    def _after_login(self, session: UserSession, message: str = 'Успешный вход'):
        self.session = session
        self.slideshow.set_user_id(session.user_id)
        for widget in self._login_widgets:
            widget.hide()
        self.form.label_user_name.setText(
            f"<span style='color:{SUCCESS};'>{session.user_name}</span>"
        )
        self.form.label_history_title.show()
        self.form.label_login_count.setText(f'Вход №: {session.login_count + 1}')
        self.form.label_login_count.show()
        if session.is_admin:
            self._show_admin_tab()
        else:
            self._hide_admin_tab()
        self._show_success(message)
        self._refresh_presets()
        latest = get_latest_preset(session.user_id) if session.user_id else None
        if latest:
            self.current_settings = latest
        else:
            self.current_settings = ShowSettings.defaults()
        self._load_settings_to_form(self.current_settings)
        self._update_profile_from_settings()
        self.settings_dirty = False

    def _user_login(self):
        ok, result = login_user(
            self.form.lineEdit_user_name.text(),
            self.form.lineEdit_user_password.text(),
        )
        if ok:
            self._after_login(result)
        else:
            self._show_error(result)

    def _user_register(self):
        ok, result = register_user(
            self.form.lineEdit_user_name.text(),
            self.form.lineEdit_user_password.text(),
        )
        if ok:
            self._after_login(result, 'Регистрация успешна')
        else:
            self._show_error(result)

    def _user_guest(self):
        self.session = login_guest()
        self.slideshow.set_user_id(None)
        for widget in self._login_widgets:
            widget.hide()
        self.form.label_user_name.setText(
            f"<span style='color:#008000;'>Гость</span>"
        )
        self.form.label_history_title.hide()
        self.form.label_login_count.hide()
        self.form.comboBox_presets.clear()
        self._hide_admin_tab()
        self.current_settings = ShowSettings.defaults()
        self._load_settings_to_form(self.current_settings)
        self._update_profile_from_settings()
        self.settings_dirty = False
        self._show_success('Режим гостя')

    def _reset_profile_labels(self):
        for label in (
            self.form.label_user_name,
            self.form.label_user_level,
            self.form.label_hsk_group,
            self.form.label_speed_show,
            self.form.label_color_scheme,
            self.form.label_show_new_start_point_2,
            self.form.label_num_hieroglyphs_in_show,
            self.form.label_hieroglyph_size,
            self.form.label_last_date,
            self.form.label_work_time_total,
            self.form.label_name_of_show_complect,
        ):
            label.setText('...')
        self.form.label_current_date.setText(str(datetime.date.today()))
        self.form.label_history_title.hide()
        self.form.label_login_count.hide()

    def _refresh_presets(self):
        self.form.comboBox_presets.blockSignals(True)
        self.form.comboBox_presets.clear()
        if not self.session.user_id:
            self.form.comboBox_presets.blockSignals(False)
            return
        self._preset_rows = list_presets(self.session.user_id)
        for row in self._preset_rows:
            self.form.comboBox_presets.addItem(row['preset_name'], row['preset_id'])
        self.form.comboBox_presets.blockSignals(False)

    def _preset_selected(self, index: int):
        if index < 0 or not hasattr(self, '_preset_rows'):
            return
        if index >= len(self._preset_rows):
            return
        preset_id = self._preset_rows[index]['preset_id']
        row = get_preset(preset_id)
        if row:
            self.current_settings = preset_to_settings(row)
            self._load_settings_to_form(self.current_settings)
            self._update_profile_from_settings()

    def _delete_preset(self):
        if not self.session.user_id:
            return
        idx = self.form.comboBox_presets.currentIndex()
        if idx < 0:
            return
        preset_id = self.form.comboBox_presets.currentData()
        if delete_preset(self.session.user_id, preset_id):
            self._refresh_presets()
            self._show_success('Настройка удалена')

    def _rename_preset(self):
        if not self.session.user_id:
            return
        preset_id = self.form.comboBox_presets.currentData()
        if preset_id is None:
            return
        new_name, ok = QInputDialog.getText(self.window, 'Переименовать', 'Новое имя (до 15):')
        if ok and new_name:
            success, msg = rename_preset(self.session.user_id, preset_id, new_name)
            if success:
                self._refresh_presets()
                self._show_success('Имя изменено')
            else:
                self._show_error(msg)

    def _read_settings_from_form(self) -> ShowSettings:
        f = self.form
        word_source = 'HSK1'
        for cb_name, hsk_val in HSK_CHECKBOXES.items():
            if getattr(f, cb_name).isChecked():
                word_source = hsk_val
                break
        color = '#008000'
        for radio_name, color_val in COLOR_RADIO.items():
            if getattr(f, radio_name).isChecked():
                color = color_val
                break
        delay_sec = slider_to_delay(f.horizontalSlider_speed.value())
        try:
            article_count = int(f.lineEdit.text() or '150')
        except ValueError:
            article_count = 150
        return ShowSettings(
            preset_name=self.current_settings.preset_name,
            word_source=word_source,
            custom_list_id=self.current_settings.custom_list_id,
            speed_slider=delay_sec,
            color=color,
            start_no=f.horizontalSlider_show_new_start_point.value(),
            article_count=article_count,
            font_size=f.horizontalSlider_size.value(),
            shuffle=f.checkBox_shuffle.isChecked(),
            tilt_degrees=f.horizontalSlider_tilt.value(),
            show_hieroglyph=f.checkBox_show_hieroglyph.isChecked(),
            show_pinyin=f.checkBox_show_pinyin.isChecked(),
            show_translation=f.checkBox_show_translation.isChecked(),
            show_phrase=f.checkBox_show_phrase.isChecked(),
        )

    def _load_settings_to_form(self, settings: ShowSettings):
        f = self.form
        for cb_name, hsk_val in HSK_CHECKBOXES.items():
            checkbox = getattr(f, cb_name)
            checkbox.blockSignals(True)
            checkbox.setChecked(settings.word_source == hsk_val)
            checkbox.blockSignals(False)
        for radio_name, color_val in COLOR_RADIO.items():
            getattr(f, radio_name).setChecked(settings.color == color_val)
        delay = min(SPEED_DELAY_MAX, max(SPEED_DELAY_MIN, float(settings.speed_slider)))
        settings.speed_slider = delay
        f.horizontalSlider_speed.setValue(delay_to_slider(delay))
        f.horizontalSlider_show_new_start_point.setValue(max(1, settings.start_no))
        f.horizontalSlider_size.setValue(settings.font_size)
        f.horizontalSlider_tilt.setValue(settings.tilt_degrees)
        f.lineEdit.setText(str(settings.article_count))
        f.checkBox_shuffle.setChecked(settings.shuffle)
        f.checkBox_show_hieroglyph.setChecked(settings.show_hieroglyph)
        f.checkBox_show_pinyin.setChecked(settings.show_pinyin)
        f.checkBox_show_translation.setChecked(settings.show_translation)
        f.checkBox_show_phrase.setChecked(settings.show_phrase)
        self._speed_changed()
        self._start_point_changed()
        self._tilt_changed()

    def _update_profile_from_settings(self):
        s = self.current_settings
        self.form.label_hsk_group.setText(s.word_source_label)
        delay_sec = s.delay_sec
        self.form.label_speed_show.setText(f'{delay_sec:.2f} сек')
        color_label = COLOR_LABELS.get(s.color, s.color)
        self.form.label_color_scheme.setText(
            f"<span style='color:{s.color}'>{color_label}</span>"
        )
        self.form.label_show_new_start_point_2.setText(f'С номера -> {s.start_no}')
        self.form.label_num_hieroglyphs_in_show.setText(f'Показ по {s.article_count} шт.')
        self.form.label_hieroglyph_size.setText(str(s.font_size))
        self.form.label_name_of_show_complect.setText(s.preset_name)
        if self.session.user_id:
            self.form.label_last_date.setText(self.session.last_date or '...')
            self.form.label_work_time_total.setText(f'{self.session.work_time_total:.0f} сек')
        self.form.label_user_level.setText('Гость' if self.session.is_guest else self.session.user_name)

    def _speed_changed(self):
        delay_sec = slider_to_delay(self.form.horizontalSlider_speed.value())
        self.form.label_for_horizontalSlider_speed.setText(f'{delay_sec:.2f} сек')
        self._mark_dirty()
        self._update_preview()

    def _start_point_changed(self):
        val = self.form.horizontalSlider_show_new_start_point.value()
        self.form.label_check_new_start_point.setText(str(val))
        self._mark_dirty()

    def _tilt_changed(self):
        val = self.form.horizontalSlider_tilt.value()
        self.form.label_tilt_value.setText(f'{val}°')
        self._mark_dirty()
        self._update_preview()

    def _hsk_changed(self, _state, active_cb):
        if active_cb.isChecked():
            for cb_name in HSK_CHECKBOXES:
                cb = getattr(self.form, cb_name)
                if cb is not active_cb:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        self.current_settings.custom_list_id = None
        self._mark_dirty()
        self._update_preview()

    def _update_preview(self, *_args):
        settings = self._read_settings_from_form()
        preview_size = min(42, max(14, int(settings.font_size * 0.9)))
        set_hieroglyph_label(
            self.form.label_preview_hieroglyph,
            '电脑',
            GLYPH_FONT,
            preview_size,
            settings.color,
            settings.tilt_degrees,
        )
        self.form.label_for_horizontalSlider_size.setFont(QFont(APP_FONT, 10))
        self.form.label_for_horizontalSlider_size.setText(str(settings.font_size))
        self.form.label_for_horizontalSlider_size.setAlignment(Qt.AlignCenter)

    def _save_settings(self):
        self.current_settings = self._read_settings_from_form()
        if self.session.is_guest or not self.session.user_id:
            self._update_profile_from_settings()
            self.settings_dirty = False
            self._show_success('Настройки применены (гостевой режим)')
            return
        default_name = auto_preset_name(self.session.login_count + 1)
        dialog = SavePresetDialog(default_name, self.window)
        if dialog.exec_() != QDialog.Accepted:
            return
        name = dialog.preset_name() or default_name
        self.current_settings.preset_name = name
        save_preset(self.session.user_id, self.current_settings, name)
        self.settings_dirty = False
        self._refresh_presets()
        self._update_profile_from_settings()
        self._show_success(f'Настройки сохранены: {name}')

    def _launch_show(self):
        self.current_settings = self._read_settings_from_form()
        self._update_profile_from_settings()
        self.form.tabWidget.setCurrentWidget(self.form.tab)
        card = self.slideshow.get_current_card()
        if card:
            self._display_card(card, 0, self.current_settings)
        else:
            self._display_card_from_settings(self.current_settings)

    def _start_show(self):
        self.current_settings = self._read_settings_from_form()
        self.slideshow.start(self.current_settings)

    def _toggle_pause(self):
        if self.slideshow.is_paused:
            self.slideshow.resume()
            self.form.pushButton_pause.setText('ПАУЗА')
        elif self.slideshow.is_running:
            self.slideshow.pause()
            self.form.pushButton_pause.setText('ДАЛЬШЕ')
        else:
            self._start_show()

    def _end_show(self):
        self.slideshow.stop()
        if not self.session.is_guest and self.session.user_id:
            reply = QMessageBox.question(
                self.window,
                'Сохранить настройки',
                'Сохранить текущие настройки показа?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Yes:
                self._save_settings()
        self.form.tabWidget.setCurrentWidget(self.form.tab_2)
        self.form.progressBar.setValue(0)
        if hasattr(self.form, 'label_show_progress_pct'):
            self.form.label_show_progress_pct.setText('0%')
        self.form.pushButton_pause.setText('ПАУЗА')

    def _on_slideshow_update(self, card, progress, settings, card_index=0):
        self._display_card(card, progress, settings, card_index)

    def _on_slideshow_finished(self):
        self.form.pushButton_pause.setText('ПАУЗА')
        self._show_success('Показ завершён')

    def _display_card_from_settings(self, settings: ShowSettings):
        queue = self.slideshow.build_queue(settings)
        if queue:
            self._display_card(queue[0], 0, settings, 0)

    def _tilt_for_card(self, settings: ShowSettings, card_index: int) -> int:
        if not settings.tilt_degrees:
            return 0
        return settings.tilt_degrees if card_index % 2 == 0 else -settings.tilt_degrees

    def _display_card(self, card, progress, settings: ShowSettings, card_index=0):
        f = self.form
        f.label_HSK.setText(settings.word_source_label)
        f.label_number.setText(str(card.number))
        f.label_pinyin.setText(card.pinyin if settings.show_pinyin else '')
        f.label_translation.setText(card.translation if settings.show_translation else '')
        f.label_phrase.setText(card.phrase if settings.show_phrase else '')
        size = max(12, int(settings.font_size * min(UI_SCALE['x'], UI_SCALE['y'])))
        phrase_size = max(10, int(size * 0.5))
        f.label_phrase.setFont(QFont(APP_FONT, phrase_size))
        f.label_pinyin.setFont(QFont(APP_FONT, max(12, int(size * 0.35))))
        f.label_translation.setFont(QFont(APP_FONT, max(12, int(size * 0.35))))
        angle = self._tilt_for_card(settings, card_index)
        if settings.show_hieroglyph:
            set_hieroglyph_label(f.label_hieroglyph, card.hieroglyph, GLYPH_FONT, size, settings.color, angle)
        else:
            set_hieroglyph_label(f.label_hieroglyph, '', GLYPH_FONT, size, settings.color, 0)
        f.progressBar.setValue(max(0, min(100, progress)))
        if hasattr(f, 'label_show_progress_pct'):
            f.label_show_progress_pct.setText(f'{max(0, min(100, progress))}%')

    def _load_excel(self):
        if not self.session.user_id:
            self._show_error('Загрузка списка доступна только зарегистрированным пользователям.')
            return
        path, _ = QFileDialog.getOpenFileName(
            self.window, 'Загрузить список', '', 'Excel (*.xlsx *.xls)'
        )
        if not path:
            return
        ok, msg, list_id = import_excel(self.session.user_id, path, '')
        if ok:
            self.current_settings.custom_list_id = list_id
            self.current_settings.word_source = 'custom'
            self.current_settings.preset_name = msg
            self._load_settings_to_form(self.current_settings)
            self._update_profile_from_settings()
            self.settings_dirty = True
            self._show_success(f'Список загружен: {msg}')
        else:
            self._show_error(msg)

    def _open_template(self):
        path = ensure_template()
        if sys.platform == 'win32':
            os.startfile(path)
        else:
            subprocess.Popen(['xdg-open', path])

    def _refresh_admin(self):
        users = list_users()
        table = self.form.tableWidget_users
        table.setRowCount(len(users))
        for row_idx, user in enumerate(users):
            table.setItem(row_idx, 0, QTableWidgetItem(str(user['user_id'])))
            table.setItem(row_idx, 1, QTableWidgetItem(user['user_name']))
            table.setItem(row_idx, 2, QTableWidgetItem(str(user['login_count'])))
            table.setItem(row_idx, 3, QTableWidgetItem(f"{user['work_time_total']:.0f}"))
            table.setItem(row_idx, 4, QTableWidgetItem('да' if user['is_admin'] else 'нет'))

        lists = list_all_custom_lists()
        ltable = self.form.tableWidget_custom_lists
        ltable.setRowCount(len(lists))
        for row_idx, lst in enumerate(lists):
            ltable.setItem(row_idx, 0, QTableWidgetItem(str(lst['list_id'])))
            ltable.setItem(row_idx, 1, QTableWidgetItem(lst['user_name']))
            ltable.setItem(row_idx, 2, QTableWidgetItem(lst['name']))
            ltable.setItem(row_idx, 3, QTableWidgetItem(str(lst['card_count'])))

        metrics = get_admin_metrics(self.app_opens)
        self.form.label_admin_metrics.setText(
            f"Пользователей: {metrics['users_count']} | "
            f"Сохранённых наборов: {metrics['presets_count']} | "
            f"Запусков приложения: {metrics['app_opens']}"
        )

    def _admin_delete_user(self):
        row = self.form.tableWidget_users.currentRow()
        if row < 0:
            return
        user_id = int(self.form.tableWidget_users.item(row, 0).text())
        ok, msg = delete_user(user_id)
        if ok:
            self._refresh_admin()
        else:
            QMessageBox.warning(self.window, 'Ошибка', msg)

    def _admin_update_user(self):
        row = self.form.tableWidget_users.currentRow()
        if row < 0:
            return
        user_id = int(self.form.tableWidget_users.item(row, 0).text())
        new_name = self.form.lineEdit_admin_new_name.text()
        new_password = self.form.lineEdit_admin_new_password.text()
        ok, msg = update_user_credentials(user_id, new_name, new_password)
        if ok:
            self._refresh_admin()
            QMessageBox.information(self.window, 'Готово', msg)
        else:
            QMessageBox.warning(self.window, 'Ошибка', msg)

    def _admin_delete_list(self):
        row = self.form.tableWidget_custom_lists.currentRow()
        if row < 0:
            return
        list_id = int(self.form.tableWidget_custom_lists.item(row, 0).text())
        delete_custom_list(list_id)
        self._refresh_admin()

    def _tab_changed(self, index: int):
        if self.form.tabWidget.widget(index) == self.form.tab:
            settings = self._read_settings_from_form()
            if self.slideshow.is_paused or not self.slideshow.is_running:
                self.current_settings = settings
                self.slideshow.apply_settings(settings)
            elif not self.slideshow.is_running:
                self._display_card_from_settings(settings)

    def _confirm_exit_save(self) -> bool:
        if self.session.is_guest or not self.settings_dirty:
            return True
        reply = QMessageBox.question(
            self.window,
            'Выход',
            'Сохранить несохранённые настройки перед выходом?',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
        )
        if reply == QMessageBox.Cancel:
            return False
        if reply == QMessageBox.Yes:
            self._save_settings()
        return True

    def _exit_app(self):
        if self._confirm_exit_save():
            self.slideshow.stop()
            self.window.close()

    def _close_event(self, event):
        if self._confirm_exit_save():
            self.slideshow.stop()
            event.accept()
        else:
            event.ignore()

    def run(self):
        return self.app.exec_()


def _log_path() -> str:
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'Reading25_error.log')


def _show_fatal_error(message: str) -> None:
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, 'Reading25 — ошибка запуска', message)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, 'Reading25 — ошибка запуска', 0x10)
        except Exception:
            pass


def main():
    try:
        app = MainApp()
        sys.exit(app.run())
    except Exception:
        error_text = traceback.format_exc()
        try:
            with open(_log_path(), 'w', encoding='utf-8') as log_file:
                log_file.write(error_text)
        except Exception:
            pass
        _show_fatal_error(
            'Не удалось запустить приложение.\n\n'
            f'Подробности сохранены в:\n{_log_path()}\n\n'
            f'{error_text[-1200:]}'
        )
        sys.exit(1)


if __name__ == '__main__':
    main()
