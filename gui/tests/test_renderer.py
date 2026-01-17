"""
Tests for the GUI renderer module (renderer.py).

Tests cover:
- Renderer initialization
- Frame rendering
- Component rendering
- Window rendering
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer import GUIRenderer
from gui import (
    GUIState,
    Window,
    Button,
    Checkbox,
    RadioButton,
    RadioGroup,
    TextInput,
    Slider,
    ProgressBar,
    ListBox,
    ImageDisplay,
)
from sixel import SIXEL_START, SIXEL_END


class TestRendererInit:
    """Tests for renderer initialization."""

    def test_default_dimensions(self):
        """Test default renderer dimensions."""
        renderer = GUIRenderer()
        assert renderer.width == 1200
        assert renderer.height == 400

    def test_custom_dimensions(self):
        """Test custom renderer dimensions."""
        renderer = GUIRenderer(width=800, height=300)
        assert renderer.width == 800
        assert renderer.height == 300


class TestRenderFrame:
    """Tests for frame rendering."""

    def test_render_empty_gui(self):
        """Test rendering an empty GUI."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        frame = renderer.render_frame(gui)

        assert frame.startswith(SIXEL_START)
        assert frame.endswith(SIXEL_END)

    def test_render_with_window(self):
        """Test rendering GUI with a window."""
        renderer = GUIRenderer(width=300, height=200)
        gui = GUIState()
        window = Window(title="TEST", x=10, y=10, width=150, height=100)
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)
        assert frame.endswith(SIXEL_END)


class TestComponentRendering:
    """Tests for individual component rendering."""

    def test_render_button(self):
        """Test rendering a button."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        window.add_component(Button(10, 30, 80, 25, "CLICK"))
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_checkbox(self):
        """Test rendering a checkbox."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        window.add_component(Checkbox(10, 30, 100, 24, "CHECK", checked=True))
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_radio_button(self):
        """Test rendering radio buttons."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)

        group = RadioGroup()
        rb1 = RadioButton(10, 30, 100, 24, "A", selected=True)
        rb2 = RadioButton(10, 55, 100, 24, "B")
        group.add_button(rb1)
        group.add_button(rb2)

        window.add_component(rb1)
        window.add_component(rb2)
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_text_input(self):
        """Test rendering a text input."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        ti = TextInput(10, 30, 120, 28, placeholder="Type...")
        window.add_component(ti)
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_text_input_with_text(self):
        """Test rendering a text input with content."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        ti = TextInput(10, 30, 120, 28)
        ti.focus()
        ti.insert_char('H')
        ti.insert_char('i')
        window.add_component(ti)
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_slider(self):
        """Test rendering a slider."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        window.add_component(Slider(10, 30, 100, 20, value=50))
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_progress_bar(self):
        """Test rendering a progress bar."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)
        window.add_component(ProgressBar(10, 30, 150, 24, value=75))
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_listbox(self):
        """Test rendering a list box."""
        renderer = GUIRenderer(width=200, height=150)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=150)
        window.add_component(ListBox(10, 30, 100, 80, items=["A", "B", "C"]))
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_image_display_no_image(self):
        """Test rendering an image display without an image."""
        renderer = GUIRenderer(width=200, height=150)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=150)
        window.add_component(ImageDisplay(10, 30, 100, 80))
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_image_display_with_image(self):
        """Test rendering an image display with an image."""
        renderer = GUIRenderer(width=200, height=150)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=150)
        image_path = Path(__file__).parent.parent / "demo" / "squirel.png"
        window.add_component(ImageDisplay(10, 30, 140, 100, image_path=str(image_path)))
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_image_display_zoomed_in(self):
        """Test rendering an image display zoomed in."""
        renderer = GUIRenderer(width=200, height=150)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=150)
        image_path = Path(__file__).parent.parent / "demo" / "squirel.png"
        img = ImageDisplay(10, 30, 140, 100, image_path=str(image_path))
        img.zoom_in()  # 2x zoom
        window.add_component(img)
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)

    def test_render_image_display_zoomed_out(self):
        """Test rendering an image display zoomed out."""
        renderer = GUIRenderer(width=200, height=150)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=150)
        image_path = Path(__file__).parent.parent / "demo" / "squirel.png"
        img = ImageDisplay(10, 30, 140, 100, image_path=str(image_path))
        img.zoom_out()  # 0.5x zoom
        window.add_component(img)
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)


class TestMultipleWindows:
    """Tests for rendering multiple windows."""

    def test_render_multiple_windows(self):
        """Test rendering multiple windows."""
        renderer = GUIRenderer(width=400, height=200)
        gui = GUIState()

        w1 = Window(title="WINDOW 1", x=10, y=10, width=150, height=100)
        w1.add_component(Button(20, 40, 80, 25, "BTN1"))
        gui.add_window(w1)

        w2 = Window(title="WINDOW 2", x=170, y=10, width=150, height=100)
        w2.add_component(Button(180, 40, 80, 25, "BTN2"))
        gui.add_window(w2)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)
        assert frame.endswith(SIXEL_END)


class TestDisabledComponents:
    """Tests for rendering disabled components."""

    def test_render_disabled_button(self):
        """Test rendering a disabled button."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)

        btn = Button(10, 30, 80, 25, "DISABLED")
        btn.enabled = False
        window.add_component(btn)
        gui.add_window(window)

        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)


class TestHiddenComponents:
    """Tests for hidden components."""

    def test_hidden_component_not_rendered(self):
        """Test that hidden components are not rendered."""
        renderer = GUIRenderer(width=200, height=100)
        gui = GUIState()
        window = Window(title="TEST", x=0, y=0, width=200, height=100)

        btn = Button(10, 30, 80, 25, "HIDDEN")
        btn.visible = False
        window.add_component(btn)
        gui.add_window(window)

        # Should render without errors
        frame = renderer.render_frame(gui)
        assert frame.startswith(SIXEL_START)
