from kivy.graphics import Line
from kivy.vector import Vector

from .baseshape import BaseShape
from ..util.functions import rect_xy_contains, rect_tl_br, normalize_rect_xy


class Rectangle(BaseShape):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with self.canvas:
            self.rectangle_line = Line(
                rounded_rectangle=self._compute_rectangle(), width=self.line_width
            )

    def on_touch_move(self, touch):
        super().on_touch_move(touch)

        if touch.button == "left":
            self.rectangle_line.rounded_rectangle = self._compute_rectangle()
            return True
        return False

    def _compute_rectangle(self):
        x0, y0 = self.start_point
        x, y = self.end_point

        width = abs(x - x0)
        height = abs(y - y0)

        left_corner_x = x0 if x0 < x else x
        left_corner_y = y0 if y0 < y else y

        return left_corner_x, left_corner_y, width, height, 10

    def build_shape_preview(self, *args):
        if self.shadow:
            self.shadow.on_pos(*args)

        self.start_point = Vector(*self.parent.pos)
        self.end_point = Vector(*self.parent.pos) + Vector(
            self.parent.width, self.parent.height
        )
        self.rectangle_line.rounded_rectangle = self._compute_rectangle()


class MarkerRectangle(Rectangle):
    def __init__(
        self,
        start_point,
        end_point,
        initial_color,
        line_width,
        fade_duration=5.0,
        pos_offset=(0, 0),
        is_shadowed=False,
        is_frozen=False,
        **kwargs
    ):
        super().__init__(
            start_point,
            initial_color,
            line_width,
            fade_duration=fade_duration,
            pos_offset=pos_offset,
            is_shadowed=is_shadowed,
            is_frozen=is_frozen,
            **kwargs
        )

        self.end_point = end_point

        self.rectangle_line.rounded_rectangle = self._compute_rectangle()

    def contains_point(self, xy):
        # tl, br = rect_tl_br(self.start_point, self.end_point)
        bounds_xy = (*self.start_point, *self.end_point)
        bounds_xy = normalize_rect_xy(bounds_xy, kivy_rect=True)

        return rect_xy_contains(bounds_xy, xy, kivy_rect=True)

    def to_rect_xy(self):
        return *self.start_point, *self.end_point

    def on_touch_up(self, touch):
        pass

    def on_touch_move(self, touch):
        pass

    def on_touch_down(self, touch):
        pass
