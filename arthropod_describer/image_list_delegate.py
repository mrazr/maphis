import typing
import importlib.resources
import typing

import PySide2
from PySide2.QtCore import Qt, QRect, QSize, QPoint, Signal, QRectF, QMarginsF, QModelIndex
from PySide2.QtGui import QImage, QIcon, QPixmap, QBrush, QColor, QFont
from PySide2.QtWidgets import QStyledItemDelegate, QApplication, QStyleOptionButton, QStyle, QListView, \
    QStyleOptionViewItem, QAbstractItemView, QStyleOptionFrame

from arthropod_describer.thumbnail_storage import ThumbnailDelegate, ThumbnailStorage_


class ImageListDelegate(ThumbnailDelegate):
    tags_rect: QRect = QRect()
    tag_rects: typing.Dict[int, QRect] = {}

    def __init__(self, thumbnail_storage: ThumbnailStorage_, parent: typing.Optional[PySide2.QtCore.QObject] = None):
        super().__init__(thumbnail_storage, parent)

        self.mouse_pos: QPoint = QPoint()
        self.icon_size = QSize(20, 20)
        with importlib.resources.path('resources', 'refresh.png') as path:
            cw = QImage(str(path)).scaledToWidth(self.icon_size.width(), Qt.TransformationMode.SmoothTransformation)
            self.cw_icon = QIcon(QPixmap.fromImage(cw))
            self.ccw_icon = QIcon(QPixmap.fromImage(cw.mirrored(False, True)))
        with importlib.resources.path('resources', 'resize.png') as path:
            rs = QImage(str(path)).scaledToWidth(self.icon_size.width(), Qt.SmoothTransformation)
            self.resize_icon = QIcon(QPixmap.fromImage(rs))

        with importlib.resources.path('resources', 'floppy-disk.png') as path:
            self.save_img = QImage(str(path)).scaledToWidth(self.icon_size.width(), Qt.SmoothTransformation)
            self.save_icon = QIcon(QPixmap.fromImage(self.save_img))

    def _paint(self, painter: PySide2.QtGui.QPainter, option: QStyleOptionViewItem,
               index: PySide2.QtCore.QModelIndex):
        painter.save()
        font_metrics = painter.fontMetrics()
        img_name = index.data(Qt.DisplayRole)
        quality_color = QColor(220, 220, 220)

        rect = option.rect
        bottom_bar = QRectF(0, rect.bottom() - 32,
                            rect.width(), 32)

        tags: typing.Set[str] = index.data(Qt.UserRole + 9)

        if len(tags) == 0:
            tags = {'no tags'}
            tag_style = QFont.StyleItalic
        else:
            tag_style = QFont.StyleNormal

        tags_str = ', '.join(list(sorted(tags)))
        tags_str_bbox = font_metrics.boundingRect(tags_str)
        tags_str_width = tags_str_bbox.width()

        text_rect = QRectF(0, rect.bottom() - 32,
                           rect.width() * 0.45, 32)
        img_name_elided = font_metrics.elidedText(img_name, Qt.ElideRight, text_rect.width())
        text_bbox = font_metrics.boundingRect(img_name_elided)
        tags_rect_width = min(rect.width() * 0.45, tags_str_width * 1.2)
        tags_rect = QRectF(rect.width() - tags_rect_width, rect.bottom() - 32,
                           tags_rect_width, 32)

        image_name_width = text_bbox.width()

        painter.setRenderHint(painter.SmoothPixmapTransform, True)
        quality_color = QColor(00, 00, 00, 200) if quality_color is None else quality_color
        painter.fillRect(bottom_bar, quality_color)
        painter.setPen(QColor(0, 0, 0, 255))
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, img_name_elided)
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        if option.state & QStyle.State_Selected:
            color = option.palette.highlight().color()
            color.setAlpha(100)
            painter.fillRect(rect, color)

        tags_str_elided = font_metrics.elidedText(tags_str, Qt.ElideRight, tags_rect.width())
        painter.setPen(QColor(80, 80, 80, 255))
        left_margin_shift = -3
        right_margin_shift = -2
        tags_rect_frame = tags_rect.marginsRemoved(QMarginsF(0, 3, -right_margin_shift, 3))
        tags_rect_frame = tags_rect_frame.marginsAdded(QMarginsF(-left_margin_shift, 0, 0, 0))

        self.tag_rects[index.row()] = tags_rect_frame.toRect()

        painter.drawRect(tags_rect_frame)
        font = painter.font()
        font.setStyle(tag_style)
        painter.setFont(font)
        painter.drawText(tags_rect_frame, Qt.AlignCenter, tags_str_elided)

        opt = QStyleOptionFrame()
        opt.rect = QRect(text_rect.toRect())
        opt.rect.x = opt.rect.x() + text_rect.width() * 0.5
        opt.features = QStyleOptionFrame.None_

        opt.state = QStyle.State_Enabled | QStyle.State_HasFocus

        style = QApplication.style()
        style.drawControl(QStyle.CE_ShapedFrame, opt, painter)

        painter.restore()

    def paint(self, painter: PySide2.QtGui.QPainter, option: QStyleOptionViewItem,
              index: PySide2.QtCore.QModelIndex):
        super().paint(painter, option, index)
        approval_count, out_of = index.data(Qt.UserRole + 4)
        self._paint(painter, option, index)
        painter.save()
        painter.setBrush(QBrush(QColor(0, 150, 0)))
        for i in range(approval_count):
            painter.drawEllipse(QPoint(i * 12 + 10, option.rect.y() + 10), 5, 5)
        painter.setBrush(QBrush(QColor(200, 150, 0)))
        for i in range(approval_count, out_of):
            painter.drawEllipse(QPoint(i * 12 + 10, option.rect.y() + 10), 4, 4)
        if not index.data(Qt.UserRole + 5):
            painter.fillRect(option.rect, QBrush(QColor(200, 200, 200, 150)))
        if index.data(Qt.UserRole + 6):
            painter.restore()
            painter.save()
            rect = QRect(option.rect.bottomLeft() - QPoint(-5, self.icon_size.height() + 32 + 2),
                         self.icon_size)
            #painter.drawImage(rect, self.save_img)
            style = QApplication.style()

            opt = QStyleOptionButton()
            #opt.rect = QRect(option.rect.topRight(), QSize(self.icon_size.width() + 12, self.icon_size.height() + 12))
            opt.rect = QRect(QPoint(5, option.rect.top() + 160 - 28 - 32 - 2), QSize(28, 28))

            opt.state = QStyle.State_Active | QStyle.State_Enabled
            #if opt.rect.contains(self.mouse_pos):
            #    opt.state = opt.state | QStyle.State_MouseOver

            opt.icon = self.save_icon
            opt.iconSize = self.icon_size

            style.drawControl(QStyle.CE_PushButton, opt, painter)
        painter.restore()
        #if False and option.state & QStyle.State_MouseOver > 0:
        #    style = QApplication.style()
        #    opt = QStyleOptionButton()
        #    opt.rect = QRect(option.rect.topRight(), QSize(self.icon_size.width() + 12, self.icon_size.height() + 12))
        #    opt.rect = opt.rect.translated(-3 * opt.rect.width(), 4)

        #    opt.state = QStyle.State_Active | QStyle.State_Enabled
        #    if opt.rect.contains(self.mouse_pos):
        #        opt.state = opt.state | QStyle.State_MouseOver

        #    opt.icon = self.cw_icon
        #    opt.iconSize = self.icon_size

        #    style.drawControl(QStyle.CE_PushButton, opt, painter)

        #    opt.rect = opt.rect.translated(self.icon_size.width() + 11, 0)
        #    opt.state = QStyle.State_Active | QStyle.State_Enabled
        #    if opt.rect.contains(self.mouse_pos):
        #        opt.state = opt.state | QStyle.State_MouseOver

        #    opt.icon = self.ccw_icon

        #    style.drawControl(QStyle.CE_PushButton, opt, painter)

        #    opt.rect = opt.rect.translated(self.icon_size.width() + 11, 0)
        #    opt.state = QStyle.State_Active | QStyle.State_Enabled
        #    if opt.rect.contains(self.mouse_pos):
        #        opt.state = opt.state | QStyle.State_MouseOver
        #    opt.icon = self.resize_icon
        #    style.drawControl(QStyle.CE_PushButton, opt, painter)


class ImageListView(QListView):
    view_left = Signal()
    show_tag_ui = Signal(QModelIndex)
    hide_tag_ui = Signal(QModelIndex)

    def __init__(self, parent: typing.Optional[PySide2.QtWidgets.QWidget] = ...):
        super().__init__(parent)
        self.delegate: typing.Optional[ImageListDelegate] = None

    def initialize(self, delegate: ImageListDelegate):
        self.setMouseTracking(True)
        self.delegate = delegate
        self.setItemDelegate(self.delegate)

    def leaveEvent(self, event:PySide2.QtCore.QEvent):
        self.view_left.emit()

    def mousePressEvent(self, event: PySide2.QtGui.QMouseEvent):
        if event.modifiers() & Qt.ControlModifier > 0:
            self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        else:
            self.setSelectionMode(QAbstractItemView.SingleSelection)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, e: PySide2.QtGui.QMouseEvent):
        super(ImageListView, self).mouseMoveEvent(e)
        index = self.indexAt(e.pos())
        if not index.isValid():
            return
        if self.delegate.tag_rects[index.row()].contains(e.pos()):
            self.show_tag_ui.emit(index)
        else:
            self.hide_tag_ui.emit(index)


