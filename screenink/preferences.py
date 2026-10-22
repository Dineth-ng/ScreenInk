"""Validated preferences stored in the existing per-user QSettings store."""
import re
from pathlib import Path
from datetime import datetime
from PySide6.QtGui import QColor
from .annotations import Tool

DEFAULTS = {
    "startup": False, "minimize_to_tray": True, "notifications": True,
    "theme": "Dark", "pen_color": "#ff0000", "pen_width": 8, "pen_style": "Brush",
    "drawing_tool": "Pen", "darkness": 25, "spotlight_opacity": 65,
    "filename_format": "ScreenInk_%Y-%m-%d_%H%M%S", "diagnostics": False,
}


def validate(values):
    result = dict(DEFAULTS)
    for key, default in DEFAULTS.items():
        value = values.get(key, default)
        if isinstance(default, bool):
            if isinstance(value, str) and value.lower() in ("true", "false"):
                value = value.lower() == "true"
            if not isinstance(value, bool):
                raise ValueError(f"Invalid {key} setting.")
        elif isinstance(default, int):
            value = int(value)
        else:
            value = str(value)
        result[key] = value
    if result['theme'] not in ('Dark', 'Light', 'System'):
        raise ValueError('Choose Dark, Light or System theme.')
    if not QColor(result['pen_color']).isValid():
        raise ValueError('Choose a valid pen color, for example #00ff00.')
    result['pen_color'] = QColor(result['pen_color']).name()
    if result['pen_style'] not in ('Solid','Dashed','Dotted','Marker','Brush','Chalk'):
        raise ValueError('Choose a supported pen style.')
    if result['pen_width'] not in (2,4,6,8,12):
        raise ValueError('Choose a supported pen thickness.')
    if result['drawing_tool'] not in [t.value for t in Tool]:
        raise ValueError('Choose a supported drawing tool.')
    if not 0 <= result['darkness'] <= 90 or not 10 <= result['spotlight_opacity'] <= 90:
        raise ValueError('Opacity is outside its supported range.')
    pattern = result['filename_format']
    if not pattern or len(pattern) > 100 or re.search(r'[<>:"/\\|?*\x00-\x1f]',pattern):
        raise ValueError('Filename format must be a filename, without folders or Windows reserved characters.')
    if re.search(r'%(?![YmdHMSf])', pattern.replace('%%', '')):
        raise ValueError('Filename placeholders: %Y %m %d %H %M %S %f or %%.')
    name = datetime.now().strftime(pattern)
    if name.endswith((' ','.')) or name.split('.')[0].upper() in {'CON','PRN','AUX','NUL', *[f'COM{i}' for i in range(1,10)], *[f'LPT{i}' for i in range(1,10)]}:
        raise ValueError('Choose a filename that Windows permits.')
    return result


def load(store):
    result = dict(DEFAULTS)
    # Recover each damaged preference independently instead of discarding all.
    for key in DEFAULTS:
        try:
            result[key] = validate({**result, key: store.value('preferences/' + key, DEFAULTS[key])})[key]
        except (ValueError, TypeError, OverflowError):
            pass
    return result


def save(store, values):
    from PySide6.QtCore import QSettings
    result = validate(values)
    for key, value in result.items():
        store.setValue('preferences/' + key, value)
    store.sync()
    if store.status() != QSettings.Status.NoError:
        raise OSError('Windows could not save preferences.')
    return result


def screenshot_name(pattern):
    name = datetime.now().strftime(pattern)
    return name if name.lower().endswith('.png') else name + '.png'
