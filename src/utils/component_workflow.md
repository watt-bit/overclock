# Adding a New Decorative Component

This document outlines the standard workflow for adding new decorative components to the Watt-Bit Sandbox application. Decorative components (such as trees, bushes, ponds, and houses) enhance the visual appeal of the simulation but don't affect the power system simulation directly.

## Standard Workflow

Follow these steps in order when adding a new decorative component:

### 1. Create the Component Class

1. Create a new Python file in the `src/components/` directory, named after your component (e.g., `my_component.py`)
2. Base the implementation on an existing decorative component (e.g., `bush.py` or `tree.py`)
3. Update the following attributes:
   - Image path (`self.image_path`) pointing to the asset in the UI assets folder
   - Component size (adjust width and height based on your image's aspect ratio)
   - Any custom visual properties specific to your component

Example template:

```python
from PyQt5.QtCore import QRectF
from src.components.base import ComponentBase
import os

class MyComponent(ComponentBase):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.width = 100  # Adjust based on desired size
        self.height = 80  # Adjust based on desired size and aspect ratio
        self.image_path = os.path.join("src", "ui", "assets", "my_component.png")
        self.load_image()
        self.is_decorative = True  # Important flag for decorative components
```

### 2. Update Main Window

1. Open `src/ui/main_window.py`
2. Add an import for your new component at the top of the file:
   ```python
   from src.components.my_component import MyComponent
   ```
3. Add a button to the component palette in the `init_ui` method:
   ```python
   my_component_btn = QPushButton("Add My Component")
   my_component_btn.clicked.connect(lambda: self.add_component("my_component"))
   component_layout.addWidget(my_component_btn)
   ```
4. Add a case in the `add_component` method to handle your new component type:
   ```python
   elif component_type == "my_component":
       component = MyComponent(0, 0)
       self.scene.addItem(component)
       # Do not add decorative components to the components list
       # as they are purely visual and not part of the power network
   ```

### 3. Update Connection Manager

1. Open `src/ui/connection_manager.py`
2. Add an import for your new component at the top of the file:
   ```python
   from src.components.my_component import MyComponent
   ```
3. Update the `handle_connection_click` method to ignore your decorative component:
   ```python
   # In handle_connection_click method
   if isinstance(component, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, MyComponent)):
       return  # Decorative components cannot be connected
   ```
4. Similarly, update the `handle_sever_connection` method:
   ```python
   # In handle_sever_connection method
   if isinstance(component, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, MyComponent)):
       return  # Decorative components have no connections to sever
   ```

### 4. Update Properties Manager

1. Open `src/ui/properties_manager.py`
2. Add an import for your new component at the top of the file:
   ```python
   from src.components.my_component import MyComponent
   ```
3. Update the `delete_component` method to handle your component:
   ```python
   # In delete_component method
   if isinstance(component, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, MyComponent)):
       self.main_window.scene.removeItem(component)
   ```
4. Update the `show_component_properties` method:
   ```python
   # In show_component_properties method
   elif isinstance(component, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, MyComponent)):
       self.clear_properties()
       title_label = QLabel(f"{component.__class__.__name__}")
       title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
       self.properties_layout.addWidget(title_label)
       self.properties_layout.addWidget(QLabel("Decorative element - no properties to edit"))
   ```

### 5. Update Model Manager

1. Open `src/models/model_manager.py`
2. Add an import for your new component at the top of the file:
   ```python
   from src.components.my_component import MyComponent
   ```
3. Update the `save_scenario` method to include your component in the saved decorative elements:
   ```python
   # In the section that saves decorative elements
   elif isinstance(item, (TreeComponent, BushComponent, PondComponent, House1Component, House2Component, MyComponent)):
       decorative_data.append({
           "type": item.__class__.__name__,
           "x": item.x(),
           "y": item.y()
       })
   ```
4. Update the `load_scenario` method to handle loading your component:
   ```python
   # In the decorative elements loading section
   elif component_type == "MyComponent":
       component = MyComponent(x, y)
       self.main_window.scene.addItem(component)
   ```

### 6. Document the Changes

1. Update the `history` file with an entry detailing the addition of your new component:
   ```
   ## YYYY-MM-DD HH:MM - Added New Decorative Component: My Component
   - Created new MyComponent class in src/components/my_component.py
   - Added "Add My Component" button to the component palette
   - Updated ConnectionManager to ignore the new decorative component
   - Updated PropertiesManager to handle the new component
   - Updated ModelManager to save/load the new component
   - Enhanced visual variety with the new decorative option
   ```

## Important Considerations

1. **Image Assets**: Ensure your image is placed in the `src/ui/assets/` directory before implementation.
2. **Aspect Ratio**: Maintain appropriate aspect ratio when setting component dimensions.
3. **Decorative Flag**: Always set `self.is_decorative = True` for decorative components.
4. **Component List**: Never add decorative components to `self.components` list as they don't participate in the power network.
5. **Consistent Naming**: Use consistent naming throughout the codebase (e.g., if your class is `MyComponent`, use "my_component" as the component type in `add_component`).

## Existing Decorative Components

For reference, the existing decorative components you can use as templates are:
- `TreeComponent` in `src/components/tree.py`
- `BushComponent` in `src/components/bush.py`
- `PondComponent` in `src/components/pond.py`
- `House1Component` in `src/components/house1.py`
- `House2Component` in `src/components/house2.py` 