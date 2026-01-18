import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union


def _resource_path(relative_path: str) -> Path:
    try:
        base = Path(sys._MEIPASS)
    except Exception:
        base = Path(__file__).resolve().parents[1]
    return base / relative_path


def _user_config_dir() -> Path:
    return Path.home() / ".go_master"


def _read_mapping(path: Path) -> Dict[str, Union[str, List[str]]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): v for k, v in data.items()}


def load_hotkeys() -> Dict[str, Union[str, List[str]]]:
    mapping: Dict[str, Union[str, List[str]]] = {}
    default_path = _resource_path("assets/config/hotkeys.json")
    mapping.update(_read_mapping(default_path))

    user_path = _user_config_dir() / "hotkeys.json"
    mapping.update(_read_mapping(user_path))
    return mapping


def _normalize_hotkey_values(value: Union[str, List[str], None]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v]
    return [str(value)] if value else []


_MODIFIER_ALIASES = {
    "ctrl": "Control",
    "control": "Control",
    "alt": "Alt",
    "option": "Alt",
    "shift": "Shift",
    "cmd": "Command",
    "command": "Command",
    "meta": "Command",
}

_KEY_ALIASES = {
    "comma": "comma",
    ",": "comma",
    "period": "period",
    ".": "period",
    "plus": "plus",
    "+": "plus",
    "minus": "minus",
    "-": "minus",
    "space": "space",
    "spacebar": "space",
    "enter": "Return",
    "return": "Return",
    "esc": "Escape",
    "escape": "Escape",
    "tab": "Tab",
    "backspace": "BackSpace",
    "delete": "Delete",
    "del": "Delete",
}

_SPECIAL_KEYS = {
    "space",
    "Return",
    "Escape",
    "Tab",
    "BackSpace",
    "Delete",
}


def hotkey_to_tk_sequences(value: Union[str, List[str], None]) -> List[str]:
    sequences: List[str] = []
    for item in _normalize_hotkey_values(value):
        item = item.strip()
        if not item:
            continue
        if item.startswith("<") and item.endswith(">"):
            sequences.append(item)
            continue
        tokens = [t.strip() for t in item.split("+") if t.strip()]
        modifiers: List[str] = []
        key = None
        for token in tokens:
            lower = token.lower()
            if lower in _MODIFIER_ALIASES:
                modifiers.append(_MODIFIER_ALIASES[lower])
            else:
                key = token
        if not key:
            continue
        key_lower = key.lower()
        if key_lower in _KEY_ALIASES:
            key_name = _KEY_ALIASES[key_lower]
        elif key_lower.startswith("f") and key_lower[1:].isdigit():
            key_name = key.upper()
        elif len(key) == 1:
            key_name = key.lower()
        else:
            key_name = key
        if modifiers:
            sequences.append(f"<{'-'.join(modifiers + [key_name])}>")
        else:
            if len(key_name) == 1:
                sequences.append(key_name)
            else:
                sequences.append(f"<{key_name}>")
    return sequences


def hotkey_to_display(value: Union[str, List[str], None]) -> str:
    values = _normalize_hotkey_values(value)
    if not values:
        return ""
    item = values[0].strip()
    if not item:
        return ""
    if item.startswith("<") and item.endswith(">"):
        tokens = [t for t in item[1:-1].split("-") if t]
        if not tokens:
            return ""
        modifiers = []
        key = tokens[-1]
        for token in tokens[:-1]:
            lower = token.lower()
            if lower == "control":
                modifiers.append("Ctrl")
            elif lower == "alt":
                modifiers.append("Alt")
            elif lower == "shift":
                modifiers.append("Shift")
            elif lower == "command":
                modifiers.append("Cmd")
            else:
                modifiers.append(token)
        if key == "space":
            key_display = "Space"
        elif key == "Return":
            key_display = "Enter"
        elif key == "BackSpace":
            key_display = "Backspace"
        else:
            key_display = key.upper() if len(key) == 1 else key
        return "+".join(modifiers + [key_display]) if modifiers else key_display

    tokens = [t.strip() for t in item.split("+") if t.strip()]
    if not tokens:
        return ""
    display = []
    for token in tokens:
        lower = token.lower()
        if lower in ("ctrl", "control"):
            display.append("Ctrl")
        elif lower in ("alt", "option"):
            display.append("Alt")
        elif lower == "shift":
            display.append("Shift")
        elif lower in ("cmd", "command", "meta"):
            display.append("Cmd")
        elif lower == "space":
            display.append("Space")
        elif lower in ("enter", "return"):
            display.append("Enter")
        else:
            display.append(token.upper() if len(token) == 1 else token)
    return "+".join(display)
