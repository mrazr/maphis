import colorsys
import typing

import PySide2
from PySide2.QtCore import Qt, QTimer, Signal
from PySide2.QtGui import QColor, QPainter, QPixmap, QValidator
from PySide2.QtWidgets import QWidget, QColorDialog, QDialogButtonBox, QDialog

from colorsys import rgb_to_hsv, hsv_to_rgb

from arthropod_describer.common.label_hierarchy import Node
from arthropod_describer.common.state import State
from arthropod_describer.ui_color_tolerance_dialog import Ui_ColorToleranceDialog


class ColorToleranceDialog(QDialog):
    def __init__(self, state: State, parent: typing.Optional[PySide2.QtWidgets.QWidget] = None,
                 f: PySide2.QtCore.Qt.WindowFlags = Qt.WindowFlags()):
        super().__init__(parent, f)
        self.state: State = state
        self.ui = Ui_ColorToleranceDialog()
        self.ui.setupUi(self)
        self._lblColor_pixmap = QPixmap(self.ui.lblColor.minimumSize())

        self._lblVTolerancePreview_pixmap = QPixmap(self.ui.lblVTolerancePreview.minimumSize())
        self._lblHSTolerancePreview_pixmap = QPixmap(self.ui.lblHSTolerancePreview.minimumSize())

        self._selected_color: QColor = QColor(255, 255, 255)
        self.ui.btnSetColor.clicked.connect(self._pick_color)
        self._parent_node: typing.Optional[Node] = None
        self.ui.buttonBox.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        self.ui.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.ui.spinBoxHueTolerance.valueChanged.connect(self._update_tolerance_preview)
        self.ui.spinBoxSaturationTolerance.valueChanged.connect(self._update_tolerance_preview)
        self.ui.spinBoxValueTolerance.valueChanged.connect(self._update_tolerance_preview)
        self.ui.sliderPreviewV.valueChanged.connect(self._update_tolerance_preview)

        self._float_v = 0
        self._animation_speed = 0.02
        self._animation_direction = 1
        self._animation_timer = QTimer()
        self._animation_timer.setInterval(50)
        self._animation_timer.timeout.connect(self._update_animation)

        self.setWindowModality(Qt.ApplicationModal)

    def _update_tolerance_preview(self):
        # Display the range of colors that falls within the selected tolerances.
        # 2D projection with a Value slider (whose range also reflects the selected range),

        selected_hue = self._selected_color.hue()
        selected_saturation = self._selected_color.saturation()
        selected_value = self._selected_color.value()
        self.ui.lblSelectedColor.setText(f"HSV == ({selected_hue}, {selected_saturation}, {selected_value})")

        min_hue = selected_hue - self.ui.spinBoxHueTolerance.value() + 360  # Add 360 to ensure we never use negative values, but `min_hue < max_hue` always holds. Later, using `% 360` may be required.
        max_hue = selected_hue + self.ui.spinBoxHueTolerance.value() + 360  # Add 360 to ensure we never use negative values, but `min_hue < max_hue` always holds. Later, using `% 360` may be required.
        min_saturation = max(0, selected_saturation - self.ui.spinBoxSaturationTolerance.value())
        max_saturation = min(255, selected_saturation + self.ui.spinBoxSaturationTolerance.value())
        min_value = max(0, selected_value - self.ui.spinBoxValueTolerance.value())
        max_value = min(255, selected_value + self.ui.spinBoxValueTolerance.value())
        self.ui.lblSelectedRange.setText(f"HSV range == ({min_hue}..{max_hue}, {min_saturation}..{max_saturation}, {min_value}..{max_value})")

        self.ui.sliderPreviewV.setRange(min_value, max_value)
        if not self.ui.checkBoxAnimate.isChecked():
            self._float_v = self.ui.sliderPreviewV.value()

        self._lblColor_pixmap.fill(self._selected_color)
        self.ui.lblColor.setPixmap(self._lblColor_pixmap)

        # 1D gradient V
        painter = QPainter(self._lblVTolerancePreview_pixmap)
        for x in range(self._lblVTolerancePreview_pixmap.width()):
            current_color = QColor()
            current_color.setHsv(255, 0, min_value + (max_value - min_value) * x / self._lblVTolerancePreview_pixmap.width())
            painter.setPen(current_color)
            painter.drawLine(x, 0, x, self._lblVTolerancePreview_pixmap.height())
        self.ui.lblVTolerancePreview.setPixmap(self._lblVTolerancePreview_pixmap)

        # 2D gradient HS
        painter = QPainter(self._lblHSTolerancePreview_pixmap)
        for x in range(self._lblHSTolerancePreview_pixmap.width()):
            for y in range(self._lblHSTolerancePreview_pixmap.height()):
                current_color = QColor()
                current_color.setHsv(min_hue + (max_hue - min_hue) * x / self._lblHSTolerancePreview_pixmap.width(),
                                     max_saturation - (max_saturation - min_saturation) * y / self._lblHSTolerancePreview_pixmap.height(),
                                     self.ui.sliderPreviewV.value()
                                     )
                painter.setPen(current_color)
                painter.drawPoint(x, y)
        self.ui.lblHSTolerancePreview.setPixmap(self._lblHSTolerancePreview_pixmap)

    def _update_animation(self):
        if not self.ui.checkBoxAnimate.isChecked() or self.ui.sliderPreviewV.minimum() >= self.ui.sliderPreviewV.maximum():
            return

        # Move the V slider, change the direction when at the beginning/end.
        self._float_v = self._float_v + (self.ui.sliderPreviewV.maximum() - self.ui.sliderPreviewV.minimum()) * self._animation_speed * self._animation_direction
        if self._float_v < self.ui.sliderPreviewV.minimum() or self._float_v > self.ui.sliderPreviewV.maximum():
            self._animation_direction = -self._animation_direction
            self._float_v = min(self.ui.sliderPreviewV.maximum(), max(self.ui.sliderPreviewV.minimum(), self._float_v))

        self.ui.sliderPreviewV.setValue(round(self._float_v))

        self._update_tolerance_preview()

    def _pick_color(self):
        color = QColorDialog.getColor(initial=self._selected_color)
        if color.isValid():
            self._selected_color = color
            self._update_tolerance_preview()

    def accept(self):
        super().accept()
        self._animation_timer.stop()

    def reject(self):
        super().reject()
        self._animation_timer.stop()

    def get_color_and_tolerances(self):
        self._update_tolerance_preview()
        self._animation_timer.start()

        if self.exec_() == QDialog.Accepted:
            # Return the selected color and tolerances
            print(f"returning {self._selected_color}, {self.ui.spinBoxHueTolerance.value()}, {self.ui.spinBoxSaturationTolerance.value()}, {self.ui.spinBoxValueTolerance.value()}")
            return self._selected_color, self.ui.spinBoxHueTolerance.value(), self.ui.spinBoxSaturationTolerance.value(), self.ui.spinBoxValueTolerance.value()
        else:
            # Return no color and tolerances
            print(f"returning {None}, {0}, {0}, {0}")
            return None, 0, 0, 0
