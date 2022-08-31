import typing

from PySide2.QtCore import Qt, QCoreApplication
from PySide2.QtWidgets import QProgressDialog, QWidget

from arthropod_describer.common.photo import Photo
from arthropod_describer.common.storage import Storage


class BlockingOperation:
    def __init__(self, storage: Storage, idxs: typing.List[int], operation: typing.Callable[[Storage, int], typing.Any],
                 result_handler: typing.Callable[[Storage, int, typing.Any], None], parent: QWidget):
        self.storage = storage
        self.indexes = idxs
        self.op = operation
        self.handler = result_handler
        self.parent = parent

    def start(self):
        prgr_diag = QProgressDialog(labelText='Processing',
                                    minimum=0,
                                    maximum=len(self.indexes), parent=self.parent)
        prgr_diag.setWindowTitle('Operation running')  # TODO allow to customize the title
        prgr_diag.setWindowModality(Qt.ApplicationModal)
        prgr_diag.setMinimumDuration(1)
        prgr_diag.show()
        for i, idx in enumerate(self.indexes):
            prgr_diag.setValue(i)
            photo_name = self.storage.image_names[idx]
            prgr_diag.setLabelText(f'Processing {photo_name}')
            QCoreApplication.processEvents()
            self.handler(self.storage, idx, self.op(self.storage, idx))
        prgr_diag.setValue(len(self.indexes))


class ProgressReport:
    def __init__(self, count: int, title_text: str, parent: typing.Optional[QWidget] = None):
        self.dialog = QProgressDialog()
        self.dialog.setWindowTitle(title_text)
        self.count = count
        self.current_count = 0

        self.dialog.setMinimum(0)
        self.dialog.setMaximum(count-1)

        self.dialog.setValue(0)
        self.dialog.show()

    def increment(self):
        self.current_count += 1
        self.dialog.setValue(self.current_count)
        QCoreApplication.processEvents()
        if self.current_count == self.count:
            self.dialog.close()
