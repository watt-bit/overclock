from __future__ import annotations
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog
from PyQt6.QtCore import Qt


def _standard_stylesheet() -> str:
    """Return the standard stylesheet used for dialogs/popups to match properties panel theme."""
    # Matches the styling used in properties_manager._show_csv_format_dialog
    return (
        """
        QDialog {
            background-color: rgba(37, 47, 52, 0.95);
            color: white;
            font-family: Menlo, Consolas, Courier, monospace;
            font-size: 10px;
            border: 1px solid #777777;
            border-radius: 3px;
        }
        QLabel {
            color: white;
            background: transparent;
        }
        QPushButton {
            background-color: rgba(37, 47, 52, 0.75);
            color: white;
            border: 1px solid #777777;
            border-radius: 3px;
            padding: 8px 16px;
            font-weight: bold;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #227D22;
        }
        QPushButton:pressed {
            background-color: #103D10;
        }
        """
    )


def apply_standard_dialog_style(widget: QDialog) -> None:
    """Apply the standard stylesheet to a QDialog/QMessageBox/QFileDialog instance."""
    try:
        widget.setStyleSheet(_standard_stylesheet())
    except Exception:
        # Styling errors should not block the dialog
        pass


def create_styled_message_box(
    parent,
    icon: QMessageBox.Icon,
    title: str,
    text: str,
    buttons: int,
    default_button: QMessageBox.StandardButton | None = None,
) -> QMessageBox:
    """Create a QMessageBox with the standard styling applied."""
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(text)
    box.setStandardButtons(buttons)
    if default_button is not None:
        box.setDefaultButton(default_button)
    apply_standard_dialog_style(box)
    return box


def get_open_file_name(
    parent,
    title: str,
    name_filter: str,
) -> tuple[str, str]:
    """Show a styled Open File dialog and return (filename, selected_filter)."""
    dialog = QFileDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    dialog.setNameFilter(name_filter)
    # Ensure we can style the dialog consistently across platforms
    try:
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    except Exception:
        pass
    apply_standard_dialog_style(dialog)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        files = dialog.selectedFiles()
        if files:
            # Qt doesn't provide selected name filter in a portable way; return input filter
            return files[0], name_filter
    return "", name_filter


def get_save_file_name(
    parent,
    title: str,
    name_filter: str,
) -> tuple[str, str]:
    """Show a styled Save File dialog and return (filename, selected_filter)."""
    dialog = QFileDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setNameFilter(name_filter)
    try:
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    except Exception:
        pass
    apply_standard_dialog_style(dialog)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        files = dialog.selectedFiles()
        if files:
            return files[0], name_filter
    return "", name_filter


