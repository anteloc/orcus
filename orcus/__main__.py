import json
import os
import platform
import sys
import tempfile
from functools import partial

from PIL import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image as KImage
from kivy.graphics import Color, Rectangle as KRectangle, Line
from kivy.properties import ObjectProperty, get_color_from_hex, BoundedNumericProperty
from kivy.uix.settings import (
    SettingsWithSidebar,
    SettingsWithNoMenu,
    SettingsWithSpinner,
    SettingsWithTabbedPanel,
)
from kivy.vector import Vector
from pytesseract import pytesseract

from orcus.util import kivy_to_std_rect_xy, min_rect_xy_containing, normalize_rect_xy

OS = platform.system().lower()

from kivy.config import Config

if OS != "windows":
    # On Windows OS, hiding the window causes sometimes
    # crashes due to "0" values in properties like width, height, etc.
    Config.set("graphics", "window_state", "hidden")

# Disable touchpads behaving like touchscreens
Config.set("input", "%(name)s", None)
Config.set("input", "mouse", "mouse,disable_multitouch")
Config.set("graphics", "multisamples", "10")

from kivy.app import App
from kivy.logger import Logger
from kivy.resources import resource_add_path, resource_find
from collections import OrderedDict

from kivy.app import App
from kivy.metrics import sp
from kivy.properties import (
    ObjectProperty,
    NumericProperty,
    ListProperty,
    StringProperty,
    BooleanProperty,
)

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from orcus.util import (
    find_current_monitor_info,
    BackgroundScreenshotHandler,
    DEFAULT_CONFIG_SECTIONS,
    CONFIG_PANEL_SECTIONS,
    rect_tl_br,
    kivy_to_std_xy,
)
from orcus.shapes import Rectangle, MarkerRectangle


class PopupHelp(Popup):
    font_size = NumericProperty(sp(18))

    def __init__(self, *args, **kwargs):
        super(PopupHelp, self).__init__(*args, **kwargs)

        self._app = App.get_running_app()
        shortcuts_opts = self._app.config.options("keyboard.shortcuts")

        openapi_api_key = self._app.config.get("openai", "openai_api_key")

        help_item = partial(Label, size_hint_y=None, height=44, markup=True)

        valid_openapi_api_key = (
            openapi_api_key is not None
            and openapi_api_key.strip()
            and openapi_api_key != "<your OPENAI_API_KEY>"
        )

        if not valid_openapi_api_key:
            self.ids.scroll_content.add_widget(
                help_item(
                    text=f"[b][color=#ff0000]WARNING:[/color][/b] Configure OpenAI API key in Settings menu"
                )
            )

        mouse_key, mouse_help = ("Mouse Left Click", "Draw/Select Rectangle")

        self.ids.scroll_content.add_widget(
            help_item(text=f"[b]{mouse_key}:[/b] {mouse_help}")
        )

        for key in shortcuts_opts:
            if key == "exit":
                continue

            shortcut_key = self._app.config.get("keyboard.shortcuts", key)
            shortcut_help = self._app.config.get("keyboard.shortcuts.help", key)

            self.ids.scroll_content.add_widget(
                help_item(text=f"[b]{shortcut_key}:[/b] {shortcut_help}")
            )

        exit_key = self._app.config.get("keyboard.shortcuts", "exit")
        exit_help = self._app.config.get("keyboard.shortcuts.help", "exit")

        self.ids.scroll_content.add_widget(
            help_item(text=f"[b]{exit_key}:[/b] {exit_help}")
        )


class PopupResults(Popup):
    font_size = NumericProperty(sp(15))
    text_ocr = StringProperty("N/A")
    text_gpt = StringProperty("N/A")
    text_expl_gpt = StringProperty("N/A")

    def __init__(
        self,
        text_ocr,
        text_gpt,
        text_expl_gpt,
        **kwargs,
    ):
        super(PopupResults, self).__init__(**kwargs)
        self.text_ocr = text_ocr if text_ocr else "N/A"
        self.text_gpt = text_gpt if text_gpt else "N/A"
        self.text_expl_gpt = text_expl_gpt if text_expl_gpt else "N/A"


