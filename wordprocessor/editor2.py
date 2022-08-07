from PyQt5.QtCore import QObject, QSizeF, QRectF, Qt, QPointF
from PyQt5.QtGui import QTextObjectInterface, QTextFormat, QTextCharFormat, QTextDocument, QPainter, QPixmap, QPageSize, \
    QBrush, QColor, QTextCursor
from PyQt5.QtWidgets import QTextEdit, QWidget, QVBoxLayout, QPushButton, QLabel, QGraphicsView, QGraphicsScene, \
    QGraphicsRectItem, QSizeGrip


class View(QGraphicsView):
    def __init__(self, parent=None):
        super(View, self).__init__(parent)
        self.imageHandler = ImageHandler(QRectF(), self)
        self.sizeGripHandler = ImageSizeGrip(QRectF(), self)
        self.sizeGripHandler.setParentItem(self.imageHandler)

    def keyPressEvent(self, event):
        self.scene().removeItem(self.imageHandler)
        self.scene().removeItem(self.sizeGripHandler)
        return QGraphicsView.keyPressEvent(self, event)


class Scene(QGraphicsScene):
    def __init__(self, parent=None):
        super(Scene, self).__init__(parent)
        self.setBackgroundBrush(QBrush(Qt.gray, Qt.SolidPattern))

    def addItem(self, item):
        if item not in self.items():
            super(Scene, self).addItem(item)

    def removeItem(self, item):
        if item in self.items():
            super(Scene, self).removeItem(item)


class ImageHandler(QGraphicsRectItem):
    def __init__(self, rect=QRectF(), view=None):
        super(ImageHandler, self).__init__(rect)
        self.view = view
        self._color = QColor(200, 100, 200, 100)

    def paint(self, painter, option, widget):
        painter.setBrush(QBrush(self._color, Qt.Dense1Pattern))
        painter.drawRect(self.rect())

    def boundingRect(self):
        return self.rect()


class ImageSizeGrip(ImageHandler):

    def __init__(self, rect=QRectF(), view=None):
        super(ImageSizeGrip, self).__init__(rect, view)
        self.start_pos = QPointF()
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setAcceptHoverEvents(True)
        self.color = QColor(120, 243, 80, 200)
        self.setFlags(QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemIsMovable)
        self.grab_textobject = False
        self.find_cursor = QTextCursor()
        self.find_position = 0

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.scenePos()
        cur = self.parentItem().inlinewidget.parent().cursorForPosition(
            self.parentItem().inlinewidget.geometry().bottomRight())
        doc = self.parentItem().inlinewidget.parent().document()
        # chr(0xfffc) is probably located in the previous positions because ImageSizeGrip is positioned at the rightbottom of the picture.
        self.find_cursor = doc.find(chr(0xfffc), cur.position(), doc.FindBackward)
        self.find_position = self.find_cursor.position()
        self.find_cursor.clearSelection()
        self.find_cursor.setPosition(self.find_position, self.find_cursor.MoveAnchor)
        movable = self.find_cursor.movePosition(self.find_cursor.Left, self.find_cursor.KeepAnchor)
        return QGraphicsRectItem.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        parentItem = self.parentItem()
        parentItem.prepareGeometryChange()
        rect = QRectF()
        rect.setCoords(parentItem.rect().topLeft().x(), parentItem.rect().topLeft().y(), event.scenePos().x(),
                       event.scenePos().y())
        parentItem.setRect(rect)
        parentItem.inlinewidget.resize(rect.size().toSize())
        parentItem.update()
        # I think it is better you load initial pixmap item. Especially jpg is subject to be broken by size change.
        pixmap = QPixmap(r"picture.jpg")
        pixmap = pixmap.scaled(rect.size().toSize())
        parentItem.inlinewidget.pixmap().swap(pixmap)
        self.find_cursor.clearSelection()
        self.find_cursor.setPosition(self.find_position, self.find_cursor.MoveAnchor)
        movable = self.find_cursor.movePosition(self.find_cursor.Left, self.find_cursor.KeepAnchor)
        if self.find_cursor.selectedText() == chr(0xfffc) and len(self.find_cursor.selectedText()) == 1:
            self.find_cursor.setKeepPositionOnInsert(True)
            self.find_cursor.deleteChar()
            inLineWidget = InLineWidget()
            inLineWidget.setGeometry(parentItem.rect().toRect())
            parentItem.inlinewidget.parent().insert_text_object(self.find_cursor, inLineWidget)
            self.find_cursor.setKeepPositionOnInsert(False)
            parentItem.inlinewidget.parent()._trigger_obj_char_rescan()
        return QGraphicsRectItem.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.view.scene().removeItem(self.parentItem())
        self.view.scene().removeItem(self)
        self.view.scene().update()
        return QGraphicsRectItem.mouseReleaseEvent(self, event)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.PointingHandCursor)
        return QGraphicsRectItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        return QGraphicsRectItem.hoverLeaveEvent(self, event)


class InLineWidget(QLabel):
    def __init__(self, parent=None):
        super(InLineWidget, self).__init__(parent)
        self.view = None
        # Now, you are using only one picture. but if you set it as variable, you can set any pixmap item.
        p = QPixmap(r"picture.jpg")
        self.setPixmap(p)
        self.setMinimumSize(1, 1)
        # self.setScaledContents(False)
        # self.setWindowFlags(Qt.SubWindow)
        sizeGrip = QSizeGrip(self)
        sizeGrip.setWindowFlags(Qt.SubWindow)
        # self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # self.setScaledContents(True)
        self.setFrameStyle(3)
        # self.setFixedSize(500, 600)
        # self.setMinimumSize(10, 10)
        # self.setStyleSheet("background-color: rgba(0, 0, 0, 40%)")
        # self.setAlignment(Qt.AlignCenter)

    def mousePressEvent(self, event):
        self.view.imageHandler.setRect(QRectF(self.geometry()))
        self.view.sizeGripHandler.setRect(QRectF(self.view.imageHandler.rect().bottomRight(), QSizeF(10, 10)))
        self.view.sizeGripHandler.setPos(0, 0)
        self.view.scene().addItem(self.view.imageHandler)
        self.view.scene().addItem(self.view.sizeGripHandler)
        self.view.imageHandler.inlinewidget = self
        return QLabel.mousePressEvent(self, event)


