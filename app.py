#!/usr/bin/env python3

import math
import time
from dataclasses import dataclass
from enum import Enum

import cairo
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")

from gi.repository import Gdk, Gio, Gtk, Pango, PangoCairo


class Tool(Enum):
    ARROW = "arrow"
    RECTANGLE = "rectangle"
    CIRCLE = "circle"
    TEXT = "text"


@dataclass
class Shape:
    tool: Tool
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    color: tuple[float, float, float, float]
    line_width: float = 4.0
    text: str = ""
    font_size: int = 24


class DrawingCanvas(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_draw_func(self.on_draw)
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_focusable(True)

        self.shapes: list[Shape] = []
        self.preview_shape: Shape | None = None
        self.current_tool = Tool.ARROW
        self.current_color = (1.0, 0.2, 0.2, 0.95)
        self.drag_start: tuple[float, float] | None = None
        self.cursor_x = 0.0
        self.cursor_y = 0.0
        self.pending_text: Shape | None = None
        self.toolbar_avoidance_callback = None

        click = Gtk.GestureClick(button=1)
        click.connect("pressed", self.on_pressed)
        click.connect("released", self.on_released)
        self.add_controller(click)

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_motion)
        self.add_controller(motion)

    def set_tool(self, tool: Tool):
        self.current_tool = tool

    def set_color(self, rgba: Gdk.RGBA):
        self.current_color = (rgba.red, rgba.green, rgba.blue, rgba.alpha)

    def set_toolbar_avoidance_callback(self, callback):
        self.toolbar_avoidance_callback = callback

    def undo(self):
        if self.shapes:
            self.shapes.pop()
            self.queue_draw()

    def clear(self):
        self.shapes.clear()
        self.preview_shape = None
        self.pending_text = None
        self.queue_draw()

    def on_pressed(self, _gesture, _n_press, x, y):
        if self.current_tool == Tool.TEXT:
            if self.pending_text:
                placed = Shape(
                    tool=Tool.TEXT,
                    start_x=x,
                    start_y=y,
                    end_x=x,
                    end_y=y,
                    color=self.pending_text.color,
                    text=self.pending_text.text,
                    font_size=self.pending_text.font_size,
                )
                self.shapes.append(placed)
                self.pending_text = None
                self.preview_shape = None
                self.queue_draw()
            return

        self.drag_start = (x, y)
        self.preview_shape = Shape(
            tool=self.current_tool,
            start_x=x,
            start_y=y,
            end_x=x,
            end_y=y,
            color=self.current_color,
        )
        self.queue_draw()

    def on_motion(self, _controller, x, y):
        self.cursor_x = x
        self.cursor_y = y

        if self.current_tool == Tool.TEXT and self.pending_text:
            if self.toolbar_avoidance_callback:
                self.toolbar_avoidance_callback(x, y)
            self.preview_shape = Shape(
                tool=Tool.TEXT,
                start_x=x,
                start_y=y,
                end_x=x,
                end_y=y,
                color=self.pending_text.color,
                text=self.pending_text.text,
                font_size=self.pending_text.font_size,
            )
            self.queue_draw()
            return

        if not self.drag_start or not self.preview_shape:
            return

        if self.toolbar_avoidance_callback:
            self.toolbar_avoidance_callback(x, y)

        self.preview_shape.end_x = x
        self.preview_shape.end_y = y
        self.queue_draw()

    def on_released(self, _gesture, _n_press, x, y):
        if not self.drag_start or not self.preview_shape:
            return

        self.preview_shape.end_x = x
        self.preview_shape.end_y = y
        self.shapes.append(self.preview_shape)
        self.preview_shape = None
        self.drag_start = None
        self.queue_draw()

    def begin_text_placement(self, text: str, font_size: int):
        clean_text = text.rstrip()
        if not clean_text:
            return

        self.current_tool = Tool.TEXT
        self.pending_text = Shape(
            tool=Tool.TEXT,
            start_x=self.cursor_x,
            start_y=self.cursor_y,
            end_x=self.cursor_x,
            end_y=self.cursor_y,
            color=self.current_color,
            text=clean_text,
            font_size=font_size,
        )
        self.preview_shape = Shape(
            tool=Tool.TEXT,
            start_x=self.cursor_x,
            start_y=self.cursor_y,
            end_x=self.cursor_x,
            end_y=self.cursor_y,
            color=self.current_color,
            text=clean_text,
            font_size=font_size,
        )
        self.queue_draw()

    def cancel_text_placement(self):
        self.pending_text = None
        if self.preview_shape and self.preview_shape.tool == Tool.TEXT:
            self.preview_shape = None
        self.queue_draw()

    def on_draw(self, _area, cr, _width, _height):
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        for shape in self.shapes:
            self.draw_shape(cr, shape)

        if self.preview_shape:
            self.draw_shape(cr, self.preview_shape, preview=True)

    def draw_shape(self, cr, shape: Shape, preview: bool = False):
        r, g, b, a = shape.color
        cr.set_source_rgba(r, g, b, a * (0.55 if preview else 1.0))
        cr.set_line_width(shape.line_width)

        if shape.tool == Tool.RECTANGLE:
            x = min(shape.start_x, shape.end_x)
            y = min(shape.start_y, shape.end_y)
            w = abs(shape.end_x - shape.start_x)
            h = abs(shape.end_y - shape.start_y)
            cr.rectangle(x, y, w, h)
            cr.stroke()
            return

        if shape.tool == Tool.CIRCLE:
            cx = (shape.start_x + shape.end_x) / 2
            cy = (shape.start_y + shape.end_y) / 2
            rx = abs(shape.end_x - shape.start_x) / 2
            ry = abs(shape.end_y - shape.start_y) / 2
            cr.save()
            cr.translate(cx, cy)
            if rx > 0 and ry > 0:
                cr.scale(rx, ry)
                cr.arc(0, 0, 1, 0, 2 * math.pi)
            cr.restore()
            cr.stroke()
            return

        if shape.tool == Tool.ARROW:
            self.draw_arrow(cr, shape)
            return

        if shape.tool == Tool.TEXT and shape.text:
            self.draw_text(cr, shape)

    def draw_arrow(self, cr, shape: Shape):
        sx, sy, ex, ey = shape.start_x, shape.start_y, shape.end_x, shape.end_y
        cr.move_to(sx, sy)
        cr.line_to(ex, ey)
        cr.stroke()

        angle = math.atan2(ey - sy, ex - sx)
        head_len = 18
        head_angle = math.pi / 7

        left_x = ex - head_len * math.cos(angle - head_angle)
        left_y = ey - head_len * math.sin(angle - head_angle)
        right_x = ex - head_len * math.cos(angle + head_angle)
        right_y = ey - head_len * math.sin(angle + head_angle)

        cr.move_to(ex, ey)
        cr.line_to(left_x, left_y)
        cr.move_to(ex, ey)
        cr.line_to(right_x, right_y)
        cr.stroke()

    def draw_text(self, cr, shape: Shape):
        layout = PangoCairo.create_layout(cr)
        layout.set_text(shape.text, -1)
        desc = Pango.FontDescription(f"Sans Bold {shape.font_size}")
        layout.set_font_description(desc)
        layout.set_wrap(Pango.WrapMode.WORD_CHAR)

        cr.move_to(shape.start_x, shape.start_y)
        PangoCairo.show_layout(cr, layout)


