from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup, QComboBox, QHBoxLayout, QLabel, QPushButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget, QCheckBox, QListWidget,
)

from src.ui.widgets.color_wheel import ColorWheel
from src.ui.widgets.slider_row import SliderRow
from src.ui.widgets.tone_curve_widget import ToneCurveWidget

PRESET_GROUPS = ("Color", "Creative", "B&W", "Portrait", "Landscape", "Vivid")
MIXER_COLORS = ("#d0d0d0", "#e23b3b", "#e07a2f", "#e2c04a", "#3caa55", "#3aa0c8", "#3a4ed0", "#c23ad0")
TONE_SPECS = (
    ("Exposure", -500, 500, 0),
    ("Contrast", -100, 100, 0),
    ("Highlights", -100, 100, 0),
    ("Shadows", -100, 100, 0),
    ("Whites", -100, 100, 0),
    ("Blacks", -100, 100, 0),
)
PRESENCE_SPECS = (
    ("Texture", -100, 100, 0),
    ("Clarity", -100, 100, 0),
    ("Dehaze", -100, 100, 0),
    ("Vibrance", -100, 100, 0),
    ("Saturation", -100, 100, 0),
)


class DevelopControls:
    def __init__(self) -> None:
        self.sliders: list[SliderRow] = []

    def slider(self, title: str, minimum: int, maximum: int, value: int = 0) -> SliderRow:
        row = SliderRow(title, minimum, maximum, value)
        self.sliders.append(row)
        return row

    def reset(self) -> None:
        for row in self.sliders:
            row.reset()

    def values(self) -> list[int]:
        return [row.value() for row in self.sliders]

    def restore(self, values: list[int]) -> None:
        for row, value in zip(self.sliders, values):
            row.set_value(value)


def basic_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_treatment_group())
    layout.addWidget(_balance_group(controls))
    _add_named_sliders(layout, controls, "Tone", TONE_SPECS)
    _add_named_sliders(layout, controls, "Presence", PRESENCE_SPECS)
    return panel


def tone_curve_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_curve_channels())
    layout.addWidget(ToneCurveWidget())
    layout.addWidget(_curve_group(controls))
    return panel


def color_mixer_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_mixer_group(controls))
    return panel


def color_grading_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_grading_group(controls))
    return panel


def detail_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    _add_named_sliders(layout, controls, "Sharpening", (
        ("Amount", 0, 150, 40),
        ("Radius", 5, 30, 10),
        ("Detail", 0, 100, 25),
        ("Masking", 0, 100, 0),
    ))
    _add_named_sliders(layout, controls, "Noise Reduction", (
        ("Luminance", 0, 100, 0),
        ("Detail ", 0, 100, 50),
        ("Contrast ", 0, 100, 0),
        ("Color", 0, 100, 25),
        ("Detail  ", 0, 100, 50),
        ("Smoothness", 0, 100, 50),
    ))
    return panel


def lens_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_profile_group())
    layout.addWidget(_manual_lens_group(controls))
    return panel


def transform_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_upright_group(controls))
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
    ))
    _add_named_sliders(layout, controls, "Grain", (
        ("Amount", 0, 100, 0),
        ("Size", 0, 100, 25),
        ("Roughness", 0, 100, 50),
    ))
    return panel


def calibration_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(_primary_group(controls, "Shadows", ("Shadows Tint",)))
    for primary in ("Red Primary", "Green Primary", "Blue Primary"):
        layout.addWidget(_primary_group(controls, primary, (f"{primary} Hue", f"{primary} Saturation")))
    return panel


def presets_panel(controls: DevelopControls) -> QWidget:
    panel = _panel()
    layout = _layout(panel)
    layout.addWidget(QLabel("None"))
    layout.addWidget(controls.slider("Amount", 0, 100, 0))
    layout.addWidget(_preset_tree())
    return panel


def history_list() -> QListWidget:
    widget = QListWidget()
    widget.addItem("Develop")
    widget.setFixedHeight(48)
    return widget


def collections_tree() -> QTreeWidget:
    tree = QTreeWidget()
    tree.setHeaderHidden(True)
    tree.addTopLevelItem(QTreeWidgetItem(["User Collections"]))
    tree.addTopLevelItem(QTreeWidgetItem(["Smart Collections"]))
    tree.setFixedHeight(72)
    return tree


