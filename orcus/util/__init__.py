from .constants import (
    RECTANGLE_COLOR,
    RECTANGLE_LINE_WIDTH,
    RECTANGLE_FADE_DURATION,
    DEFAULT_CONFIG_SECTIONS,
    CONFIG_PANEL_SECTIONS,
    DUMMY_OPENAPI_API_KEY,
)

from .functions import (
    find_current_monitor_info,
    std_to_kivy_xy,
    kivy_to_std_xy,
    std_to_kivy_rect_xy,
    std_to_kivy_rect_wh,
    kivy_to_std_rect_xy,
    kivy_to_std_rect_wh,
    rect_wh_to_xy,
    rect_xy_to_wh,
    rect_tl_br,
    normalize_rect_xy,
    normalize_rect_wh,
    min_rect_xy_containing,
    min_rect_wh_containing,
)

# from .mixins import HoverSizeMixin

from .screenshot import BackgroundScreenshotHandler

from .ocr import kivy_paragraphs_bounds_xy

# mixins = ("HoverAnimationMixin", "HoverSizeMixin", "HoverSizeHintMixin")
#
# # Required for kivy .kv files to recognize the mixins when creating rules and templates
# for mixin in mixins:
#     Factory.register(mixin, module="componga.util.mixins")
