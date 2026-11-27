from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QSizePolicy, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from src.develop.crop_settings import MAX_ANGLE, MAX_EDGE
from src.develop.white_balance import CHOICES
from src.ui.density import Density
from src.ui.widgets.color_wheel import ColorWheel
from src.ui.widgets.develop_group import DevelopGroup
from src.ui.widgets.etched_divider import EtchedDivider
from src.ui.widgets.slider_row import SliderRow
from src.ui.widgets.tone_curve_widget import ToneCurveWidget

PRESET_GROUPS = ("Color", "Creative", "B&W", "Portrait", "Landscape", "Vivid")
MIXER_COLORS = ("#d0d0d0", "#e23b3b", "#e07a2f", "#e2c04a", "#3caa55", "#3aa0c8", "#3a4ed0", "#c23ad0")
TONE_UPPER = (
    ("Exposure", -500, 500, 0),
    ("Contrast", -100, 100, 0),
)
TONE_LOWER = (
    ("Highlights", -100, 100, 0),
    ("Shadows", -100, 100, 0),
    ("Whites", -100, 100, 0),
    ("Blacks", -100, 100, 0),
)
TONE_SPECS = TONE_UPPER + TONE_LOWER
PRESENCE_UPPER = (
    ("Texture", -100, 100, 0),
    ("Clarity", -100, 100, 0),
    ("Dehaze", -100, 100, 0),
)
PRESENCE_LOWER = (
    ("Vibrance", -100, 100, 0),
    ("Saturation", -100, 100, 0),
)
PRESENCE_SPECS = PRESENCE_UPPER + PRESENCE_LOWER


class DevelopControls:
    def __init__(self) -> None:
        self.sliders: list[SliderRow] = []
        self.crop_lock = QCheckBox("Lock aspect ratio")
        self.white_balance = _white_balance_combo()

    def slider(self, title: str, minimum: int, maximum: int, value: int = 0) -> SliderRow:
        row = SliderRow(title, minimum, maximum, value)
        self.sliders.append(row)
        return row

    def reset(self) -> None:
        for row in self.sliders:
            row.reset()
        self.crop_lock.setChecked(False)

    def values(self) -> list[int]:
        return [row.value() for row in self.sliders]

    def restore(self, values: list[int]) -> None:
        for row, value in zip(self.sliders, values):
            row.set_value(value)

    def first_named(self, titles: tuple[str, ...]) -> list[SliderRow]:
        found: dict[str, SliderRow] = {}
        for row in self.sliders:
            if row.title in titles:
                found.setdefault(row.title, row)
        return list(found.values())

    def named_values(self, titles: tuple[str, ...]) -> dict[str, int]:
        return {row.title: row.value() for row in self.first_named(titles)}

    def restore_named(self, titles: tuple[str, ...], values: dict[str, int]) -> None:
        for row in self.first_named(titles):
            row.set_value(values.get(row.title, row.default))


def basic_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_treatment_group())
    layout.addWidget(_balance_group(controls))
    layout.addWidget(_clustered_group(controls, "Tone", TONE_UPPER, TONE_LOWER))
    layout.addWidget(_clustered_group(controls, "Presence", PRESENCE_UPPER, PRESENCE_LOWER))
    _finish(layout)
    return panel


def tone_curve_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_padded(_curve_channels()))
    layout.addWidget(_padded(ToneCurveWidget()))
    layout.addWidget(_curve_group(controls))
    _finish(layout)
    return panel


def color_mixer_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_mixer_group(controls))
    _finish(layout)
    return panel


def color_grading_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_grading_group(controls))
    _finish(layout)
    return panel


def detail_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    _add_named_sliders(layout, controls, "Sharpening", (
        ("Amount", 0, 150, 40),
        ("Radius", 5, 30, 10),
        ("Detail", 0, 100, 25),
        ("Masking", 0, 100, 0),
    ), show_divider=False)
    _add_named_sliders(layout, controls, "Noise Reduction", (
        ("Luminance", 0, 100, 0),
        ("Detail ", 0, 100, 50),
        ("Contrast ", 0, 100, 0),
        ("Color", 0, 100, 25),
        ("Detail  ", 0, 100, 50),
        ("Smoothness", 0, 100, 50),
    ), show_divider=True)
    _finish(layout)
    return panel


def lens_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_profile_group())
    layout.addWidget(_manual_lens_group(controls))
    _finish(layout)
    return panel


def transform_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_upright_group(controls))
    _finish(layout)
    return panel