class TextEditorWindow(Gtk.Window):
    def __init__(self, parent: Gtk.Window, canvas: DrawingCanvas):
        super().__init__(title="Text Editor", transient_for=parent, modal=False)
        self.canvas = canvas
        self.set_default_size(380, 280)
        self.set_resizable(True)
        self.add_css_class("editor-window")

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_margin_top(12)
        outer.set_margin_bottom(12)
        outer.set_margin_start(12)
        outer.set_margin_end(12)
        self.set_child(outer)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        outer.append(controls)

        size_label = Gtk.Label(label="Font Size")
        controls.append(size_label)

        adjustment = Gtk.Adjustment(value=24, lower=10, upper=144, step_increment=1, page_increment=4)
        self.font_size = Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
        controls.append(self.font_size)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        outer.append(scroll)

        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.set_top_margin(10)
        self.text_view.set_bottom_margin(10)
        self.text_view.set_left_margin(10)
        self.text_view.set_right_margin(10)
        scroll.set_child(self.text_view)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        outer.append(actions)

        cancel = Gtk.Button(label="Cancel")
        cancel.connect("clicked", lambda *_: self.close())
        actions.append(cancel)

        drop = Gtk.Button(label="Drop")
        drop.add_css_class("suggested-action")
        drop.connect("clicked", self.on_drop_clicked)
        actions.append(drop)

        self.connect("close-request", self.on_close_request)

    def on_drop_clicked(self, _button):
        buffer = self.text_view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        self.canvas.begin_text_placement(text, self.font_size.get_value_as_int())
        self.close()

    def on_close_request(self, _window):
        self.canvas.grab_focus()
        return False


