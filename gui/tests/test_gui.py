"""
Tests for the GUI component module (gui.py).

Tests cover:
- Component base class
- Button component
- Checkbox component
- Radio button and radio group
- Text input component
- Slider component
- Progress bar component
- List box component
- Window container
- GUI state management
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gui import (
    Component,
    ComponentState,
    Bounds,
    Button,
    Checkbox,
    RadioButton,
    RadioGroup,
    TextInput,
    Slider,
    ProgressBar,
    ListBox,
    ListItem,
    ImageDisplay,
    Window,
    GUIState,
)


class TestBounds:
    """Tests for the Bounds class."""

    def test_bounds_creation(self):
        """Test creating bounds."""
        bounds = Bounds(10, 20, 100, 50)
        assert bounds.x == 10
        assert bounds.y == 20
        assert bounds.width == 100
        assert bounds.height == 50

    def test_contains_point_inside(self):
        """Test point inside bounds."""
        bounds = Bounds(10, 20, 100, 50)
        assert bounds.contains(10, 20) is True
        assert bounds.contains(50, 40) is True
        assert bounds.contains(109, 69) is True

    def test_contains_point_outside(self):
        """Test point outside bounds."""
        bounds = Bounds(10, 20, 100, 50)
        assert bounds.contains(9, 20) is False
        assert bounds.contains(10, 19) is False
        assert bounds.contains(110, 40) is False
        assert bounds.contains(50, 70) is False

    def test_contains_point_on_edge(self):
        """Test point on bounds edge."""
        bounds = Bounds(0, 0, 10, 10)
        assert bounds.contains(0, 0) is True
        assert bounds.contains(9, 9) is True
        assert bounds.contains(10, 10) is False  # Exclusive upper bound


class TestButton:
    """Tests for the Button component."""

    def test_button_creation(self):
        """Test creating a button."""
        btn = Button(10, 20, 100, 30, "TEST")
        assert btn.x == 10
        assert btn.y == 20
        assert btn.width == 100
        assert btn.height == 30
        assert btn.label == "TEST"
        assert btn.toggled is False

    def test_button_click_toggles(self):
        """Test that clicking a button toggles its state."""
        btn = Button(10, 20, 100, 30, "TEST")
        btn.on_click(50, 35)
        assert btn.toggled is True
        btn.on_click(50, 35)
        assert btn.toggled is False

    def test_button_click_outside_ignored(self):
        """Test that clicking outside the button is ignored."""
        btn = Button(10, 20, 100, 30, "TEST")
        btn.on_click(5, 35)  # Outside left
        assert btn.toggled is False

    def test_button_click_callback(self):
        """Test button click callback."""
        clicked = [False]

        def callback():
            clicked[0] = True

        btn = Button(10, 20, 100, 30, "TEST", on_click=callback)
        btn.on_click(50, 35)
        assert clicked[0] is True

    def test_button_disabled_no_click(self):
        """Test that disabled button ignores clicks."""
        btn = Button(10, 20, 100, 30, "TEST")
        btn.enabled = False
        btn.on_click(50, 35)
        assert btn.toggled is False

    def test_button_state_disabled(self):
        """Test button state when disabled."""
        btn = Button(10, 20, 100, 30, "TEST")
        btn.enabled = False
        assert btn.state == ComponentState.DISABLED


class TestCheckbox:
    """Tests for the Checkbox component."""

    def test_checkbox_creation(self):
        """Test creating a checkbox."""
        cb = Checkbox(10, 20, 100, 24, "Option", checked=True)
        assert cb.label == "Option"
        assert cb.checked is True
        assert cb.value is True

    def test_checkbox_toggle(self):
        """Test toggling a checkbox."""
        cb = Checkbox(10, 20, 100, 24, "Option", checked=False)
        cb.toggle()
        assert cb.checked is True
        cb.toggle()
        assert cb.checked is False

    def test_checkbox_click_toggles(self):
        """Test that clicking toggles the checkbox."""
        cb = Checkbox(10, 20, 100, 24, "Option", checked=False)
        cb.on_click(50, 30)
        assert cb.checked is True

    def test_checkbox_on_change_callback(self):
        """Test checkbox change callback."""
        changes = []

        def callback(checked):
            changes.append(checked)

        cb = Checkbox(10, 20, 100, 24, "Option", on_change=callback)
        cb.toggle()
        assert changes == [True]
        cb.toggle()
        assert changes == [True, False]


class TestRadioButton:
    """Tests for RadioButton and RadioGroup."""

    def test_radio_group_selection(self):
        """Test radio group mutual exclusivity."""
        group = RadioGroup()

        rb1 = RadioButton(10, 20, 100, 24, "A", selected=True)
        rb2 = RadioButton(10, 50, 100, 24, "B")
        rb3 = RadioButton(10, 80, 100, 24, "C")

        group.add_button(rb1)
        group.add_button(rb2)
        group.add_button(rb3)

        assert rb1.selected is True
        assert rb2.selected is False
        assert rb3.selected is False

        rb2.select()
        assert rb1.selected is False
        assert rb2.selected is True
        assert rb3.selected is False

    def test_radio_group_selected_value(self):
        """Test getting selected value from group."""
        group = RadioGroup()

        rb1 = RadioButton(10, 20, 100, 24, "Option A")
        rb2 = RadioButton(10, 50, 100, 24, "Option B")

        group.add_button(rb1)
        group.add_button(rb2)

        rb1.select()
        assert group.selected_value == "Option A"
        assert group.selected_index == 0

        rb2.select()
        assert group.selected_value == "Option B"
        assert group.selected_index == 1

    def test_radio_click_selects(self):
        """Test that clicking a radio button selects it."""
        group = RadioGroup()
        rb1 = RadioButton(10, 20, 100, 24, "A", selected=True)
        rb2 = RadioButton(10, 50, 100, 24, "B")

        group.add_button(rb1)
        group.add_button(rb2)

        rb2.on_click(50, 60)
        assert rb2.selected is True
        assert rb1.selected is False


class TestTextInput:
    """Tests for the TextInput component."""

    def test_text_input_creation(self):
        """Test creating a text input."""
        ti = TextInput(10, 20, 150, 28, placeholder="Enter...")
        assert ti.text == ""
        assert ti.placeholder == "Enter..."
        assert ti.cursor_pos == 0
        assert ti.has_focus is False

    def test_text_input_focus(self):
        """Test focusing/unfocusing text input."""
        ti = TextInput(10, 20, 150, 28)
        ti.focus()
        assert ti.has_focus is True
        assert ti.state == ComponentState.FOCUSED

        ti.blur()
        assert ti.has_focus is False
        assert ti.state == ComponentState.NORMAL

    def test_text_input_insert_char(self):
        """Test inserting characters."""
        ti = TextInput(10, 20, 150, 28)
        ti.focus()
        ti.insert_char('H')
        ti.insert_char('i')
        assert ti.text == "Hi"
        assert ti.cursor_pos == 2

    def test_text_input_delete_char(self):
        """Test deleting characters (backspace)."""
        ti = TextInput(10, 20, 150, 28)
        ti.focus()
        ti.insert_char('A')
        ti.insert_char('B')
        ti.insert_char('C')
        ti.delete_char()
        assert ti.text == "AB"
        assert ti.cursor_pos == 2

    def test_text_input_cursor_movement(self):
        """Test cursor movement."""
        ti = TextInput(10, 20, 150, 28)
        ti.focus()
        ti.insert_char('A')
        ti.insert_char('B')
        ti.insert_char('C')

        ti.move_cursor_left()
        assert ti.cursor_pos == 2

        ti.move_cursor_left()
        assert ti.cursor_pos == 1

        ti.move_cursor_right()
        assert ti.cursor_pos == 2

    def test_text_input_max_length(self):
        """Test max length constraint."""
        ti = TextInput(10, 20, 150, 28, max_length=3)
        ti.focus()
        ti.insert_char('A')
        ti.insert_char('B')
        ti.insert_char('C')
        ti.insert_char('D')  # Should be ignored
        assert ti.text == "ABC"

    def test_text_input_click_focuses(self):
        """Test that clicking focuses the input."""
        ti = TextInput(10, 20, 150, 28)
        ti.on_click(50, 30)
        assert ti.has_focus is True


class TestSlider:
    """Tests for the Slider component."""

    def test_slider_creation(self):
        """Test creating a slider."""
        slider = Slider(10, 20, 100, 20, min_value=0, max_value=100, value=50)
        assert slider.value == 50
        assert slider.min_value == 0
        assert slider.max_value == 100

    def test_slider_percentage(self):
        """Test slider percentage calculation."""
        slider = Slider(10, 20, 100, 20, min_value=0, max_value=100, value=25)
        assert slider.percentage == 25.0

        slider = Slider(10, 20, 100, 20, min_value=50, max_value=150, value=100)
        assert slider.percentage == 50.0

    def test_slider_value_clamping(self):
        """Test that slider values are clamped."""
        slider = Slider(10, 20, 100, 20, min_value=0, max_value=100, value=50)
        slider.value = 150
        assert slider.value == 100

        slider.value = -50
        assert slider.value == 0

    def test_slider_click_sets_value(self):
        """Test that clicking sets the slider value."""
        slider = Slider(10, 20, 100, 20, min_value=0, max_value=100, value=0)
        # Click at middle of slider
        slider.on_click(60, 30)  # 50% of the way across
        assert slider.value == 50.0

    def test_slider_on_change_callback(self):
        """Test slider change callback."""
        values = []

        def callback(value):
            values.append(value)

        slider = Slider(10, 20, 100, 20, on_change=callback)
        slider.value = 75
        assert values == [75]


class TestProgressBar:
    """Tests for the ProgressBar component."""

    def test_progress_bar_creation(self):
        """Test creating a progress bar."""
        pb = ProgressBar(10, 20, 150, 24, value=50)
        assert pb.value == 50
        assert pb.percentage == 50.0

    def test_progress_bar_increment(self):
        """Test incrementing progress."""
        pb = ProgressBar(10, 20, 150, 24, value=50)
        pb.increment(10)
        assert pb.value == 60

    def test_progress_bar_value_clamping(self):
        """Test that progress values are clamped."""
        pb = ProgressBar(10, 20, 150, 24, value=50)
        pb.value = 150
        assert pb.value == 100

        pb.value = -50
        assert pb.value == 0


class TestListBox:
    """Tests for the ListBox component."""

    def test_listbox_creation(self):
        """Test creating a list box."""
        lb = ListBox(10, 20, 120, 100, items=["A", "B", "C"])
        assert len(lb.items) == 3
        assert lb.selected_index == -1

    def test_listbox_select_item(self):
        """Test selecting an item."""
        lb = ListBox(10, 20, 120, 100, items=["A", "B", "C"])
        lb.select_index(1)
        assert lb.selected_index == 1
        assert lb.selected_item.label == "B"
        assert lb.value == "B"

    def test_listbox_add_item(self):
        """Test adding items."""
        lb = ListBox(10, 20, 120, 100)
        lb.add_item("Item 1")
        lb.add_item("Item 2", "value2")
        assert len(lb.items) == 2
        assert lb.items[1].value == "value2"

    def test_listbox_click_selects(self):
        """Test that clicking selects an item."""
        lb = ListBox(10, 20, 120, 100, items=["A", "B", "C"])
        # Click on second item (y=20 + item_height)
        lb.on_click(50, 20 + lb.item_height)
        assert lb.selected_index == 1


class TestWindow:
    """Tests for the Window container."""

    def test_window_creation(self):
        """Test creating a window."""
        w = Window(title="Test", x=10, y=20, width=200, height=150)
        assert w.title == "Test"
        assert w.x == 10
        assert w.y == 20
        assert len(w.components) == 0

    def test_window_add_component(self):
        """Test adding components to a window."""
        w = Window(title="Test", x=10, y=20, width=200, height=150)
        btn = Button(20, 40, 80, 30, "Click")
        w.add_component(btn)
        assert len(w.components) == 1

    def test_window_contains_point(self):
        """Test window hit testing."""
        w = Window(title="Test", x=10, y=20, width=200, height=150)
        assert w.contains_point(50, 50) is True
        assert w.contains_point(5, 50) is False

    def test_window_get_component_at(self):
        """Test getting component at position."""
        w = Window(title="Test", x=0, y=0, width=200, height=150)
        btn = Button(10, 30, 80, 30, "Click")
        w.add_component(btn)

        component = w.get_component_at(50, 45)
        assert component is btn

        component = w.get_component_at(100, 45)
        assert component is None


class TestGUIState:
    """Tests for the GUIState class."""

    def test_gui_state_add_window(self):
        """Test adding windows to GUI state."""
        gui = GUIState()
        w = Window(title="Test", x=10, y=20, width=200, height=150)
        gui.add_window(w)
        assert len(gui.windows) == 1
        # Window is not active until focused via keyboard navigation
        assert w.active is False

    def test_gui_state_get_window_at(self):
        """Test getting window at position."""
        gui = GUIState()
        w1 = Window(title="W1", x=0, y=0, width=100, height=100)
        w2 = Window(title="W2", x=100, y=0, width=100, height=100)
        gui.add_window(w1)
        gui.add_window(w2)

        assert gui.get_window_at(50, 50) is w1
        assert gui.get_window_at(150, 50) is w2
        assert gui.get_window_at(250, 50) is None

    def test_gui_state_handle_click(self):
        """Test handling clicks on components."""
        gui = GUIState()
        w = Window(title="Test", x=0, y=0, width=200, height=150)
        btn = Button(10, 30, 80, 30, "Click")
        w.add_component(btn)
        gui.add_window(w)

        component = gui.handle_click(50, 45)
        assert component is btn
        assert btn.toggled is True

    def test_gui_state_handle_key(self):
        """Test handling key input for focused component."""
        gui = GUIState()
        w = Window(title="Test", x=0, y=0, width=200, height=150)
        ti = TextInput(10, 30, 100, 28)
        w.add_component(ti)
        gui.add_window(w)

        # Focus the text input via keyboard navigation
        gui.focus_next()
        assert ti.has_focus is True

        # Type a character
        gui.handle_key('A')
        assert ti.text == "A"


class TestImageDisplay:
    """Tests for the ImageDisplay component."""

    def test_image_display_creation(self):
        """Test creating an image display without an image."""
        img = ImageDisplay(10, 20, 100, 80)
        assert img.x == 10
        assert img.y == 20
        assert img.width == 100
        assert img.height == 80
        assert img.zoom_level == 0
        assert img.zoom_factor == 1.0
        assert img.image_data is None
        assert img.indexed_data is None

    def test_image_display_with_image(self):
        """Test creating an image display with a valid image."""
        image_path = Path(__file__).parent.parent / "demo" / "squirel.png"
        img = ImageDisplay(10, 20, 100, 80, image_path=str(image_path))
        assert img.image_data is not None
        assert img.image_width == 256
        assert img.image_height == 256

    def test_image_display_zoom_in(self):
        """Test zooming in."""
        img = ImageDisplay(10, 20, 100, 80)
        assert img.zoom_level == 0
        assert img.zoom_factor == 1.0

        result = img.zoom_in()
        assert result is True
        assert img.zoom_level == 1
        assert img.zoom_factor == 2.0

        img.zoom_in()
        assert img.zoom_level == 2
        assert img.zoom_factor == 4.0

    def test_image_display_zoom_out(self):
        """Test zooming out."""
        img = ImageDisplay(10, 20, 100, 80)

        result = img.zoom_out()
        assert result is True
        assert img.zoom_level == -1
        assert img.zoom_factor == 0.5

        img.zoom_out()
        assert img.zoom_level == -2
        assert img.zoom_factor == 0.25

    def test_image_display_zoom_limits(self):
        """Test zoom limits."""
        img = ImageDisplay(10, 20, 100, 80)

        # Zoom out to minimum
        for _ in range(10):
            img.zoom_out()
        assert img.zoom_level == ImageDisplay.MIN_ZOOM_LEVEL

        # Try to zoom out past minimum
        result = img.zoom_out()
        assert result is False
        assert img.zoom_level == ImageDisplay.MIN_ZOOM_LEVEL

        # Reset and zoom in to maximum
        img._zoom_level = 0
        for _ in range(10):
            img.zoom_in()
        assert img.zoom_level == ImageDisplay.MAX_ZOOM_LEVEL

        # Try to zoom in past maximum
        result = img.zoom_in()
        assert result is False
        assert img.zoom_level == ImageDisplay.MAX_ZOOM_LEVEL

    def test_image_display_zoom_callback(self):
        """Test zoom callback is called."""
        zoom_levels = []

        def on_zoom(level):
            zoom_levels.append(level)

        img = ImageDisplay(10, 20, 100, 80, on_zoom=on_zoom)
        img.zoom_in()
        img.zoom_in()
        img.zoom_out()

        assert zoom_levels == [1, 2, 1]

    def test_image_display_on_click(self):
        """Test that on_click does nothing (image display is not clickable)."""
        img = ImageDisplay(10, 20, 100, 80)
        # Should not raise
        img.on_click(50, 50)

    def test_image_display_indexed_data_setter(self):
        """Test setting indexed data cache."""
        img = ImageDisplay(10, 20, 100, 80)
        assert img.indexed_data is None

        test_data = [[1, 2], [3, 4]]
        img.indexed_data = test_data
        assert img.indexed_data == test_data

    def test_image_display_invalid_path(self):
        """Test creating an image display with invalid path."""
        img = ImageDisplay(10, 20, 100, 80, image_path="/nonexistent/path.png")
        assert img.image_data is None
        assert img.image_width == 0
        assert img.image_height == 0

    def test_image_display_image_path_property(self):
        """Test image_path property."""
        img = ImageDisplay(10, 20, 100, 80, image_path="/some/path.png")
        assert img.image_path == "/some/path.png"


class TestGUIStateImageDisplay:
    """Tests for GUIState with ImageDisplay component."""

    def test_handle_special_key_image_display_zoom_in(self):
        """Test arrow keys zoom in on ImageDisplay."""
        gui = GUIState()
        w = Window(title="Test", x=0, y=0, width=200, height=150)
        img = ImageDisplay(10, 30, 100, 80)
        w.add_component(img)
        gui.add_window(w)

        # Focus the image display
        gui.focus_next()

        # Up arrow should zoom in
        result = gui.handle_special_key('up')
        assert result is True
        assert img.zoom_level == 1

        # Right arrow should also zoom in
        result = gui.handle_special_key('right')
        assert result is True
        assert img.zoom_level == 2

    def test_handle_special_key_image_display_zoom_out(self):
        """Test arrow keys zoom out on ImageDisplay."""
        gui = GUIState()
        w = Window(title="Test", x=0, y=0, width=200, height=150)
        img = ImageDisplay(10, 30, 100, 80)
        w.add_component(img)
        gui.add_window(w)

        # Focus the image display
        gui.focus_next()

        # Down arrow should zoom out
        result = gui.handle_special_key('down')
        assert result is True
        assert img.zoom_level == -1

        # Left arrow should also zoom out
        result = gui.handle_special_key('left')
        assert result is True
        assert img.zoom_level == -2
