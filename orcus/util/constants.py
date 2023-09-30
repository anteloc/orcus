SCREEN_TITLE = "orcus"

RECTANGLE_LINE_WIDTH = 2
RECTANGLE_COLOR = "ff0000"
RECTANGLE_FADE_DURATION = 0.5

DUMMY_OPENAPI_API_KEY = "<your OPENAI_API_KEY>"
DEFAULT_CONFIG_SECTIONS = [
    {
        "name": "rectangle.attributes",
        "options": {
            "rectangle_line_width": RECTANGLE_LINE_WIDTH,
            "rectangle_color": RECTANGLE_COLOR,
            "rectangle_fade_duration": RECTANGLE_FADE_DURATION,
        },
    },
    {
        "name": "keyboard.shortcuts",
        "options": {
            "auto_manual_mode": "a",
            "increase_auto_tolerance": "+",
            "decrease_auto_tolerance": "-",
            "update_background": "u",
            "show_settings": "s",
            "show_help": "h",
            "exit": "escape",
        },
    },
    {
        "name": "keyboard.shortcuts.help",
        "options": {
            "auto_manual_mode": "Switch between auto and manual mode",
            "increase_auto_tolerance": "[Auto] Paragraph detection tolerance increase",
            "decrease_auto_tolerance": "[Auto] Paragraph detection tolerance decrease",
            "update_background": "Refresh desktop image",
            "show_settings": "Edit Settings",
            "show_help": "Show Help",
            "exit": "Exit Orcus",
        },
    },
    {
        "name": "openai",
        "options": {
            "openai_api_key": DUMMY_OPENAPI_API_KEY,
        },
    },
]

CONFIG_PANEL_SECTIONS = [
    {"type": "title", "title": "Selection Rectangle Options"},
    {
        "type": "numeric",
        "title": "Rectangle Fade Duration",
        "desc": "Time interval until selection rectangle fades away",
        "section": "rectangle.attributes",
        "key": "rectangle_fade_duration",
    },
    {
        "type": "numeric",
        "title": "Rectangle Line Width",
        "desc": "Rectangle line thickness",
        "section": "rectangle.attributes",
        "key": "rectangle_line_width",
    },
    {
        "type": "color",
        "title": "Rectangle Color",
        "desc": "Rectangle line color",
        "section": "rectangle.attributes",
        "key": "rectangle_color",
    },
    {"type": "title", "title": "OpenAI & ChatGPT Options"},
    {
        "type": "string",
        "title": "OpenAI API Key",
        "desc": "API key required for OpenAI API calls",
        "section": "openai",
        "key": "openai_api_key",
    }
]

