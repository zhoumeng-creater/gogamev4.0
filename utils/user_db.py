import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _default_user_data_dir() -> Path:
    return Path.home() / ".go_master"


def _ensure_dir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


class UserDatabase:
    """User data database for progress, attempts, stats, and replay comments."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path) if db_path else str(_default_user_data_dir() / "user.db")
        _ensure_dir(Path(self.db_path).parent)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._init_database()

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass

    def _init_database(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_summary (
                user_id TEXT PRIMARY KEY,
                total_score INTEGER DEFAULT 0,
                current_lesson TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lesson_progress (
                user_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                step_completed INTEGER NOT NULL,
                completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, lesson_id, step_completed)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lesson_completion (
                user_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, lesson_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS puzzle_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                puzzle_id TEXT NOT NULL,
                attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success INTEGER,
                time_spent INTEGER,
                hints_used INTEGER DEFAULT 0
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS puzzle_completion (
                user_id TEXT NOT NULL,
                puzzle_id TEXT NOT NULL,
                completion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, puzzle_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS game_stats (
                game_id TEXT PRIMARY KEY,
                date TEXT,
                duration INTEGER,
                board_size INTEGER,
                player_black TEXT,
                player_white TEXT,
                black_rating INTEGER,
                white_rating INTEGER,
                result TEXT,
                move_count INTEGER,
                resignation INTEGER,
                timeout INTEGER,
                captures_black INTEGER,
                captures_white INTEGER,
                territory_black INTEGER,
                territory_white INTEGER,
                time_black REAL,
                time_white REAL,
                longest_think_black REAL,
                longest_think_white REAL,
                opening_pattern TEXT,
                joseki_used TEXT,
                ko_fights INTEGER,
                passes INTEGER,
                mistakes INTEGER,
                brilliant_moves INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS player_stats (
                player_name TEXT PRIMARY KEY,
                total_games INTEGER,
                wins INTEGER,
                losses INTEGER,
                draws INTEGER,
                games_as_black INTEGER,
                wins_as_black INTEGER,
                games_as_white INTEGER,
                wins_as_white INTEGER,
                total_time_played INTEGER,
                average_move_time REAL,
                fastest_game INTEGER,
                longest_game INTEGER,
                rating INTEGER,
                highest_rating INTEGER,
                lowest_rating INTEGER,
                rating_history TEXT,
                achievements TEXT,
                winning_streak INTEGER,
                longest_winning_streak INTEGER,
                losing_streak INTEGER,
                opponents TEXT,
                favorite_openings TEXT,
                total_moves INTEGER,
                total_captures INTEGER,
                resignation_wins INTEGER,
                resignation_losses INTEGER,
                timeout_wins INTEGER,
                timeout_losses INTEGER
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS global_stats (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                total_games INTEGER,
                total_time INTEGER,
                most_popular_board INTEGER,
                most_popular_rules TEXT,
                daily_games TEXT,
                hourly_distribution TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS replay_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                node_path TEXT,
                move_number INTEGER,
                text TEXT,
                author TEXT,
                evaluation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()

    def _json_dumps(self, value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return "[]"

    def _json_loads(self, value: Optional[str], fallback: Any) -> Any:
        if not value:
            return fallback
        try:
            return json.loads(value)
        except Exception:
            return fallback

    def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT total_score, current_lesson FROM user_summary WHERE user_id = ?",
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return {"total_score": 0, "current_lesson": None}
        return {
            "total_score": int(row[0] or 0),
            "current_lesson": row[1],
        }

    def set_user_summary(self, user_id: str, total_score: int, current_lesson: Optional[str]) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_summary (user_id, total_score, current_lesson, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, int(total_score or 0), current_lesson),
        )
        self.connection.commit()

    def record_lesson_step(
        self,
        user_id: str,
        lesson_id: str,
        step: int,
        score: int = 0,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO lesson_progress
            (user_id, lesson_id, step_completed, completion_date, score)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            """,
            (user_id, lesson_id, int(step), int(score or 0)),
        )
        self.connection.commit()

    def list_lesson_steps(self, user_id: str, lesson_id: str) -> List[int]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT step_completed
            FROM lesson_progress
            WHERE user_id = ? AND lesson_id = ?
            ORDER BY step_completed
            """,
            (user_id, lesson_id),
        )
        return [int(row[0]) for row in cursor.fetchall()]

    def record_lesson_completed(self, user_id: str, lesson_id: str, score: int = 0) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO lesson_completion
            (user_id, lesson_id, completion_date, score)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            """,
            (user_id, lesson_id, int(score or 0)),
        )
        self.connection.commit()

    def list_completed_lessons(self, user_id: str) -> List[str]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT lesson_id FROM lesson_completion WHERE user_id = ? ORDER BY completion_date",
            (user_id,),
        )
        return [str(row[0]) for row in cursor.fetchall()]

    def record_puzzle_attempt(
        self,
        user_id: str,
        puzzle_id: str,
        success: bool,
        time_spent: int = 0,
        hints_used: int = 0,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO puzzle_attempts
            (user_id, puzzle_id, attempt_date, success, time_spent, hints_used)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
            """,
            (user_id, puzzle_id, 1 if success else 0, int(time_spent or 0), int(hints_used or 0)),
        )
        self.connection.commit()

    def mark_puzzle_completed(self, user_id: str, puzzle_id: str) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO puzzle_completion
            (user_id, puzzle_id, completion_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (user_id, puzzle_id),
        )
        self.connection.commit()

    def list_completed_puzzles(self, user_id: str) -> List[str]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT puzzle_id FROM puzzle_completion WHERE user_id = ? ORDER BY completion_date",
            (user_id,),
        )
        return [str(row[0]) for row in cursor.fetchall()]

    def has_statistics(self) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM game_stats")
        row = cursor.fetchone()
        if row and int(row[0]) > 0:
            return True
        cursor.execute("SELECT COUNT(*) FROM player_stats")
        row = cursor.fetchone()
        return bool(row and int(row[0]) > 0)

    def upsert_game_stats(self, game_stats: Dict[str, Any]) -> None:
        if not game_stats:
            return
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO game_stats (
                game_id, date, duration, board_size, player_black, player_white,
                black_rating, white_rating, result, move_count, resignation, timeout,
                captures_black, captures_white, territory_black, territory_white,
                time_black, time_white, longest_think_black, longest_think_white,
                opening_pattern, joseki_used, ko_fights, passes, mistakes, brilliant_moves
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(game_stats.get("game_id") or ""),
                str(game_stats.get("date") or ""),
                int(game_stats.get("duration") or 0),
                int(game_stats.get("board_size") or 0),
                str(game_stats.get("player_black") or ""),
                str(game_stats.get("player_white") or ""),
                game_stats.get("black_rating"),
                game_stats.get("white_rating"),
                str(game_stats.get("result") or ""),
                int(game_stats.get("move_count") or 0),
                1 if game_stats.get("resignation") else 0,
                1 if game_stats.get("timeout") else 0,
                int(game_stats.get("captures_black") or 0),
                int(game_stats.get("captures_white") or 0),
                int(game_stats.get("territory_black") or 0),
                int(game_stats.get("territory_white") or 0),
                float(game_stats.get("time_black") or 0.0),
                float(game_stats.get("time_white") or 0.0),
                float(game_stats.get("longest_think_black") or 0.0),
                float(game_stats.get("longest_think_white") or 0.0),
                str(game_stats.get("opening_pattern") or ""),
                self._json_dumps(game_stats.get("joseki_used") or []),
                int(game_stats.get("ko_fights") or 0),
                int(game_stats.get("passes") or 0),
                int(game_stats.get("mistakes") or 0),
                int(game_stats.get("brilliant_moves") or 0),
            ),
        )
        self.connection.commit()

    def list_game_stats(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        sql = "SELECT * FROM game_stats ORDER BY created_at"
        params: Tuple[Any, ...] = ()
        if limit:
            sql += " LIMIT ?"
            params = (int(limit),)
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            entry = dict(row)
            entry["resignation"] = bool(entry.get("resignation"))
            entry["timeout"] = bool(entry.get("timeout"))
            entry["joseki_used"] = self._json_loads(entry.get("joseki_used"), [])
            results.append(entry)
        return results

    def upsert_player_stats(self, player_name: str, player_stats: Dict[str, Any]) -> None:
        if not player_name:
            return
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO player_stats (
                player_name, total_games, wins, losses, draws, games_as_black, wins_as_black,
                games_as_white, wins_as_white, total_time_played, average_move_time, fastest_game,
                longest_game, rating, highest_rating, lowest_rating, rating_history, achievements,
                winning_streak, longest_winning_streak, losing_streak, opponents, favorite_openings,
                total_moves, total_captures, resignation_wins, resignation_losses, timeout_wins,
                timeout_losses
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                player_name,
                int(player_stats.get("total_games") or 0),
                int(player_stats.get("wins") or 0),
                int(player_stats.get("losses") or 0),
                int(player_stats.get("draws") or 0),
                int(player_stats.get("games_as_black") or 0),
                int(player_stats.get("wins_as_black") or 0),
                int(player_stats.get("games_as_white") or 0),
                int(player_stats.get("wins_as_white") or 0),
                int(player_stats.get("total_time_played") or 0),
                float(player_stats.get("average_move_time") or 0.0),
                player_stats.get("fastest_game"),
                player_stats.get("longest_game"),
                int(player_stats.get("rating") or 0),
                int(player_stats.get("highest_rating") or 0),
                int(player_stats.get("lowest_rating") or 0),
                self._json_dumps(player_stats.get("rating_history") or []),
                self._json_dumps(player_stats.get("achievements") or []),
                int(player_stats.get("winning_streak") or 0),
                int(player_stats.get("longest_winning_streak") or 0),
                int(player_stats.get("losing_streak") or 0),
                self._json_dumps(player_stats.get("opponents") or {}),
                self._json_dumps(player_stats.get("favorite_openings") or {}),
                int(player_stats.get("total_moves") or 0),
                int(player_stats.get("total_captures") or 0),
                int(player_stats.get("resignation_wins") or 0),
                int(player_stats.get("resignation_losses") or 0),
                int(player_stats.get("timeout_wins") or 0),
                int(player_stats.get("timeout_losses") or 0),
            ),
        )
        self.connection.commit()

    def list_player_stats(self) -> Dict[str, Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM player_stats")
        rows = cursor.fetchall()
        results: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            entry = dict(row)
            name = str(entry.get("player_name"))
            entry["rating_history"] = self._json_loads(entry.get("rating_history"), [])
            entry["achievements"] = self._json_loads(entry.get("achievements"), [])
            entry["opponents"] = self._json_loads(entry.get("opponents"), {})
            entry["favorite_openings"] = self._json_loads(entry.get("favorite_openings"), {})
            results[name] = entry
        return results

    def get_global_stats(self) -> Optional[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM global_stats WHERE id = 1")
        row = cursor.fetchone()
        if not row:
            return None
        entry = dict(row)
        entry["daily_games"] = self._json_loads(entry.get("daily_games"), {})
        entry["hourly_distribution"] = self._json_loads(entry.get("hourly_distribution"), {})
        return entry

    def upsert_global_stats(self, global_stats: Dict[str, Any]) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO global_stats
            (id, total_games, total_time, most_popular_board, most_popular_rules, daily_games, hourly_distribution)
            VALUES (1, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(global_stats.get("total_games") or 0),
                int(global_stats.get("total_time") or 0),
                int(global_stats.get("most_popular_board") or 0),
                str(global_stats.get("most_popular_rules") or ""),
                self._json_dumps(global_stats.get("daily_games") or {}),
                self._json_dumps(global_stats.get("hourly_distribution") or {}),
            ),
        )
        self.connection.commit()

    def add_replay_comment(
        self,
        session_id: str,
        node_path: str,
        move_number: int,
        text: str,
        author: str = "",
        evaluation: Optional[str] = None,
    ) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO replay_comments
            (session_id, node_path, move_number, text, author, evaluation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (session_id, node_path, int(move_number or 0), text, author or "", evaluation),
        )
        self.connection.commit()

    def list_replay_comments(self, session_id: str) -> List[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT node_path, move_number, text, author, evaluation
            FROM replay_comments
            WHERE session_id = ?
            ORDER BY id
            """,
            (session_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


_global_user_db: Optional[UserDatabase] = None


def get_user_db() -> UserDatabase:
    global _global_user_db
    if _global_user_db is None:
        _global_user_db = UserDatabase()
    return _global_user_db