class Toolbar(Gtk.Box):
    def __init__(self, canvas: DrawingCanvas, window: Gtk.ApplicationWindow):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.canvas = canvas
        self.window = window
        self.tool_buttons: dict[Tool, Gtk.Button] = {}

        self.add_css_class("toolbar-panel")

        tool_buttons = [
            ("Arrow", Tool.ARROW),
            ("Rectangle", Tool.RECTANGLE),
            ("Circle", Tool.CIRCLE),
            ("Text", Tool.TEXT),
        ]

        for label, tool in tool_buttons:
            button = Gtk.Button(label=label)
            button.connect("clicked", self.on_tool_clicked, tool)
            self.tool_buttons[tool] = button
            self.append(button)

        color_button = Gtk.ColorDialogButton.new(Gtk.ColorDialog())
        rgba = Gdk.RGBA()
        rgba.parse("rgba(255, 51, 51, 0.95)")
        color_button.set_rgba(rgba)
        color_button.connect("notify::rgba", self.on_color_changed)
        self.append(color_button)

        undo = Gtk.Button(label="Undo")
        undo.connect("clicked", lambda *_: self.canvas.undo())
        self.append(undo)

        clear = Gtk.Button(label="Clear")
        clear.connect("clicked", lambda *_: self.canvas.clear())
        self.append(clear)

        move_bar = Gtk.Button(label="Move Bar")
        move_bar.connect("clicked", self.on_move_bar_clicked)
        self.append(move_bar)

        collapse = Gtk.Button(label="Collapse")
        collapse.connect("clicked", self.on_collapse_clicked)
        self.append(collapse)

        quit_btn = Gtk.Button(label="Quit")
        quit_btn.connect("clicked", lambda *_: self.window.close())
        self.append(quit_btn)

        self.update_active_tool(self.canvas.current_tool)

    def on_tool_clicked(self, _button, tool: Tool):
        self.canvas.set_tool(tool)
        self.update_active_tool(tool)
        if tool == Tool.TEXT:
            editor = TextEditorWindow(self.window, self.canvas)
            editor.present()

    def on_color_changed(self, button, _pspec):
        self.canvas.set_color(button.get_rgba())

    def on_move_bar_clicked(self, _button):
        self.window.move_toolbar_clockwise()

    def on_collapse_clicked(self, _button):
        self.window.set_toolbar_collapsed(True)

    def update_active_tool(self, active_tool: Tool):
        for tool, button in self.tool_buttons.items():
            if tool == active_tool:
                button.add_css_class("tool-active")
            else:
                button.remove_css_class("tool-active")


