"""
GUI component module with SOLID architecture.

Provides abstract component interfaces and concrete implementations
for various GUI elements that can be clicked and interacted with.

SOLID Principles Applied:
- Single Responsibility: Each component handles only its own state/behavior
- Open/Closed: New components can be added without modifying existing code
- Liskov Substitution: All components can be used interchangeably via Component interface
- Interface Segregation: Separate protocols for clickable, focusable, etc.
- Dependency Inversion: High-level modules depend on abstractions (Component protocol)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, Tuple, List, Optional, Callable, runtime_checkable


class ComponentState(Enum):
    """Visual states for interactive components."""
    NORMAL = "normal"
    HOVER = "hover"
    PRESSED = "pressed"
    DISABLED = "disabled"
    FOCUSED = "focused"


@dataclass
class Bounds:
    """Rectangular bounds for hit testing and rendering."""
    x: int
    y: int
    width: int
    height: int

    def contains(self, px: int, py: int) -> bool:
        """Check if a point is inside this bounds."""
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)


@runtime_checkable
class Clickable(Protocol):
    """Protocol for components that respond to clicks."""

    def on_click(self, x: int, y: int) -> None:
        """Handle a click at the given position."""
        ...

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within this component."""
        ...


@runtime_checkable
class Focusable(Protocol):
    """Protocol for components that can receive focus."""

    def focus(self) -> None:
        """Give focus to this component."""
        ...

    def blur(self) -> None:
        """Remove focus from this component."""
        ...

    @property
    def has_focus(self) -> bool:
        """Check if this component has focus."""
        ...


@runtime_checkable
class ValueHolder(Protocol):
    """Protocol for components that hold a value."""

    @property
    def value(self):
        """Get the current value."""
        ...


class Component(ABC):
    """
    Abstract base class for all GUI components.

    All components have bounds, state, and can be rendered.
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        self._bounds = Bounds(x, y, width, height)
        self._state = ComponentState.NORMAL
        self._enabled = True
        self._visible = True

    @property
    def bounds(self) -> Bounds:
        """Get component bounds."""
        return self._bounds

    @property
    def x(self) -> int:
        return self._bounds.x

    @property
    def y(self) -> int:
        return self._bounds.y

    @property
    def width(self) -> int:
        return self._bounds.width

    @property
    def height(self) -> int:
        return self._bounds.height

    @property
    def state(self) -> ComponentState:
        """Get current visual state."""
        if not self._enabled:
            return ComponentState.DISABLED
        return self._state

    @state.setter
    def state(self, value: ComponentState) -> None:
        """Set visual state."""
        self._state = value

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within this component."""
        return self._bounds.contains(x, y)

    def set_hover(self, is_hover: bool) -> None:
        """Set hover state."""
        if self._enabled:
            self._state = ComponentState.HOVER if is_hover else ComponentState.NORMAL


class Button(Component):
    """
    A clickable button component.

    Supports click callbacks and visual state changes.
    """

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        label: str,
        on_click: Optional[Callable[[], None]] = None
    ):
        super().__init__(x, y, width, height)
        self.label = label
        self._on_click = on_click
        self._click_count = 0

    def on_click(self, px: int, py: int) -> None:
        """Handle click event."""
        if self._enabled and self.contains_point(px, py):
            self._click_count += 1
            if self._on_click:
                self._on_click()

    @property
    def click_count(self) -> int:
        """Get the number of times this button has been clicked."""
        return self._click_count


class Checkbox(Component):
    """
    A checkbox component that toggles between checked/unchecked.
    """

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        label: str,
        checked: bool = False,
        on_change: Optional[Callable[[bool], None]] = None
    ):
        super().__init__(x, y, width, height)
        self.label = label
        self._checked = checked
        self._on_change = on_change

    @property
    def checked(self) -> bool:
        return self._checked

    @property
    def value(self) -> bool:
        return self._checked

    def toggle(self) -> None:
        """Toggle the checked state."""
        if self._enabled:
            self._checked = not self._checked
            if self._on_change:
                self._on_change(self._checked)

    def on_click(self, px: int, py: int) -> None:
        """Handle click event."""
        if self._enabled and self.contains_point(px, py):
            self.toggle()