def crop_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    for title in ("Left", "Top", "Right", "Bottom"):
        layout.addWidget(controls.slider(title, 0, MAX_EDGE, 0))
    layout.addWidget(controls.slider("Angle", -MAX_ANGLE, MAX_ANGLE, 0))
    layout.addWidget(_padded(controls.crop_lock))
    _finish(layout)
    return panel


def effects_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    _add_named_sliders(layout, controls, "Post-Crop Vignetting", (
        ("Amount", -100, 100, 0),
        ("Midpoint", 0, 100, 50),
        ("Roundness", -100, 100, 0),
        ("Feather", 0, 100, 50),
        ("Highlights", 0, 100, 0),
    ), show_divider=False)
    _add_named_sliders(layout, controls, "Grain", (
        ("Amount", 0, 100, 0),
        ("Size", 0, 100, 25),
        ("Roughness", 0, 100, 50),
    ), show_divider=True)
    _finish(layout)
    return panel


def calibration_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_primary_group(controls, "Shadows", ("Shadows Tint",), show_divider=False))
    for primary in ("Red Primary", "Green Primary", "Blue Primary"):
        layout.addWidget(_primary_group(controls, primary, (f"{primary} Hue", f"{primary} Saturation")))
    _finish(layout)
    return panel


def presets_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_padded(QLabel("Preset: None")))
    amount = controls.slider("Amount", 0, 100, 0)
    amount.set_compact_caption(46)
    layout.addWidget(amount)
    layout.addWidget(EtchedDivider("major"))
    layout.addWidget(_preset_tree())
    _finish(layout)
    return panel


def history_list() -> QListWidget:
    widget = QListWidget()
    widget.setMinimumHeight(72)
    widget.setMaximumHeight(160)
    return widget


def collections_tree() -> QTreeWidget:
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.addTopLevelItem(QTreeWidgetItem(["User Collections"]))
    tree.addTopLevelItem(QTreeWidgetItem(["Smart Collections"]))
    tree.setFixedHeight(72)
    return tree


def _clustered_group(controls: DevelopControls, title: str, upper: tuple, lower: tuple) -> QWidget:
    group, inner = _group(title, show_divider=True)
    _append_specs(inner, controls, upper)
    inner.addWidget(EtchedDivider("soft"))
    _append_specs(inner, controls, lower)
    return group


def _add_named_sliders(
    layout: QVBoxLayout,
    controls: DevelopControls,
    title: str,
    specs: tuple,
    show_divider: bool = True,
) -> None:
    group, inner = _group(title, show_divider=show_divider)
    _append_specs(inner, controls, specs)
    layout.addWidget(group)


def _append_specs(inner: QVBoxLayout, controls: DevelopControls, specs: tuple) -> None:
    for name, minimum, maximum, value in specs:
        inner.addWidget(controls.slider(name.strip(), minimum, maximum, value))


def _panel() -> QWidget:
    panel = QWidget()
    panel.setObjectName("panelBody")
    panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
    return panel


def _layout(panel: QWidget) -> QVBoxLayout:
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(0, 2, 0, 4)
    layout.setSpacing(0)
    return layout


def _finish(layout: QVBoxLayout) -> None:
    return


def _group(title: str, show_divider: bool = True, align_to_track: bool = True) -> tuple[QWidget, QVBoxLayout]:
    group = DevelopGroup(title, show_divider=show_divider, align_to_track=align_to_track)
    return group, group.body_layout()


def _padded(widget: QWidget) -> QWidget:
    wrap = QWidget()
    wrap.setObjectName("developRow")
    layout = QHBoxLayout(wrap)
    layout.setContentsMargins(Density.SLIDER_ROW_MARGIN_X, 2, Density.SLIDER_ROW_MARGIN_X, 2)
    layout.setSpacing(4)
    layout.addWidget(widget)
    return wrap


def _treatment_group() -> QWidget:
    group, layout = _group("Treatment", show_divider=False)
    layout.addWidget(_padded(_treatment_row()))
    return group


def _balance_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("WB", show_divider=True)
    layout.addWidget(_wb_row(controls.white_balance))
    layout.addWidget(controls.slider("Temp", 2000, 50000, 5500))
    layout.addWidget(controls.slider("Tint", -150, 150, 0))
    return group


