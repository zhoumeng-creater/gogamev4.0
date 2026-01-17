from pathlib import Path

from core import Game
from features.replay import ReplayManager
from features.teaching import TeachingSystem
from utils.content_db import ContentDatabase
from utils.user_db import UserDatabase


def _content_pack_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "assets" / "content_packs" / "default"


def _init_teaching_system(tmp_path, monkeypatch):
    content_db = ContentDatabase(db_path=str(tmp_path / "content.db"), pack_dir=_content_pack_dir())
    user_db = UserDatabase(db_path=str(tmp_path / "user.db"))

    def _tmp_puzzle_db_path(self):
        return str(tmp_path / "puzzles.db")

    monkeypatch.setattr(TeachingSystem, "_default_puzzle_db_path", _tmp_puzzle_db_path)
    teaching = TeachingSystem(content_db=content_db, user_db=user_db, user_id="smoke")
    return teaching, content_db, user_db


def test_smoke_lesson_progress_and_puzzle(tmp_path, monkeypatch):
    teaching, content_db, user_db = _init_teaching_system(tmp_path, monkeypatch)
    try:
        lesson = teaching.get_lesson("rules_basic")
        assert lesson is not None
        assert lesson.content
        assert teaching.start_lesson("rules_basic") is True

        for item in lesson.content:
            teaching.complete_lesson_step(lesson.id, item.step)

        completed_lessons = user_db.list_completed_lessons("smoke")
        assert "rules_basic" in completed_lessons
        summary = user_db.get_user_summary("smoke")
        assert summary["total_score"] >= 100

        puzzle = teaching.get_puzzle("capture_basic_1")
        assert puzzle is not None
        correct = puzzle.solution[0]
        wrong = next(iter(puzzle.wrong_moves.keys()), None)
        if wrong is None or wrong == correct:
            wrong = (0, 0)
            if wrong == correct:
                wrong = (1, 1)

        success, _ = teaching.check_puzzle_solution(puzzle.id, wrong[0], wrong[1])
        assert success is False
        success, _ = teaching.check_puzzle_solution(puzzle.id, correct[0], correct[1])
        assert success is True

        assert puzzle.id in user_db.list_completed_puzzles("smoke")
        cursor = user_db.connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM puzzle_attempts WHERE user_id = ? AND puzzle_id = ?",
            ("smoke", puzzle.id),
        )
        assert cursor.fetchone()[0] >= 2
    finally:
        content_db.close()
        user_db.close()


def test_smoke_replay_comment_roundtrip(tmp_path):
    user_db = UserDatabase(db_path=str(tmp_path / "user.db"))
    try:
        game = Game(board_size=9)
        game.make_move(2, 2)
        replay = ReplayManager(game=game, user_db=user_db)
        replay.next_move()

        comment_text = "smoke comment"
        replay.add_comment(comment_text, author="smoke", evaluation="good")

        replay_reload = ReplayManager(
            game=game,
            user_db=user_db,
            session_id=replay.session_id,
        )
        node = replay_reload.move_tree.root.children[0]
        assert any(c.text == comment_text and c.author == "smoke" for c in node.comments)
        assert any(c.move_evaluation == "good" for c in node.comments)
    finally:
        user_db.close()