class RadioGroup:
    """
    Manages a group of radio buttons ensuring mutual exclusivity.
    """

    def __init__(self):
        self._buttons: List["RadioButton"] = []
        self._selected_index: int = -1
        self._on_change: Optional[Callable[[int, str], None]] = None

    def add_button(self, button: "RadioButton") -> None:
        """Add a radio button to this group."""
        button._group = self
        self._buttons.append(button)
        if button.selected:
            self._select_button(button)

    def _select_button(self, selected: "RadioButton") -> None:
        """Select a button, deselecting others."""
        for i, button in enumerate(self._buttons):
            if button is selected:
                button._selected = True
                self._selected_index = i
            else:
                button._selected = False

        if self._on_change and self._selected_index >= 0:
            self._on_change(self._selected_index, selected.label)

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def selected_value(self) -> Optional[str]:
        if 0 <= self._selected_index < len(self._buttons):
            return self._buttons[self._selected_index].label
        return None

    def set_on_change(self, callback: Callable[[int, str], None]) -> None:
        """Set callback for selection changes."""
        self._on_change = callback


class RadioButton(Component):
    """
    A radio button component - part of a RadioGroup.
    """

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        label: str,
        selected: bool = False
    ):
        super().__init__(x, y, width, height)
        self.label = label
        self._selected = selected
        self._group: Optional[RadioGroup] = None

    @property
    def selected(self) -> bool:
        return self._selected

    @property
    def value(self) -> bool:
        return self._selected

    def select(self) -> None:
        """Select this radio button."""
        if self._enabled and self._group:
            self._group._select_button(self)

    def on_click(self, px: int, py: int) -> None:
        """Handle click event."""
        if self._enabled and self.contains_point(px, py):
            self.select()


class TextInput(Component):
    """
    A text input field component.

    Supports text entry, cursor position, and focus.
    """

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        placeholder: str = "",
        max_length: int = 20,
        on_change: Optional[Callable[[str], None]] = None
    ):
        super().__init__(x, y, width, height)
        self.placeholder = placeholder
        self.max_length = max_length
        self._text = ""
        self._cursor_pos = 0
        self._has_focus = False
        self._on_change = on_change

    @property
    def text(self) -> str:
        return self._text

    @property
    def value(self) -> str:
        return self._text

    @property
    def cursor_pos(self) -> int:
        return self._cursor_pos

    @property
    def has_focus(self) -> bool:
        return self._has_focus

    def focus(self) -> None:
        """Give focus to this input."""
        self._has_focus = True
        self._state = ComponentState.FOCUSED

    def blur(self) -> None:
        """Remove focus from this input."""
        self._has_focus = False
        self._state = ComponentState.NORMAL

    def on_click(self, px: int, py: int) -> None:
        """Handle click event - focus the input."""
        if self._enabled and self.contains_point(px, py):
            self.focus()

    def insert_char(self, char: str) -> None:
        """Insert a character at cursor position."""
        if self._has_focus and len(self._text) < self.max_length:
            self._text = (
                self._text[:self._cursor_pos] +
                char +
                self._text[self._cursor_pos:]
            )
            self._cursor_pos += 1
            if self._on_change:
                self._on_change(self._text)

    def delete_char(self) -> None:
        """Delete character before cursor (backspace)."""
        if self._has_focus and self._cursor_pos > 0:
            self._text = (
                self._text[:self._cursor_pos - 1] +
                self._text[self._cursor_pos:]
            )
            self._cursor_pos -= 1
            if self._on_change:
                self._on_change(self._text)

    def move_cursor_left(self) -> None:
        """Move cursor left."""
        if self._cursor_pos > 0:
            self._cursor_pos -= 1

    def move_cursor_right(self) -> None:
        """Move cursor right."""
        if self._cursor_pos < len(self._text):
            self._cursor_pos += 1