class FakeDesktop(FloatLayout):
    background = ObjectProperty(None)
    autodetect_smoothness = BoundedNumericProperty(4, min=1, max=20)
    auto_mode = BooleanProperty(False)

    def __init__(self):
        super(FakeDesktop, self).__init__()
        self._rectangle_color = None
        self._rectangle_fade_duration = None
        self._rectangle_line_width = None
        self._show_help_key = None
        self._show_settings_key = None
        self._update_background_key = None
        self.auto_manual_mode = None
        self.increase_auto_tolerance = None
        self.decrease_auto_tolerance = None
        self._app = App.get_running_app()
        self._config = self._app.config
        self._bg_handler = None
        self._current_rectangle = None
        self._marker_rectangles = []
        self.help_visible = False

    def post_init(self):
        self.reload_config()

        self._bg_handler = BackgroundScreenshotHandler(self)
        self._bg_handler.take_screenshot()

        # Set bindings and initial values according to the mode
        self.on_auto_mode()

        self.show_help()

    def reload_config(self):
        sect = "keyboard.shortcuts"

        self._update_background_key = self._config.get(sect, "update_background")
        self._show_settings_key = self._config.get(sect, "show_settings")
        self._show_help_key = self._config.get(sect, "show_help")
        self._auto_manual_mode_key = self._config.get(sect, "auto_manual_mode")
        self._increase_auto_tolerance_key = self._config.get(
            sect, "increase_auto_tolerance"
        )
        self._decrease_auto_tolerance_key = self._config.get(
            sect, "decrease_auto_tolerance"
        )

        sect = "rectangle.attributes"

        self._rectangle_line_width = self._config.getint(sect, "rectangle_line_width")
        self._rectangle_fade_duration = self._config.getfloat(
            sect, "rectangle_fade_duration"
        )
        self._rectangle_color = get_color_from_hex(
            self._config.get(sect, "rectangle_color")
        )

    def on_auto_mode(self, *args):
        if self.auto_mode:
            Logger.debug("AUTO MODE")
            self.on_touch_down = self.on_touch_down_auto
            self.on_touch_up = self.on_touch_up_auto
            self.on_touch_move = self.on_touch_move_auto

            self._clear_current_rectangle()
            self._update_paragraph_markers()
        else:
            Logger.debug("MANUAL MODE")
            self.on_touch_down = self.on_touch_down_manual
            self.on_touch_up = self.on_touch_up_manual
            self.on_touch_move = self.on_touch_move_manual

            self._clear_marker_rectangles()

    def _clear_marker_rectangles(self):
        if self._marker_rectangles:
            for mr in self._marker_rectangles:
                self.remove_widget(mr)
            self._marker_rectangles = []

    def _clear_current_rectangle(self):
        if self._current_rectangle is not None:
            self.remove_widget(self._current_rectangle)
            self._current_rectangle.unbind(shape_faded=self.on_shape_faded)
            self._current_rectangle = None

    def on_background(self, *args):
        self._set_background(self.background)

        if self.auto_mode:
            self._update_paragraph_markers()

    def on_autodetect_smoothness(self, *args):
        self._update_paragraph_markers()

    def on_touch_down(self, touch):
        return False

    def on_touch_down_manual(self, touch):
        Logger.debug(
            f"on_touch_down_manual: {touch}, current_rectangle: {self._current_rectangle}"
        )
        if touch.button == "left" and self._current_rectangle is None:
            self._create_rectangle(touch.pos)
            return True
        return False

    def on_touch_down_auto(self, touch):
        Logger.debug(
            f"on_touch_down_auto: {touch.button}, marker_rectangles: {self._marker_rectangles}"
        )
        if touch.button == "left" and self._marker_rectangles:
            rects_xy = [mr.to_rect_xy() for mr in self._marker_rectangles]
            rects_xy = [normalize_rect_xy(r, kivy_rect=True) for r in rects_xy]
            min_rect_xy = min_rect_xy_containing(rects_xy, touch.pos, kivy_rect=True)

            if min_rect_xy is not None:
                x1, y1, x2, y2 = min_rect_xy
                text_ocr = self._ocr_region((x1, y1), (x2, y2))
                Logger.debug(f"AUTO OCR text: {text_ocr}")
                popup_results = PopupResults(text_ocr, None, None)
                popup_results.open()
            return True
        return False

    def on_touch_move(self, touch):
        return False

    def on_touch_move_auto(self, touch):
        return True

    def on_touch_move_manual(self, touch):
        # XXX Maybe this method is not needed because the rectangle widget takes care of on_touch_move itself
        if touch.button == "left" and self._current_rectangle:
            self._current_rectangle.on_touch_move(touch)
            return True
        return False

    def on_touch_up(self, touch):
        return False

    def on_touch_up_auto(self, touch):
        return True

    def on_touch_up_manual(self, touch):
        if touch.button == "left" and self._current_rectangle:
            self._current_rectangle.on_touch_up(touch)
            return True
        return False

    def on_shape_faded(self, instance, _):
        xy1 = instance.start_point
        xy2 = instance.end_point

        if xy1 != xy2:
            text_ocr = self._ocr_region(xy1, xy2)
            Logger.debug(f"MANUAL OCR text: {text_ocr}")
            popup_results = PopupResults(text_ocr, None, None)
            popup_results.open()
        self._clear_current_rectangle()

    def on_key_down(self, _keyboard, keycode, _text, _modifiers):
        key = keycode[1]

        if key == self._update_background_key:
            self.background.close()
            bg_handler = BackgroundScreenshotHandler(self)
            bg_handler.take_screenshot()
            return True
        elif key == self._show_settings_key:
            self._app.open_settings()
            return True
        elif key == self._show_help_key:
            self.show_help()
            return True
        elif key == self._auto_manual_mode_key:
            self.auto_mode = not self.auto_mode
            return True
        elif key == self._increase_auto_tolerance_key:
            self._modify_smoothness(1)
            return True
        elif key == self._decrease_auto_tolerance_key:
            self._modify_smoothness(-1)
            return True

        return False

    def on_key_up(self, *args):
        return True

    def show_help(self, *args):
        if not self.help_visible:
            self.help_visible = True
            help_popup = PopupHelp()

            def dismiss(*args):
                self.help_visible = False

            help_popup.bind(on_dismiss=dismiss)
            help_popup.open()

    def on_show_settings(self, *args):
        if self.show_settings:
            self._app.open_settings()
            self.show_settings = False

    def _create_rectangle(self, start_point):
        Logger.debug(f"_create_rectangle: {start_point}")
        # Create a new shape instance of the current type
        self._current_rectangle = Rectangle(
            start_point,
            self._rectangle_color,
            self._rectangle_line_width,
            fade_duration=self._rectangle_fade_duration,
            is_shadowed=False,
            is_frozen=False,
        )

        self._current_rectangle.bind(shape_faded=self.on_shape_faded)

        self.add_widget(self._current_rectangle)

    def _set_background(self, new_background):
        bg = new_background
        bg_size = Image.open(bg.name).size

        with self.canvas:
            Color(1, 1, 1, 1)
            KRectangle(source=bg.name, pos=(0, 0), size=bg_size)
            Color(1, 0, 0, 1)
            Line(rectangle=(0, 0, *bg_size), width=5)

        self.background = bg

    def _modify_smoothness(self, delta):
        try:
            self.autodetect_smoothness += delta
        except ValueError:
            pass

    def _ocr_region(self, xy1, xy2):
        Logger.debug(f"_ocr_region: {xy1}, {xy2}")
        bg_img = Image.open(self.background.name)

        kivy_rect_xy = normalize_rect_xy((*xy1, *xy2), kivy_rect=True)
        Logger.debug(f"_ocr_region kivy_rect_xy: {kivy_rect_xy}")

        # Kivy coord system to PIL coord system
        pil_rect_xy = kivy_to_std_rect_xy(kivy_rect_xy, bg_img.height)
        Logger.debug(f"_ocr_region pil_rect_xy: {pil_rect_xy}")

        ocr_target = bg_img.crop(pil_rect_xy)

        tmp_dir = tempfile.gettempdir()
        filename = "target.png"
        ocr_image = os.path.join(tmp_dir, filename)

        ocr_target.save(ocr_image, "PNG")

        # ocr_target.show()

        text_ocr = pytesseract.image_to_string(ocr_target, lang="eng")

        return text_ocr

    def _update_paragraph_markers(self):
        from orcus.util import kivy_paragraphs_bounds_xy

        if self.background is None:
            return

        # Clear the previous markers, if any
        self._clear_marker_rectangles()

        bounds_xy = kivy_paragraphs_bounds_xy(
            self.background.name, self.autodetect_smoothness
        )

        for x1, y1, x2, y2 in bounds_xy:
            marker_rectangle = MarkerRectangle(
                start_point=(x1, y1),
                end_point=(x2, y2),
                initial_color=(0, 1, 0, 1),
                line_width=2,
                fade_duration=0,
                is_shadowed=False,
                is_frozen=True,
            )

            self.add_widget(marker_rectangle)
            self._marker_rectangles.append(marker_rectangle)


