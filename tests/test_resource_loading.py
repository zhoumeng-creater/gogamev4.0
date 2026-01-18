from pathlib import Path
from typing import Dict, List, Tuple

from ui.help import RulesHelpDialog, TutorialDialog
from ui.problem_library import ProblemLibraryWindow
from utils.content_db import ContentDatabase


def _content_pack_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "content_packs" / "default"


class DummyTranslator:
    def __init__(self, language: str = "zh") -> None:
        self.language = language


class DummyContentDB:
    def __init__(self, resources: List[Dict[str, str]]) -> None:
        self._resources = resources
        self.calls: List[Tuple[str, str]] = []

    def list_resources(self, category: str, language: str) -> List[Dict[str, str]]:
        self.calls.append((category, language))
        return list(self._resources)


def test_content_pack_resources_loaded(tmp_path):
    content_db = ContentDatabase(
        db_path=str(tmp_path / "content.db"),
        pack_dir=_content_pack_dir(),
    )
    try:
        rules = content_db.list_resources("rules_help", "zh")
        assert rules
        assert any("qipai.org.cn" in item.get("url", "") for item in rules)

        tutorials = content_db.list_resources("tutorial", "zh")
        assert tutorials
        assert any("online-go.com" in item.get("url", "") for item in tutorials)

        problems = content_db.list_resources("problem_library", "zh")
        assert problems
        assert any("goproblems.com" in item.get("url", "") for item in problems)
    finally:
        content_db.close()


def test_help_resources_no_fallback():
    dialog = RulesHelpDialog.__new__(RulesHelpDialog)
    dialog.translator = DummyTranslator(language="en")
    dialog.content_db = DummyContentDB([])
    assert dialog._load_resources("rules_help") == []
    assert dialog.content_db.calls == [("rules_help", "en")]

    tutorial = TutorialDialog.__new__(TutorialDialog)
    tutorial.translator = DummyTranslator(language="zh")
    tutorial.content_db = DummyContentDB([])
    assert tutorial._load_resources("tutorial") == []
    assert tutorial.content_db.calls == [("tutorial", "zh")]


def test_problem_resources_no_fallback():
    window = ProblemLibraryWindow.__new__(ProblemLibraryWindow)
    window.translator = DummyTranslator(language="zh")
    window.content_db = DummyContentDB([])
    assert window._load_resources("problem_library") == []
    assert window.content_db.calls == [("problem_library", "zh")]