class Slider(Component):
    """
    A slider component for selecting a value in a range.
    """

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        min_value: float = 0.0,
        max_value: float = 100.0,
        value: float = 50.0,
        on_change: Optional[Callable[[float], None]] = None
    ):
        super().__init__(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self._value = max(min_value, min(value, max_value))
        self._on_change = on_change
        self._dragging = False

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        new_value = max(self.min_value, min(v, self.max_value))
        if new_value != self._value:
            self._value = new_value
            if self._on_change:
                self._on_change(self._value)

    @property
    def percentage(self) -> float:
        """Get value as percentage (0-100)."""
        range_val = self.max_value - self.min_value
        if range_val == 0:
            return 0.0
        return ((self._value - self.min_value) / range_val) * 100

    def on_click(self, px: int, py: int) -> None:
        """Handle click - set value based on click position."""
        if self._enabled and self.contains_point(px, py):
            # Calculate value from click position
            rel_x = px - self.x
            percentage = rel_x / self.width
            range_val = self.max_value - self.min_value
            self.value = self.min_value + percentage * range_val


class ProgressBar(Component):
    """
    A progress bar component showing completion percentage.
    """

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        value: float = 0.0,
        max_value: float = 100.0
    ):
        super().__init__(x, y, width, height)
        self._value = max(0, min(value, max_value))
        self._max_value = max_value
        self._animated = False
        self._animation_offset = 0

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, v: float) -> None:
        self._value = max(0, min(v, self._max_value))

    @property
    def percentage(self) -> float:
        """Get value as percentage."""
        if self._max_value == 0:
            return 0.0
        return (self._value / self._max_value) * 100

    def increment(self, amount: float = 1.0) -> None:
        """Increment the progress value."""
        self.value = self._value + amount

    def on_click(self, px: int, py: int) -> None:
        """Progress bars don't respond to clicks by default."""
        pass


class ListItem:
    """An item in a list component."""

    def __init__(self, label: str, value: Optional[str] = None):
        self.label = label
        self.value = value if value is not None else label


class ListBox(Component):
    """
    A list box component showing selectable items.
    """

    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        items: Optional[List[str]] = None,
        on_select: Optional[Callable[[int, str], None]] = None
    ):
        super().__init__(x, y, width, height)
        self._items: List[ListItem] = []
        if items:
            for item in items:
                self._items.append(ListItem(item))
        self._selected_index = -1
        self._hover_index = -1
        self._on_select = on_select
        self._item_height = 20
        self._scroll_offset = 0

    @property
    def items(self) -> List[ListItem]:
        return self._items

    @property
    def selected_index(self) -> int:
        return self._selected_index

    @property
    def selected_item(self) -> Optional[ListItem]:
        if 0 <= self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    @property
    def value(self) -> Optional[str]:
        item = self.selected_item
        return item.value if item else None

    @property
    def item_height(self) -> int:
        return self._item_height

    @property
    def hover_index(self) -> int:
        return self._hover_index

    def add_item(self, label: str, value: Optional[str] = None) -> None:
        """Add an item to the list."""
        self._items.append(ListItem(label, value))

    def select_index(self, index: int) -> None:
        """Select an item by index."""
        if 0 <= index < len(self._items):
            self._selected_index = index
            if self._on_select:
                item = self._items[index]
                self._on_select(index, item.value)

    def _get_item_index_at(self, py: int) -> int:
        """Get the item index at a given y position."""
        rel_y = py - self.y
        index = rel_y // self._item_height + self._scroll_offset
        if 0 <= index < len(self._items):
            return index
        return -1

    def on_click(self, px: int, py: int) -> None:
        """Handle click - select item at position."""
        if self._enabled and self.contains_point(px, py):
            index = self._get_item_index_at(py)
            if index >= 0:
                self.select_index(index)

    def update_hover(self, px: int, py: int) -> None:
        """Update hover state based on mouse position."""
        if self.contains_point(px, py):
            self._hover_index = self._get_item_index_at(py)
        else:
            self._hover_index = -1


