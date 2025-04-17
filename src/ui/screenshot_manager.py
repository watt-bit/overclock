from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtGui import QPainter, QPixmap
from PyQt5.QtCore import Qt


class ScreenshotManager:
    def __init__(self, main_window):
        self.main_window = main_window
        
    def take_screenshot(self):
        """Take a screenshot of the modeling view area and copy to clipboard"""
        # Create a pixmap the size of the viewport
        pixmap = QPixmap(self.main_window.view.viewport().size())
        pixmap.fill(Qt.transparent)
        
        # Create painter for the pixmap
        painter = QPainter(pixmap)
        
        # Render the view onto the pixmap
        self.main_window.view.render(painter)
        
        # Add the Overclock logo overlay if it exists
        if hasattr(self.main_window, 'logo_overlay') and not self.main_window.logo_overlay.pixmap().isNull():
            # Get the logo position and pixmap
            logo_pos = self.main_window.logo_overlay.pos()
            logo_pixmap = self.main_window.logo_overlay.pixmap()
            
            # Draw the logo at its current position
            painter.drawPixmap(logo_pos, logo_pixmap)
        
        # Add the mode toggle button if it exists
        if hasattr(self.main_window, 'mode_toggle_btn'):
            # Create a pixmap from the mode toggle button
            mode_btn_pixmap = QPixmap(self.main_window.mode_toggle_btn.size())
            mode_btn_pixmap.fill(Qt.transparent)
            self.main_window.mode_toggle_btn.render(mode_btn_pixmap)
            
            # Get the button position
            mode_btn_pos = self.main_window.mode_toggle_btn.pos()
            
            # Draw the button at its current position
            painter.drawPixmap(mode_btn_pos, mode_btn_pixmap)
        
        # Add the CAPEX label if it exists
        if hasattr(self.main_window, 'capex_label'):
            # Create a pixmap from the CAPEX label
            capex_pixmap = QPixmap(self.main_window.capex_label.size())
            capex_pixmap.fill(Qt.transparent)
            self.main_window.capex_label.render(capex_pixmap)
            
            # Get the label position
            capex_pos = self.main_window.capex_label.pos()
            
            # Draw the label at its current position
            painter.drawPixmap(capex_pos, capex_pixmap)
        
        # Add the IRR label if it exists
        if hasattr(self.main_window, 'irr_label'):
            # Create a pixmap from the IRR label
            irr_pixmap = QPixmap(self.main_window.irr_label.size())
            irr_pixmap.fill(Qt.transparent)
            self.main_window.irr_label.render(irr_pixmap)
            
            # Get the label position
            irr_pos = self.main_window.irr_label.pos()
            
            # Draw the label at its current position
            painter.drawPixmap(irr_pos, irr_pixmap)
        
        # End painting
        painter.end()
        
        # Copy pixmap to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(pixmap)
        
        # Show confirmation to user
        QMessageBox.information(self.main_window, "Screenshot", "Screenshot copied to clipboard") 