class ToolbarRestoreButton(Gtk.Button):
    def __init__(self, window: Gtk.ApplicationWindow):
        super().__init__(label="WyMakeup")
        self.window = window
        self.add_css_class("toolbar-restore")
        self.connect("clicked", self.on_clicked)

        right_click = Gtk.GestureClick(button=3)
        right_click.connect("pressed", self.on_right_click)
        self.add_controller(right_click)

        hover = Gtk.EventControllerMotion()
        hover.connect("enter", self.on_hover_enter)
        hover.connect("leave", self.on_hover_leave)
        self.add_controller(hover)

    def on_clicked(self, _button):
        self.window.show_restore_hint(False)
        self.window.set_toolbar_collapsed(False)

    def on_right_click(self, _gesture, _n_press, _x, _y):
        self.window.show_restore_hint(False)
        self.window.move_toolbar_clockwise()

    def on_hover_enter(self, _controller, _x, _y):
        self.window.show_restore_hint(True)

    def on_hover_leave(self, _controller):
        self.window.show_restore_hint(False)


class RestoreHint(Gtk.Label):
    def __init__(self):
        super().__init__(label="Left click: restore  |  Right click: move")
        self.add_css_class("restore-hint")
        self.set_visible(False)


class WayMarkWindow(Gtk.ApplicationWindow):
    def __init__(self, app: Gtk.Application):
        super().__init__(application=app, title="WayMarkup")
        self.set_default_size(1400, 900)
        self.fullscreen()
        self.set_decorated(False)
        self.toolbar_corner = 2
        self.last_toolbar_move_at = 0.0
        self.toolbar_collapsed = False
        self.add_css_class("overlay-window")

        overlay = Gtk.Overlay()
        self.set_child(overlay)

        self.canvas = DrawingCanvas()
        self.canvas.set_toolbar_avoidance_callback(self.maybe_move_toolbar_away)
        overlay.set_child(self.canvas)

        toolbar = Toolbar(self.canvas, self)
        self.toolbar = toolbar
        overlay.add_overlay(toolbar)

        restore_button = ToolbarRestoreButton(self)
        self.restore_button = restore_button
        overlay.add_overlay(restore_button)
        self.restore_button.set_visible(False)

        restore_hint = RestoreHint()
        self.restore_hint = restore_hint
        overlay.add_overlay(restore_hint)

        self.position_toolbar()

        shortcut_controller = Gtk.ShortcutController()
        self.add_controller(shortcut_controller)

        self.add_shortcut(shortcut_controller, "<Ctrl>z", self.canvas.undo)
        self.add_shortcut(shortcut_controller, "Delete", self.canvas.clear)
        self.add_shortcut(shortcut_controller, "Escape", self.on_escape_pressed)

    def add_shortcut(self, controller, trigger: str, callback):
        shortcut = Gtk.Shortcut.new(
            Gtk.ShortcutTrigger.parse_string(trigger),
            Gtk.CallbackAction.new(lambda *_: (callback(), True)[1]),
        )
        controller.add_shortcut(shortcut)

    def on_escape_pressed(self):
        if self.canvas.pending_text:
            self.canvas.cancel_text_placement()
            return
        self.close()

    def move_toolbar_clockwise(self):
        self.toolbar_corner = (self.toolbar_corner + 1) % 4
        self.last_toolbar_move_at = time.monotonic()
        self.position_toolbar()

    def set_toolbar_collapsed(self, collapsed: bool):
        self.toolbar_collapsed = collapsed
        self.toolbar.set_visible(not collapsed)
        self.restore_button.set_visible(collapsed)
        if not collapsed:
            self.show_restore_hint(False)
        self.position_toolbar()

    def position_toolbar(self):
        margin = 18
        corners = [
            (Gtk.Align.START, Gtk.Align.START),
            (Gtk.Align.END, Gtk.Align.START),
            (Gtk.Align.END, Gtk.Align.END),
            (Gtk.Align.START, Gtk.Align.END),
        ]
        halign, valign = corners[self.toolbar_corner]
        self.toolbar.set_halign(halign)
        self.toolbar.set_valign(valign)
        self.toolbar.set_margin_start(margin if halign == Gtk.Align.START else 0)
        self.toolbar.set_margin_end(margin if halign == Gtk.Align.END else 0)
        self.toolbar.set_margin_top(margin if valign == Gtk.Align.START else 0)
        self.toolbar.set_margin_bottom(margin if valign == Gtk.Align.END else 0)

        self.restore_button.set_halign(halign)
        self.restore_button.set_valign(valign)
        self.restore_button.set_margin_start(margin if halign == Gtk.Align.START else 0)
        self.restore_button.set_margin_end(margin if halign == Gtk.Align.END else 0)
        self.restore_button.set_margin_top(margin if valign == Gtk.Align.START else 0)
        self.restore_button.set_margin_bottom(margin if valign == Gtk.Align.END else 0)

        hint_margin_x = 110
        hint_margin_y = 78
        self.restore_hint.set_halign(halign)
        self.restore_hint.set_valign(valign)
        self.restore_hint.set_margin_start(hint_margin_x if halign == Gtk.Align.START else 0)
        self.restore_hint.set_margin_end(hint_margin_x if halign == Gtk.Align.END else 0)
        self.restore_hint.set_margin_top(hint_margin_y if valign == Gtk.Align.START else 0)
        self.restore_hint.set_margin_bottom(hint_margin_y if valign == Gtk.Align.END else 0)

    def show_restore_hint(self, visible: bool):
        self.restore_hint.set_visible(visible and self.toolbar_collapsed)

    def maybe_move_toolbar_away(self, cursor_x: float, cursor_y: float):
        if time.monotonic() - self.last_toolbar_move_at < 0.55:
            return

        width = self.canvas.get_width()
        height = self.canvas.get_height()
        tracked_widget = self.restore_button if self.toolbar_collapsed else self.toolbar
        toolbar_width = max(tracked_widget.get_width(), 1)
        toolbar_height = max(tracked_widget.get_height(), 1)

        if width <= 0 or height <= 0 or toolbar_width <= 0 or toolbar_height <= 0:
            return

        margin = 18
        if self.toolbar_corner in (0, 3):
            left = margin
            right = margin + toolbar_width
        else:
            left = width - margin - toolbar_width
            right = width - margin

        if self.toolbar_corner in (0, 1):
            top = margin
            bottom = margin + toolbar_height
        else:
            top = height - margin - toolbar_height
            bottom = height - margin

        padding = 80
        if left - padding <= cursor_x <= right + padding and top - padding <= cursor_y <= bottom + padding:
            self.move_toolbar_clockwise()


class WayMarkApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.wymakeup.WayMarkup", flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        css = Gtk.CssProvider()
        css.load_from_data(
            b"""
            window.overlay-window {
                background-color: transparent;
            }

            window.editor-window {
                background: #f4f1ea;
                color: #161616;
            }

            .toolbar-panel {
                background: rgba(24, 24, 24, 0.78);
                border-radius: 16px;
                padding: 12px;
            }

            .toolbar-restore {
                min-height: 46px;
                min-width: 76px;
                background: rgba(24, 24, 24, 0.82);
                color: #f7f7f7;
                border-radius: 999px;
                border: 1px solid rgba(255, 255, 255, 0.18);
            }

            .restore-hint {
                background: rgba(20, 20, 20, 0.88);
                color: #f8f8f8;
                padding: 8px 12px;
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 0.14);
            }

            .toolbar-panel button,
            .toolbar-panel colorswatch {
                min-height: 42px;
            }

            .toolbar-panel button.tool-active {
                background: linear-gradient(to bottom, rgba(255, 255, 255, 0.92), rgba(220, 220, 220, 0.92));
                color: #111;
                border: 1px solid rgba(0, 0, 0, 0.38);
                box-shadow:
                    inset 0 3px 6px rgba(255, 255, 255, 0.55),
                    inset 0 -3px 6px rgba(0, 0, 0, 0.18),
                    0 1px 0 rgba(255, 255, 255, 0.12);
            }
            """
        )
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        window = self.props.active_window
        if not window:
            window = WayMarkWindow(self)
        window.present()


def main():
    app = WayMarkApplication()
    raise SystemExit(app.run(None))


if __name__ == "__main__":
    main()