@dataclass
class Window:
    """
    A window container that holds components.
    """
    title: str
    x: int
    y: int
    width: int
    height: int
    components: List[Component] = field(default_factory=list)
    active: bool = False

    def add_component(self, component: Component) -> None:
        """Add a component to this window."""
        self.components.append(component)

    def contains_point(self, px: int, py: int) -> bool:
        """Check if a point is within this window."""
        return (self.x <= px < self.x + self.width and
                self.y <= py < self.y + self.height)

    def get_component_at(self, px: int, py: int) -> Optional[Component]:
        """Get the component at a given position."""
        for component in reversed(self.components):
            if component.visible and component.contains_point(px, py):
                return component
        return None


class GUIState:
    """
    Manages the overall GUI state including all windows and components.

    Navigation model:
    - Tab cycles between windows (top-level components)
    - Arrow keys navigate within the focused window
    - Space/Enter activates the selected item in the window
    """

    def __init__(self):
        self.windows: List[Window] = []
        self._focused_window_index: int = -1
        self._component_index_per_window: dict = {}  # window -> index of selected component

    def add_window(self, window: Window) -> None:
        """Add a window to the GUI."""
        self.windows.append(window)
        # Initialize component index for this window (select first interactive component)
        self._component_index_per_window[id(window)] = 0

    def _get_interactive_components(self, window: Window) -> List[Component]:
        """Get list of interactive components in a window."""
        return [c for c in window.components
                if c.enabled and not isinstance(c, ProgressBar)]

    def get_focused_window(self) -> Optional[Window]:
        """Get the currently focused window."""
        if 0 <= self._focused_window_index < len(self.windows):
            return self.windows[self._focused_window_index]
        return None

    def get_focused_component(self) -> Optional[Component]:
        """Get the currently focused component within the focused window."""
        window = self.get_focused_window()
        if not window:
            return None
        components = self._get_interactive_components(window)
        if not components:
            return None
        idx = self._component_index_per_window.get(id(window), 0)
        if 0 <= idx < len(components):
            return components[idx]
        return components[0] if components else None

    def clear_focus(self) -> None:
        """Remove focus from all components."""
        for window in self.windows:
            window.active = False
            for component in window.components:
                if component.state == ComponentState.FOCUSED:
                    component.state = ComponentState.NORMAL

    def _update_focus_visuals(self) -> None:
        """Update visual focus indicators."""
        # Clear all focus
        for window in self.windows:
            window.active = False
            for component in window.components:
                if component.state == ComponentState.FOCUSED:
                    component.state = ComponentState.NORMAL
                # Also blur TextInputs
                if isinstance(component, TextInput) and component.has_focus:
                    component.blur()

        # Set focus on current window and component
        window = self.get_focused_window()
        if window:
            window.active = True
            component = self.get_focused_component()
            if component:
                component.state = ComponentState.FOCUSED
                # Also focus TextInputs so they accept typing
                if isinstance(component, TextInput):
                    component.focus()

    def focus_next(self) -> None:
        """Move focus to the next window."""
        if not self.windows:
            return
        self._focused_window_index = (self._focused_window_index + 1) % len(self.windows)
        self._update_focus_visuals()

    def focus_previous(self) -> None:
        """Move focus to the previous window."""
        if not self.windows:
            return
        self._focused_window_index = (self._focused_window_index - 1) % len(self.windows)
        self._update_focus_visuals()

    def activate_focused(self) -> bool:
        """
        Activate the currently focused component.

        Returns True if a component was activated.
        """
        component = self.get_focused_component()
        if not component:
            return False

        # Handle different component types
        if isinstance(component, Button):
            # Show pressed state briefly for visual feedback
            component.state = ComponentState.PRESSED
            component.on_click(0, 0)
            # Note: state will be reset to FOCUSED on next input event
            return True
        elif isinstance(component, Checkbox):
            component.toggle()
            return True
        elif isinstance(component, RadioButton):
            component.select()
            return True
        elif isinstance(component, TextInput):
            # Focus text input for typing
            if hasattr(component, 'focus'):
                component.focus()
            return True
        elif isinstance(component, ListBox):
            return True

        return False

    def handle_key(self, key: str) -> bool:
        """
        Handle a key press (for text input).

        Returns True if the key was handled.
        """
        component = self.get_focused_component()
        if component and isinstance(component, TextInput):
            if len(key) == 1 and key.isprintable():
                component.insert_char(key)
                return True
        return False

    def handle_special_key(self, key_name: str) -> bool:
        """
        Handle arrow keys and other special keys within the focused window.

        Returns True if the key was handled.
        """
        window = self.get_focused_window()
        if not window:
            return False

        component = self.get_focused_component()
        components = self._get_interactive_components(window)

        if not components:
            return False

        current_idx = self._component_index_per_window.get(id(window), 0)

        # TextInput: handle backspace and left/right cursor movement
        if isinstance(component, TextInput):
            if key_name == 'backspace':
                component.delete_char()
                return True
            elif key_name == 'left':
                component.move_cursor_left()
                return True
            elif key_name == 'right':
                component.move_cursor_right()
                return True
            elif key_name in ('up', 'down'):
                # Move to prev/next component in window
                if key_name == 'up' and current_idx > 0:
                    self._component_index_per_window[id(window)] = current_idx - 1
                    self._update_focus_visuals()
                    return True
                elif key_name == 'down' and current_idx < len(components) - 1:
                    self._component_index_per_window[id(window)] = current_idx + 1
                    self._update_focus_visuals()
                    return True

        # Slider: left/right to adjust value
        elif isinstance(component, Slider):
            if key_name == 'left':
                step = (component.max_value - component.min_value) / 20
                component.value = max(component.min_value, component.value - step)
                return True
            elif key_name == 'right':
                step = (component.max_value - component.min_value) / 20
                component.value = min(component.max_value, component.value + step)
                return True
            elif key_name in ('up', 'down'):
                # Move to prev/next slider
                if key_name == 'up' and current_idx > 0:
                    self._component_index_per_window[id(window)] = current_idx - 1
                    self._update_focus_visuals()
                    return True
                elif key_name == 'down' and current_idx < len(components) - 1:
                    self._component_index_per_window[id(window)] = current_idx + 1
                    self._update_focus_visuals()
                    return True

        # RadioButton, Checkbox, Button, ListBox: up/down to move between items
        elif isinstance(component, (RadioButton, Checkbox, Button, ListBox)):
            if key_name == 'up' and current_idx > 0:
                self._component_index_per_window[id(window)] = current_idx - 1
                self._update_focus_visuals()
                # For radio buttons, also select the new one
                new_component = components[current_idx - 1]
                if isinstance(new_component, RadioButton):
                    new_component.select()
                return True
            elif key_name == 'down' and current_idx < len(components) - 1:
                self._component_index_per_window[id(window)] = current_idx + 1
                self._update_focus_visuals()
                # For radio buttons, also select the new one
                new_component = components[current_idx + 1]
                if isinstance(new_component, RadioButton):
                    new_component.select()
                return True
            # ListBox also handles internal selection
            if isinstance(component, ListBox):
                if key_name == 'up' and component.selected_index > 0:
                    component.select_index(component.selected_index - 1)
                    return True
                elif key_name == 'down' and component.selected_index < len(component.items) - 1:
                    component.select_index(component.selected_index + 1)
                    return True

        return False

    # Legacy methods for compatibility
    def get_window_at(self, px: int, py: int) -> Optional[Window]:
        """Get the window at a given position."""
        for window in reversed(self.windows):
            if window.contains_point(px, py):
                return window
        return None

    def get_component_at(self, px: int, py: int) -> Optional[Component]:
        """Get the component at a given position."""
        window = self.get_window_at(px, py)
        if window:
            return window.get_component_at(px, py)
        return None

    def handle_click(self, px: int, py: int) -> Optional[Component]:
        """Handle a click at the given position."""
        component = self.get_component_at(px, py)
        if component and component.enabled:
            component.on_click(px, py)
            return component
        return None

    @property
    def focused_component(self) -> Optional[Component]:
        return self.get_focused_component()