def _add_named_sliders(layout: QVBoxLayout, controls: DevelopControls, title: str, specs: tuple) -> None:
    group, inner = _group(title)
    for name, minimum, maximum, value in specs:
        inner.addWidget(controls.slider(name.strip(), minimum, maximum, value))
    layout.addWidget(group)


def _panel() -> QWidget:
    return QWidget()


def _layout(panel: QWidget) -> QVBoxLayout:
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(4, 6, 4, 8)
    layout.setSpacing(8)
    return layout


def _group(title: str) -> tuple[QWidget, QVBoxLayout]:
    group = QWidget()
    group.setObjectName("developGroup")
    outer = QVBoxLayout(group)
    outer.setContentsMargins(1, 1, 1, 1)
    outer.setSpacing(0)
    outer.addWidget(_heading(title))
    return group, _group_body(outer)


def _group_body(outer: QVBoxLayout) -> QVBoxLayout:
    body = QWidget()
    body.setObjectName("developGroupBody")
    layout = QVBoxLayout(body)
    layout.setContentsMargins(6, 6, 6, 7)
    layout.setSpacing(2)
    outer.addWidget(body)
    return layout


def _heading(title: str) -> QLabel:
    label = QLabel(title)
    label.setObjectName("developHeading")
    return label


def _treatment_group() -> QWidget:
    group, layout = _group("Treatment")
    layout.addWidget(_treatment_row())
    return group


def _balance_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("WB")
    layout.addWidget(_white_balance_combo())
    layout.addWidget(controls.slider("Temp", 2000, 50000, 5500))
    layout.addWidget(controls.slider("Tint", -150, 150, 0))
    return group


def _treatment_row() -> QWidget:
    row, layout = _row()
    group = QButtonGroup(row)
    group.setExclusive(True)
    _add_toggles(layout, group)
    return row


def _add_toggles(layout: QHBoxLayout, group: QButtonGroup) -> None:
    for title, checked in (("Color", True), ("B&W", False)):
        layout.addWidget(_toggle(group, title, checked))


def _toggle(group: QButtonGroup, title: str, checked: bool) -> QPushButton:
    button = QPushButton(title)
    button.setCheckable(True)
    button.setChecked(checked)
    group.addButton(button)
    return button


def _white_balance_combo() -> QComboBox:
    combo = QComboBox()
    for name in ("As Shot", "Auto", "Daylight", "Cloudy", "Shade", "Tungsten", "Fluorescent", "Flash", "Custom"):
        combo.addItem(name)
    return combo


def _curve_channels() -> QWidget:
    row, layout = _row()
    for name in ("Parametric", "Point Curve", "RGB"):
        layout.addWidget(QPushButton(name))
    return row


def _curve_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Regions")
    for title in ("Highlights", "Lights", "Darks", "Shadows"):
        layout.addWidget(controls.slider(f"Curve {title}", -100, 100, 0))
    return group


def _mixer_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Adjust   HSL")
    layout.addWidget(_color_dots())
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
    group, layout = _group("Grading")
    layout.addWidget(_wheels())
    layout.addWidget(controls.slider("Blending", 0, 100, 50))
    layout.addWidget(controls.slider("Balance", -100, 100, 0))
    return group


def _profile_group() -> QWidget:
    group, layout = _group("Profile")
    layout.addWidget(QCheckBox("Remove Chromatic Aberration"))
    layout.addWidget(QCheckBox("Enable Profile Corrections"))
    return group


def _manual_lens_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Manual")
    layout.addWidget(controls.slider("Distortion", -100, 100, 0))
    layout.addWidget(controls.slider("Vignetting", -100, 100, 0))
    return group


def _upright_group(controls: DevelopControls) -> QWidget:
    group, layout = _group("Upright")
    layout.addWidget(_upright_row())
    _add_transform_sliders(layout, controls)
    layout.addWidget(QCheckBox("Constrain Crop"))
    return group


def _add_transform_sliders(layout: QVBoxLayout, controls: DevelopControls) -> None:
    titles = ("Vertical", "Horizontal", "Rotate", "Aspect", "Scale", "X Offset", "Y Offset")
    for title in titles:
        layout.addWidget(controls.slider(title, -100, 100, 0))


def _primary_group(controls: DevelopControls, title: str, names: tuple[str, ...]) -> QWidget:
    group, layout = _group(title)
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
