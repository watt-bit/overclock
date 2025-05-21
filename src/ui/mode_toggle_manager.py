from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt

class ModeToggleManager:
    """
    Manager for toggling between Model and Historian views.
    Extracts the mode toggle button logic from the main window.
    """
    
    def __init__(self, main_window):
        """Initialize with reference to the main window"""
        self.main_window = main_window
    
    def toggle_mode_button(self):
        """Toggle the mode button text between Model and Historian"""
        if self.main_window.is_model_view:
            # Switching to Historian mode
            self.main_window.mode_toggle_btn.setText("💾 Historian")
            
            # Hide the properties panel if it's open
            if self.main_window.properties_dock.isVisible():
                self.main_window.properties_dock.setVisible(False)
            
            # Hide the analytics panel if it's open
            if self.main_window.analytics_dock.isVisible():
                self.main_window.analytics_dock.setVisible(False)
            
            # Hide the analytics toggle button in historian view
            if hasattr(self.main_window, 'analytics_toggle_btn'):
                self.main_window.analytics_toggle_btn.hide()
            
            # Disable the toolbar menu buttons for properties and analytics
            self.main_window.properties_action.setEnabled(False)
            self.main_window.analytics_action.setEnabled(False)
            
            # Disable all component buttons
            self.main_window.disable_component_buttons(True)
            
            # Disable background toggle button in historian view and apply disabled style
            self.main_window.background_toggle_btn.setEnabled(False)
            self.main_window.background_toggle_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: #999999; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                }
            """)
            
            # Switch to the historian view
            self.switch_to_historian_view()
        else:
            # Switching back to Model mode
            self.main_window.mode_toggle_btn.setText("🏗️ Build")
            
            # Show the analytics toggle button when returning to model view
            if hasattr(self.main_window, 'analytics_toggle_btn'):
                self.main_window.analytics_toggle_btn.show()
            
            # Re-enable the toolbar menu buttons
            self.main_window.properties_action.setEnabled(True)
            self.main_window.analytics_action.setEnabled(True)
            
            # Re-enable all component buttons
            self.main_window.disable_component_buttons(False)
            
            # Re-enable background toggle button in model view with original style
            self.main_window.background_toggle_btn.setEnabled(True)
            self.main_window.background_toggle_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: white; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                }
                QPushButton:hover { 
                    background-color: #4D4D4D; 
                    border: 1px solid #666666;
                }
                QPushButton:pressed { 
                    background-color: #2D2D2D; 
                    border: 2px solid #777777;
                    padding: 4px; 
                }
            """)
            
            # Switch back to the model view
            self.switch_to_model_view()

    def switch_to_historian_view(self):
        """Switch from model view to historian view"""
        if self.main_window.is_model_view:
            # Store the current zoom slider value
            self.main_window.previous_zoom_value = self.main_window.zoom_slider.value()
            
            # Set flag to indicate we're now in historian view
            self.main_window.is_model_view = False
            
            # Hide the analytics panel if it's open
            if self.main_window.analytics_dock.isVisible():
                self.main_window.analytics_dock.setVisible(False)
            
            # Hide the analytics toggle button in historian view
            if hasattr(self.main_window, 'analytics_toggle_btn'):
                self.main_window.analytics_toggle_btn.hide()
            
            # Disable the toolbar menu buttons for properties and analytics
            self.main_window.properties_action.setEnabled(False)
            self.main_window.analytics_action.setEnabled(False)
            
            # Update the historian chart with current data
            self.main_window.historian_manager.update_chart()
            
            # Change the view to show the historian scene
            self.main_window.view.setScene(self.main_window.historian_manager.historian_scene)
            
            # Reset the view's scroll position to ensure the chart is centered
            self.main_window.view.resetTransform()  # Clear any existing transforms
            self.main_window.view.setTransform(self.main_window.view.transform().scale(1, 1))  # Set to 1:1 scale
            
            # Disable scrolling and movement in historian view
            self.main_window.view.setDragMode(QGraphicsView.NoDrag)
            self.main_window.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.main_window.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Resize the chart widget to fit the current view size
            view_size = self.main_window.view.viewport().size()
            self.main_window.historian_manager.resize_chart_widget(view_size.width(), view_size.height())
            
            # Center the view on the chart AFTER resizing
            self.main_window.view.centerOn(self.main_window.historian_manager.chart_proxy)
            
            # Set zoom to 1x and disable slider
            self.main_window.zoom_slider.setValue(100)  # Set slider to 1.0x
            self.main_window.zoom_slider.setEnabled(False)
            
            # Ensure background toggle is disabled with gray text
            self.main_window.background_toggle_btn.setEnabled(False)
            self.main_window.background_toggle_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: #999999; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                }
            """)
            
            # Note: Setting the slider value automatically triggers zoom_changed,
            # which applies the transform and updates the view.

    def switch_to_model_view(self):
        """Switch from historian view back to model view"""
        if not self.main_window.is_model_view:
            # Set flag to indicate we're now in model view
            self.main_window.is_model_view = True
            
            # Change the view back to show the model scene
            self.main_window.view.setScene(self.main_window.scene)
            
            # Re-enable scrolling and movement in model view
            self.main_window.view.setDragMode(QGraphicsView.ScrollHandDrag)
            self.main_window.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.main_window.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            
            # Re-enable zoom slider and restore previous value
            self.main_window.zoom_slider.setEnabled(True)
            if self.main_window.previous_zoom_value is not None:
                self.main_window.zoom_slider.setValue(self.main_window.previous_zoom_value)
            
            # Re-enable background toggle button with original style
            self.main_window.background_toggle_btn.setEnabled(True)
            self.main_window.background_toggle_btn.setStyleSheet("""
                QPushButton { 
                    background-color: #3D3D3D; 
                    color: white; 
                    border: 1px solid #555555; 
                    border-radius: 3px; 
                    padding: 5px; 
                }
                QPushButton:hover { 
                    background-color: #4D4D4D; 
                    border: 1px solid #666666;
                }
                QPushButton:pressed { 
                    background-color: #2D2D2D; 
                    border: 2px solid #777777;
                    padding: 4px; 
                }
            """)
            
            # Reset the stored previous value
            self.main_window.previous_zoom_value = None
            
            # Note: Setting the slider value automatically triggers zoom_changed,
            # which applies the transform and updates the view. 