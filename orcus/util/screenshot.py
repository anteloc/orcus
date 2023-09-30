import os
import platform
import tempfile
import time
import mss
import mss.tools
from kivy.logger import Logger
from kivy.clock import Clock
from .functions import find_current_monitor_info

OS = platform.system().lower()


class BackgroundScreenshot(object):
    def __init__(self):
        ts = time.time() * 1000
        tmp_dir = tempfile.gettempdir()
        filename = f"desktop-background-{ts}.png"
        self.name = os.path.join(tmp_dir, filename)
        Logger.debug(f"image tmp file: {self.name}")

    def close(self):
        if os.path.exists(self.name):
            os.remove(self.name)


class _BackgroundScreenshotHandlerTrait(object):
    def take_screenshot(self, mon, target, win):
        self._hide_window(win)
        bg = self._capture_background(mon)
        self._show_window(win)

        target.background = bg

    def _capture_background(self, mon, attempts=0):
        Logger.debug(f"taking screenshot for mon: {mon}")

        if attempts > 3:
            return None

        tmp_file = BackgroundScreenshot()

        with mss.mss() as sct:
            monitors = sct.monitors
            mon_number = monitors.index(mon) if mon in monitors else None
            # Maybe the previous monitor was disconnected
            if mon_number is None:
                new_mon, _ = find_current_monitor_info()
                attempts += 1
                return self._capture_background(new_mon, attempts)

            sct_img = sct.grab(mon)
            mss.tools.to_png(sct_img.rgb, sct_img.size, level=1, output=tmp_file.name)

        return tmp_file


class _OSXBackgroundScreenshotHandler(_BackgroundScreenshotHandlerTrait):
    def _hide_window(self, win):
        # TODO NOT tested on OSX
        win.hide()

        Clock.usleep(200000)

    def _show_window(self, win):
        win.show()


class _WindowsBackgroundScreenshotHandler(_BackgroundScreenshotHandlerTrait):
    _prev_style = None

    def _hide_window(self, win):
        # Widows only, to improve performance and avoid issues with native windows
        import win32gui
        import win32con

        handle = win32gui.FindWindow(None, win.title)
        Logger.debug(f"[{self.__class__}] _hide_window handle: {handle}")

        win32gui.ShowWindow(handle, win32con.SW_HIDE)

        Clock.usleep(300000)

    def _show_window(self, win):
        import win32gui
        import win32con

        handle = win32gui.FindWindow(None, win.title)
        Logger.debug(f"[{self.__class__}] _show_window handle: {handle}")

        win32gui.ShowWindow(handle, win32con.SW_SHOW)


class _LinuxBackgroundScreenshotHandler(_BackgroundScreenshotHandlerTrait):
    def _hide_window(self, win):
        # For Linux, given that there are multiple desktop managers,
        # handling the window in a native way would be too complex
        win.hide()

        Clock.usleep(200000)

    def _show_window(self, win):
        win.show()


class BackgroundScreenshotHandler(object):
    def __init__(self, target):
        from kivy.app import App

        self._target = target
        self._app = App.get_running_app()
        self._mon = self._app.monitor
        self._delegate = None

    def _create_delegate(self):
        if OS == "darwin":
            self._delegate = _OSXBackgroundScreenshotHandler()
        elif OS == "linux":
            self._delegate = _LinuxBackgroundScreenshotHandler()
        elif OS == "windows":
            self._delegate = _WindowsBackgroundScreenshotHandler()
        else:
            raise Exception(f"OS {OS} not supported")

    def take_screenshot(self):
        # Importing the window here to avoid initializing the window
        # before the app is ready
        try:
            if self._delegate is None:
                self._create_delegate()

            self._delegate.take_screenshot(
                self._mon, self._target, self._app.root_window
            )
        except Exception as e:
            Logger.exception(f"Error taking screenshot: {e}")
            raise e