def _wb_row(combo: QComboBox) -> QWidget:
    row = QWidget()
    row.setObjectName("developRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(Density.SLIDER_ROW_MARGIN_X, 0, Density.SLIDER_ROW_MARGIN_X, 4)
    layout.setSpacing(Density.SLIDER_ROW_SPACING)
    spacer = QLabel("")
    spacer.setFixedWidth(Density.SLIDER_CAPTION_WIDTH)
    layout.addWidget(spacer)
    layout.addWidget(combo, 1)
    return row


def _treatment_row() -> QWidget:
    row, layout = _row()
    group = QButtonGroup(row)
    group.setExclusive(True)
    _add_toggles(layout, group)
    return row


def _add_toggles(layout: QHBoxLayout, group: QButtonGroup) -> None:
    for title, checked in (("Color", True), ("B&&W", False)):
        layout.addWidget(_toggle(group, title, checked))


def _toggle(group: QButtonGroup, title: str, checked: bool) -> QPushButton:
    button = QPushButton(title)
    button.setCheckable(True)
    button.setChecked(checked)
    group.addButton(button)
    return button


def _white_balance_combo() -> QComboBox:
    combo = QComboBox()
    combo.addItems(list(CHOICES))
    return combo


def _curve_channels() -> QWidget:
    row, layout = _row()
    for name in ("Parametric", "Point Curve", "RGB"):
        layout.addWidget(QPushButton(name))
    return row


def _curve_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Regions", show_divider=True)
    for title in ("Highlights", "Lights", "Darks", "Shadows"):
        layout.addWidget(controls.slider(f"Curve {title}", -100, 100, 0))
    return group


def _mixer_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Adjust   HSL", show_divider=False, align_to_track=False)
    layout.addWidget(_padded(_color_dots()))
    _add_mixer_sliders(layout, controls)
    return group


def _add_mixer_sliders(layout: QVBoxLayout, controls: DevelopControls) -> None:
    for title in ("Hue", "Saturation", "Luminance"):
        layout.addWidget(controls.slider(title, -100, 100, 0))


def _color_dots() -> QWidget:
    row, layout = _row()
    for color in MIXER_COLORS:
        layout.addWidget(_dot(color))
    return row


def _dot(color: str) -> QPushButton:
    button = QPushButton()
    button.setFixedSize(16, 16)
    button.setStyleSheet(f"background-color: {color}; border-radius: 8px; border: 1px solid rgb(20, 20, 20);")
    return button


def _grading_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Grading", show_divider=False, align_to_track=False)
    layout.addWidget(_padded(_wheels()))
    layout.addWidget(controls.slider("Blending", 0, 100, 50))
    layout.addWidget(controls.slider("Balance", -100, 100, 0))
    return group


def _profile_group() -> QWidget:
    group, layout = _group("Profile", show_divider=False, align_to_track=False)
    layout.addWidget(_padded(QCheckBox("Remove Chromatic Aberration")))
    layout.addWidget(_padded(QCheckBox("Enable Profile Corrections")))
    return group


def _manual_lens_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Manual", show_divider=True)
    layout.addWidget(controls.slider("Distortion", -100, 100, 0))
    layout.addWidget(controls.slider("Vignetting", -100, 100, 0))
    return group


def _upright_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Upright", show_divider=False, align_to_track=False)
    layout.addWidget(_padded(_upright_row()))
    _add_transform_sliders(layout, controls)
    layout.addWidget(_padded(QCheckBox("Constrain Crop")))
    return group


def _add_transform_sliders(layout: QVBoxLayout, controls: DevelopControls) -> None:
    titles = ("Vertical", "Horizontal", "Rotate", "Aspect", "Scale", "X Offset", "Y Offset")
    for title in titles:
        layout.addWidget(controls.slider(title, -100, 100, 0))


def _primary_group(
    controls: DevelopControls,
    title: str,
    names: tuple[str, ...],
    show_divider: bool = True,
) -> QWidget:
    group, layout = _group(title, show_divider=show_divider)
    for name in names:
        layout.addWidget(controls.slider(name, -100, 100, 0))
    return group


def _wheels() -> QWidget:
    row, layout = _row()
    for title in ("Shadows", "Midtones", "Highlights"):
        layout.addWidget(ColorWheel(title))
    return row


def _upright_row() -> QWidget:
    row, layout = _row()
    for title in ("Off", "Auto", "Level", "Vertical", "Full"):
        layout.addWidget(QPushButton(title))
    return row


def _row() -> tuple[QWidget, QHBoxLayout]:
    row = QWidget()
    row.setObjectName("developRow")
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(4)
    return row, layout


def _preset_tree() -> QTreeWidget:
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    for name in PRESET_GROUPS:
        item = QTreeWidgetItem([name])
        item.addChild(QTreeWidgetItem(["None"]))
        tree.addTopLevelItem(item)
    tree.setMinimumHeight(120)
    return tree