class InlinedWidgetInfo:
    # From your pasting URL
    object_replacement_character = chr(0xfffc)
    _instance_counter = 0

    def __init__(self, widget):
        self.widget = widget
        self.text_format_id = QTextFormat.UserObject + InlinedWidgetInfo._instance_counter
        self.char = self.object_replacement_character
        InlinedWidgetInfo._instance_counter += 1


class TextEdit(QTextEdit):

    def __init__(self):
        super(TextEdit, self).__init__()
        # From your pasting URL, but some valiables belong to QTextEdit.
        self.last_text_lenght = 0
        self.text_format_id_to_inlined_widget_map = {}
        self.currentCharFormatChanged.connect(self.on_character_format_change)
        self.selectionChanged.connect(self._trigger_obj_char_rescan)
        self.textChanged.connect(self.on_text_changed)

    def wrap_with_text_object(self, inlined_widget):
        class ImageObject(QObject, QTextObjectInterface):
            def __init__(self, parent=None):
                super(ImageObject, self).__init__(parent)

            def drawObject(self, painter: QPainter, rect: QRectF, doc: QTextDocument, posInDocument: int,
                           format: QTextFormat) -> None:
                # inlined_widget.widget.render(painter, rect.topLeft().toPoint())
                inlined_widget.widget.setGeometry(rect.toRect())

            def intrinsicSize(self, doc: QTextDocument, posInDocument: int, format: QTextFormat) -> QSizeF:
                return QSizeF(inlined_widget.widget.size())

        document_layout = self.document().documentLayout()
        document_layout.registerHandler(inlined_widget.text_format_id, ImageObject(self))
        self.text_format_id_to_inlined_widget_map[inlined_widget.text_format_id] = inlined_widget
        inlined_widget.widget.setPixmap(inlined_widget.widget.pixmap().scaled(inlined_widget.widget.size()))

    def insert_text_object(self, cursor, inlined_widget):
        inlined_widget = InlinedWidgetInfo(inlined_widget)
        self.wrap_with_text_object(inlined_widget)
        inlined_widget.widget.view = self.vi
        inlined_widget.widget.setParent(self)

        char_format = QTextCharFormat()
        char_format.setObjectType(inlined_widget.text_format_id)
        cursor.insertText(inlined_widget.char, char_format)
        inlined_widget.widget.show()

    def on_character_format_change(self, qtextcharformat):
        text_format_id = qtextcharformat.objectType()

        # id 0 is used when the object is deselected - I don't really want the id
        # itself, I just want to know that there was some change AFTER it was done
        if text_format_id == 0:
            self._trigger_obj_char_rescan()

    def on_text_changed(self):
        current_text_lenght = len(self.toPlainText())
        if self.last_text_lenght > current_text_lenght:
            self._trigger_obj_char_rescan()

        self.last_text_lenght = current_text_lenght

    def _trigger_obj_char_rescan(self):
        text = self.toPlainText()
        character_indexes = [
            cnt for cnt, char in enumerate(text)
            if char == InlinedWidgetInfo.object_replacement_character
        ]

        # get text_format_id for all OBJECT REPLACEMENT CHARACTERs
        present_text_format_ids = set()
        for index in character_indexes:
            cursor = QTextCursor(self.document())

            # I have to create text selection in order to detect correct character
            cursor.setPosition(index)
            if index < len(text):
                cursor.setPosition(index + 1, QTextCursor.KeepAnchor)

            text_format_id = cursor.charFormat().objectType()

            present_text_format_ids.add(text_format_id)

        # diff for characters that are there and that should be there
        expected_text_format_ids = set(self.text_format_id_to_inlined_widget_map.keys())
        removed_text_ids = expected_text_format_ids - present_text_format_ids

        # hide widgets for characters that were removed
        for text_format_id in removed_text_ids:
            inlined_widget = self.text_format_id_to_inlined_widget_map[text_format_id]
            inlined_widget.widget.hide()
            del self.text_format_id_to_inlined_widget_map[text_format_id]


class TestWidget(QWidget):

    def __init__(self):
        super(TestWidget, self).__init__()
        layout = QVBoxLayout(self)
        self.vi = View()
        self.sc = Scene()
        self.te = TextEdit()
        self.te.vi = self.vi
        self.te.resize(int(QPageSize.size(QPageSize.A0, QPageSize.Point).width()),
                       int(QPageSize.size(QPageSize.A0, QPageSize.Point).height()))
        self.sc.addWidget(self.te)
        self.vi.setScene(self.sc)
        self.vi.setSceneRect(QRectF(0, 0, int(QPageSize.size(QPageSize.A0, QPageSize.Point).width()),
                                    int(QPageSize.size(QPageSize.A0, QPageSize.Point).height())))
        layout.addWidget(self.vi)
        self.btn_img = QPushButton('add picture', clicked=lambda: self.te.insert_text_object(self.te.textCursor(), InLineWidget()))
        layout.addWidget(self.btn_img)
        self.vi.centerOn(0, 0)

    def addPic(self):
        # is not used
        pass


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = TestWidget()

    widget.show()

    sys.exit(app.exec_())