class OrcusApp(App):
    use_kivy_settings = False

    def build(self):
        Config.set("kivy", "log_level", "debug")
        self.title = "Orcus"

        self.monitor = None
        self.monitor_unsc = None
        self.fake_desktop = FakeDesktop()

        resource_add_path(os.path.join(os.path.dirname(__file__), "resources"))

        return self.fake_desktop

    def build_config(self, config):
        for section in DEFAULT_CONFIG_SECTIONS:
            config.setdefaults(section["name"], section["options"])

    def on_config_change(self, *args, **kwargs):
        self.config.write()
        self.reload_config()
        self.fake_desktop.reload_config()

    def build_settings(self, settings):
        settings.add_json_panel(
            "Settings", self.config, data=json.dumps(CONFIG_PANEL_SECTIONS)
        )

        settings.size_hint = (0.5, 0.5)
        settings.pos_hint = {"center_x": 0.5, "center_y": 0.5}

    def close_settings(self, settings=None):
        self.reload_config()
        self.fake_desktop.reload_config()

        super(OrcusApp, self).close_settings(settings)

    def get_application_config(self):
        config_file = self._bootstrap_config_file()

        return config_file

    def get_resource(self, filename):
        return resource_find(filename)

    def _bootstrap_config_file(self):
        home_directory = os.path.expanduser("~")
        config_dir = os.path.join(home_directory, ".orcus")

        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

        config_file = os.path.join(config_dir, "orcus.ini")

        return config_file

    def on_start(self):
        self.root_window.title = self.title
        Logger.debug(f"self.root_window: {self.root_window}")
        self.monitor, self.monitor_unsc = find_current_monitor_info()

        self.reload_config()

        self._setup_keyboard()
        self._fullscreen()

        self.fake_desktop.post_init()

    def reload_config(self):
        self._openai_api_key = self.config.get("openai", "openai_api_key")

    def _setup_keyboard(self):
        # Bind the keyboard to the on_key_down function
        self._keyboard = self.root_window.request_keyboard(
            self._keyboard_closed, self.fake_desktop
        )
        self._keyboard.bind(
            on_key_down=self.fake_desktop.on_key_down,
            on_key_up=self.fake_desktop.on_key_up,
        )

    def _keyboard_closed(self):
        # Unbind the keyboard
        self._keyboard.unbind(
            on_key_down=self.fake_desktop.on_key_down,
            on_key_up=self.fake_desktop.on_key_up,
        )
        self._keyboard = None

    def _fullscreen(self):
        if OS == "linux":
            self.root_window.fullscreen = "auto"
        elif OS == "darwin":
            # TODO Full screen custom config for OSX
            pass
        elif OS == "windows":
            pass
        else:
            raise Exception(
                f"OS {OS} not supported - Unable to set window to fullscreen"
            )

        self._position_window()
        self._resize_window()

    def _position_window(self):
        self.root_window.left, self.root_window.top = (
            self.monitor["left"],
            self.monitor["top"],
        )

    def _resize_window(self):
        self.root_window.system_size = (
            self.monitor_unsc["width"],
            self.monitor_unsc["height"],
        )


def main():
    app = OrcusApp()
    app.run()


if __name__ == "__main__":
    main()
