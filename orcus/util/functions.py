import mouse
from kivy.logger import Logger
from kivy.metrics import Metrics

# from .constants import SHAPE_TYPES, SHAPE_TYPES_LOWER, SHAPE_TYPES_UPPER
from .screeninfo import get_monitors


# XXX This is a hack to ensure that the metrics are set for the monitors, just in
#   case componga's screeninfo doesn't report the correct values
def _ensure_metrics(monitors):
    for monitor in monitors:
        if monitor.dpi is None or monitor.density is None:
            Logger.warn(
                f"No metrics detected by componga's screeninfo, using kivy's metrics: dpi: {Metrics.dpi}, density: {Metrics.density}"
            )
            monitor.dpi = Metrics.dpi
            monitor.density = Metrics.density


def find_current_monitor_info():
    monitors = get_monitors()
    _ensure_metrics(monitors)

    Logger.debug(f"monitors screeninfo: {monitors}")

    mouse_x, mouse_y = mouse.get_position()
    Logger.debug(f"mouse at {mouse_x}, {mouse_y}")

    current_monitor = None

    for mon in monitors:
        scr_x0 = mon.x
        scr_x1 = mon.x + mon.width
        scr_y0 = mon.y
        scr_y1 = mon.y + mon.height

        if (
            mouse_x >= scr_x0
            and mouse_x <= scr_x1
            and mouse_y >= scr_y0
            and mouse_y <= scr_y1
        ):
            current_monitor = mon

        if current_monitor is not None:
            density = current_monitor.density
            mss_monitor = {
                "left": current_monitor.x,
                "top": current_monitor.y,
                "width": current_monitor.width,
                "height": current_monitor.height,
            }
            mss_monitor_unsc = {
                key: int(val / density) for key, val in mss_monitor.items()
            }

            return mss_monitor, mss_monitor_unsc

    return None, None


def _delta_y_coords(xy, delta_y0s):
    x, y = xy
    return x, delta_y0s - y


def rect_xy_to_wh(rect_xy):
    x1, y1, x2, y2 = rect_xy
    w = abs(x2 - x1)
    h = abs(y2 - y1)
    return x1, y1, w, h


def rect_wh_to_xy(rect_wh, kivy_rect=False):
    x1, y1, w, h = rect_wh
    x2 = x1 + w
    y2 = y1 + h if not kivy_rect else y1 - h
    return x1, y1, x2, y2


def rect_xy_contains(rect_xy, xy, kivy_rect=False):
    rect_xy = normalize_rect_xy(rect_xy, kivy_rect)
    x1, y1, x2, y2 = rect_xy
    x, y = xy

    x_contained = x1 <= x <= x2
    y_contained = (y1 <= y <= y2) if not kivy_rect else (y2 <= y <= y1)

    return x_contained and y_contained


def rect_wh_contains(rect_wh, xy, kivy_rect=False):
    rect_xy = rect_wh_to_xy(rect_wh, kivy_rect)

    return rect_xy_contains(rect_xy, xy, kivy_rect)


def min_rect_xy_containing(rects_xy, xy, kivy_rect=False):
    Logger.debug(
        f"min_rect_xy_containing rects_xy: {rects_xy}, xy: {xy}, kivy_rect: {kivy_rect}"
    )

    containers = [
        rect_xy_to_wh(rect_xy)
        for rect_xy in rects_xy
        if rect_xy_contains(rect_xy, xy, kivy_rect)
    ]

    Logger.debug(f"min_rect_xy_containing containers: {containers}")

    if not containers:
        return None

    min_rect = min(containers, key=lambda r_wh: r_wh[2] * r_wh[3])

    return rect_wh_to_xy(min_rect, kivy_rect)


def min_rect_wh_containing(rects_wh, xy, kivy_rect=False):
    rects_xy = [rect_wh_to_xy(rect_wh, kivy_rect) for rect_wh in rects_wh]
    return min_rect_xy_containing(rects_xy, xy, kivy_rect)


def std_to_kivy_xy(std_xy, delta_y0s):
    return _delta_y_coords(std_xy, delta_y0s)


def kivy_to_std_xy(kivy_xy, delta_y0s):
    return _delta_y_coords(kivy_xy, delta_y0s)


def std_to_kivy_rect_xy(std_rect_xy, delta_y0s):
    std_x1, std_y1, std_x2, std_y2 = std_rect_xy

    kivy_x1, kivy_y1 = std_to_kivy_xy((std_x1, std_y1), delta_y0s)
    kivy_x2, kivy_y2 = std_to_kivy_xy((std_x2, std_y2), delta_y0s)

    return kivy_x1, kivy_y1, kivy_x2, kivy_y2


def std_to_kivy_rect_wh(std_rect_wh, delta_y0s):
    std_rect_xy = rect_wh_to_xy(std_rect_wh, kivy_rect=False)

    kivy_rect_xy = std_to_kivy_rect_xy(std_rect_xy, delta_y0s)

    return rect_xy_to_wh(kivy_rect_xy)


def kivy_to_std_rect_xy(kivy_rect_xy, delta_y0s):
    kivy_x1, kivy_y1, kivy_x2, kivy_y2 = kivy_rect_xy

    std_x1, std_y1 = kivy_to_std_xy((kivy_x1, kivy_y1), delta_y0s)
    std_x2, std_y2 = kivy_to_std_xy((kivy_x2, kivy_y2), delta_y0s)

    return std_x1, std_y1, std_x2, std_y2


def kivy_to_std_rect_wh(kivy_rect_wh, delta_y0s):
    kivy_rect_xy = rect_wh_to_xy(kivy_rect_wh, kivy_rect=True)

    std_rect_xy = kivy_to_std_rect_xy(kivy_rect_xy, delta_y0s)

    return rect_xy_to_wh(std_rect_xy)


def rect_tl_br(xy1, xy2, kivy_rect=False):
    x1, y1 = xy1
    x2, y2 = xy2

    tl = [min(x1, x2), min(y1, y2)] if not kivy_rect else [min(x1, x2), max(y1, y2)]
    br = [max(x1, x2), max(y1, y2)] if not kivy_rect else [max(x1, x2), min(y1, y2)]

    return tl, br


def normalize_rect_xy(rect_xy, kivy_rect=False):
    x1, y1, x2, y2 = rect_xy
    tl, br = rect_tl_br((x1, y1), (x2, y2), kivy_rect)

    return *tl, *br


def normalize_rect_wh(rect_wh, kivy_rect=False):
    rect_xy = rect_wh_to_xy(rect_wh, kivy_rect)
    rect_xy = normalize_rect_xy(rect_xy, kivy_rect)

    return rect_xy_to_wh(rect_xy)
