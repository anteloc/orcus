import typing as T

from orcus.util.screeninfo.common import Monitor


# https://developer.apple.com/documentation/appkit/nsscreen/1388371-main
# first entry in array is always the primary screen
def check_primary(screens: T.Any, screen: T.Any) -> bool:
    return screen == screens[0]


def enumerate_monitors() -> T.Iterable[Monitor]:
    from kivy.logger import Logger
    Logger.debug(f"osx enumerate_monitors()")

    from AppKit import NSScreen, NSDeviceResolution

    screens = NSScreen.screens()

    for screen in screens:
        f = screen.frame
        if callable(f):
            f = f()

         # TODO NOT tested on MacOS or any Apple device
        description = screen.deviceDescription()
        # Resolution in dpi's
        # XXX Should they always be the same in desktop environments?
        rx, _ry = description[NSDeviceResolution].sizeValue()

        dpi = rx
        density = dpi / 96.0

        yield Monitor(
            x=int(f.origin.x),
            y=int(f.origin.y),
            width=int(f.size.width),
            height=int(f.size.height),
            dpi=dpi,
            density=density,
            is_primary=check_primary(screens, screen),
        )
