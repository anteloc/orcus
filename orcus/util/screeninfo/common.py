import math
import enum
import typing as T
from dataclasses import dataclass


STANDARD_DPIS = [600, 480, 384, 288, 240, 216, 192, 168, 144, 120, 96]

def calculate_dpi_density(width, height, width_mm, height_mm):
    width_in = width_mm / 25.4
    height_in = height_mm / 25.4
    
    dpi = (width / width_in + height / height_in) / 2.0
    # Round to the nearest standard DPI that is less than or equal to the calculated DPI
    dpi = next(std for std in STANDARD_DPIS if float(std) <= dpi)

    density = dpi / 96.0
    
    return dpi, density


@dataclass
class Monitor:
    """Stores the resolution and position of a monitor."""

    x: int
    y: int
    width: int
    height: int
    dpi: T.Optional[float] = None
    density: T.Optional[float] = None
    width_mm: T.Optional[int] = None
    height_mm: T.Optional[int] = None
    name: T.Optional[str] = None
    is_primary: T.Optional[bool] = None

    def __repr__(self) -> str:
        return (
            f"Monitor("
            f"x={self.x}, y={self.y}, "
            f"width={self.width}, height={self.height}, "
            f"dpi={self.dpi}, density={self.density}, "
            f"width_mm={self.width_mm}, height_mm={self.height_mm}, "
            f"name={self.name!r}, "
            f"is_primary={self.is_primary}"
            f")"
        )


class ScreenInfoError(Exception):
    pass


class Enumerator(enum.Enum):
    Windows = "windows"
    Cygwin = "cygwin"
    Xrandr = "xrandr"
    Xinerama = "xinerama"
    DRM = "drm"
    OSX = "osx"
