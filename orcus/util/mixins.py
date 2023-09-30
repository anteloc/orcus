from kivy.app import App
from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty


class HoverAnimationMixin(EventDispatcher):
    init_prop_value = ObjectProperty(None)
    final_prop_value = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(HoverAnimationMixin, self).__init__(*args, **kwargs)

        self._hover = False
        self._anim = None
        self._prev_size = None
        self._prev_pos = None
        self._app = App.get_running_app()
        self._app.root_window.bind(mouse_pos=self.on_mouse_pos)

    def __del__(self):
        try:
            self._app.root_window.unbind(mouse_pos=self.on_mouse_pos)
        except:
            pass

    def on_mouse_pos(self, _, pos):
        if self.collide_point(*pos):
            self.on_hover()
        else:
            self.on_unhover()

    def on_hover(self):
        if not self._hover:
            self._start_anim(self.final_prop_value)
            self._hover = True

    def on_unhover(self):
        if self._hover:
            self._start_anim(self.init_prop_value)
            self._hover = False

    def _start_anim(self, new_prop_value):
        if self._anim:
            self._anim.cancel(self)

        self._anim = self._build_anim(new_prop_value)
        self._anim.start(self)

    def _build_anim(self, new_prop_value):
        pass


class HoverSizeMixin(HoverAnimationMixin):
    hover_min_size = ObjectProperty(None)
    hover_max_size = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(HoverSizeMixin, self).__init__(*args, **kwargs)

        self.bind(
            hover_min_size=self.setter("init_prop_value"),
            hover_max_size=self.setter("final_prop_value"),
        )

    def _build_anim(self, new_prop_value):
        return Animation(size=new_prop_value, duration=0.2)


# XXX This mixin is not used yet due to problems with positioning the widget
class HoverSizeHintMixin(HoverAnimationMixin):
    hover_min_sizeh = ObjectProperty(None)
    hover_max_sizeh = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(HoverSizeHintMixin, self).__init__(*args, **kwargs)

        self.bind(
            hover_min_sizeh=self.setter("init_prop_value"),
            hover_max_sizeh=self.setter("final_prop_value"),
        )

    def _build_anim(self, new_prop_value):
        return Animation(size_hint=new_prop_value, duration=0.2)
