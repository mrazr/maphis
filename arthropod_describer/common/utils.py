import typing
from pathlib import Path

from PySide2.QtWidgets import QFileDialog, QWidget


def choose_folder(parent: QWidget) -> typing.Optional[Path]:
    file_dialog = QFileDialog(parent)
    file_dialog.setFileMode(QFileDialog.Directory)
    file_dialog.setWindowTitle("Open photo folder")
    if file_dialog.exec_():
        file_path = Path(file_dialog.selectedFiles()[0])
        return file_path
    return None
