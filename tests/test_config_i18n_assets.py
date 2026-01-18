import ast
import json
from pathlib import Path

from ui.themes import ThemeManager
from utils.config import ConfigManager
from utils.hotkeys import hotkey_to_display, hotkey_to_tk_sequences, load_hotkeys
from utils.sound import SoundManager
from utils.translator import Translator


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _collect_translation_keys(root: Path) -> set[str]:
    keys: set[str] = set()

    def add_key(value):
        if isinstance(value, str):
            keys.add(value)

    class KeyVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                base = node.func.value
                if isinstance(base, ast.Name) and base.id == "translator":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        add_key(node.args[0].value)
                elif isinstance(base, ast.Attribute) and base.attr == "translator":
                    if node.args and isinstance(node.args[0], ast.Constant):
                        add_key(node.args[0].value)
                elif isinstance(base, ast.Call):
                    if isinstance(base.func, ast.Name) and base.func.id in {
                        "get_translator",
                        "Translator",
                    }:
                        if node.args and isinstance(node.args[0], ast.Constant):
                            add_key(node.args[0].value)
            if isinstance(node.func, ast.Name) and node.func.id in {"t", "_t"}:
                if node.args and isinstance(node.args[0], ast.Constant):
                    add_key(node.args[0].value)
            self.generic_visit(node)

    for path in root.rglob("*.py"):
        if any(part in {".git", ".venv", "site-packages"} for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        KeyVisitor().visit(tree)

    return keys


def test_translator_loads_assets():
    translations_dir = _repo_root() / "assets" / "translations"
    translator = Translator(language="zh", translations_dir=str(translations_dir))
    assert translator.get("app_name") == "围棋大师"
    assert translator.get("language_name_en") != "language_name_en"
    assert {"zh", "en", "ja"}.issubset(set(translator.get_available_languages()))


def test_hotkeys_mapping_and_sequences():
    mapping = load_hotkeys()
    assert mapping.get("new_game") == "Ctrl+N"
    assert mapping.get("pause") == "Space"

    assert hotkey_to_tk_sequences("Ctrl+N") == ["<Control-n>"]
    assert hotkey_to_tk_sequences("F11") == ["<F11>"]
    assert hotkey_to_tk_sequences("Space") == ["<space>"]
    assert hotkey_to_tk_sequences("Ctrl+Plus") == ["<Control-plus>"]
    assert hotkey_to_display("Ctrl+N") == "Ctrl+N"


def test_default_config_from_assets(tmp_path):
    config_path = tmp_path / "config.json"
    manager = ConfigManager(config_file=str(config_path))
    assert manager.config.display.theme == "wood"
    assert manager.config.rules.default_rules == "chinese"
    assert manager.config.rules.default_board_size == 19


def test_themes_loaded_from_assets():
    manager = ThemeManager()
    assert "wood" in manager.themes
    theme = manager.get_theme("wood")
    assert theme is not None
    assert theme.board_background == "#F4D0A4"


def test_sound_mapping_from_config(monkeypatch):
    monkeypatch.setattr(SoundManager, "_init_audio_system", lambda self: False)
    monkeypatch.setattr(SoundManager, "_start_playing_thread", lambda self: None)
    manager = SoundManager(config_manager=None)
    try:
        assert manager.sound_files.get("place_stone") == "place_stone.wav"
        assert "time_warning" in manager.sound_files
    finally:
        manager.cleanup()


def test_translation_keys_covered_by_assets():
    repo_root = _repo_root()
    keys = _collect_translation_keys(repo_root)
    translations_dir = repo_root / "assets" / "translations"

    for lang in ("zh", "en", "ja"):
        data = json.loads((translations_dir / f"{lang}.json").read_text(encoding="utf-8"))
        missing = sorted(k for k in keys if k not in data)
        assert not missing, f"Missing {lang} keys: {missing}"
