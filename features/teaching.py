"""
教学系统模块
提供规则教程、战术训练、互动课程等功能
"""

import hashlib
import json
import time
import uuid
from typing import List, Dict, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from pathlib import Path

from utils.content_db import ContentDatabase, get_content_db
from ui.translator import get_translator
from utils.user_db import get_user_db

# 导入核心模块
from core import Board, Rules, MoveResult


def _resolve_translator(translator=None):
    return translator or get_translator()


class LessonType(Enum):
    """课程类型"""
    RULES = 'rules'  # 规则
    BASICS = 'basics'  # 基础
    TACTICS = 'tactics'  # 战术
    STRATEGY = 'strategy'  # 战略
    LIFE_DEATH = 'life_death'  # 死活
    TESUJI = 'tesuji'  # 手筋
    ENDGAME = 'endgame'  # 收官


class DifficultyLevel(Enum):
    """难度级别"""
    BEGINNER = 1  # 初学者
    ELEMENTARY = 2  # 初级
    INTERMEDIATE = 3  # 中级
    ADVANCED = 4  # 高级
    EXPERT = 5  # 专家


@dataclass
class Lesson:
    """课程"""
    id: str
    title: str
    type: LessonType
    difficulty: DifficultyLevel
    description: str
    content: List['LessonContent']
    prerequisites: List[str] = field(default_factory=list)  # 先修课程
    objectives: List[str] = field(default_factory=list)  # 学习目标
    estimated_time: int = 15  # 预计时间（分钟）
    
    def get_progress(self, completed_steps: Set[int]) -> float:
        """获取进度"""
        if not self.content:
            return 1.0
        return len(completed_steps) / len(self.content)


@dataclass
class LessonContent:
    """课程内容"""
    step: int
    type: str  # 'text', 'demo', 'puzzle', 'quiz'
    title: str
    content: Dict[str, Any]
    
    def is_interactive(self) -> bool:
        """是否为互动内容"""
        return self.type in ['puzzle', 'quiz']


@dataclass
class Puzzle:
    """棋题"""
    id: str
    title: str
    difficulty: int
    board_state: List[List[str]]  # 棋盘状态
    player_color: str
    objective: str  # 目标描述
    solution: List[Tuple[int, int]]  # 正解序列
    wrong_moves: Dict[Tuple[int, int], str]  # 错误着法及提示
    hint: str = ""
    explanation: str = ""
    
    def check_move(
        self,
        x: int,
        y: int,
        translator=None,
    ) -> Tuple[bool, str]:
        """检查着法"""
        move = (x, y)
        translator = _resolve_translator(translator)
        
        # 检查是否为正解
        if self.solution and move == self.solution[0]:
            return True, translator.get("puzzle_correct")
        
        # 检查是否为已知错误
        if move in self.wrong_moves:
            return False, self.wrong_moves[move]
        
        return False, translator.get("puzzle_try_again")


class PuzzleDatabase:
    """棋题数据库"""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path) if db_path else ":memory:"
        self.connection = None
        self._init_database()

    def _init_database(self):
        if self.db_path != ":memory:":
            try:
                Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS puzzles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                difficulty INTEGER DEFAULT 1,
                board_size INTEGER NOT NULL,
                board_state TEXT NOT NULL,
                player_color TEXT NOT NULL,
                objective TEXT NOT NULL,
                solution TEXT NOT NULL,
                wrong_moves TEXT,
                hint TEXT,
                explanation TEXT,
                tags TEXT,
                source TEXT,
                pack_version TEXT,
                content_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS puzzle_translations (
                puzzle_id TEXT NOT NULL,
                language TEXT NOT NULL,
                title TEXT,
                objective TEXT,
                hint TEXT,
                explanation TEXT,
                wrong_moves TEXT,
                PRIMARY KEY (puzzle_id, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS puzzle_packs (
                pack_id TEXT PRIMARY KEY,
                name TEXT,
                version TEXT,
                languages TEXT,
                description TEXT,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.connection.commit()
        self._migrate_schema()
        self._backfill_content_hashes()

    def _table_columns(self, table: str) -> List[str]:
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]

    def _migrate_schema(self) -> None:
        cursor = self.connection.cursor()
        columns = set(self._table_columns("puzzles"))
        if "source" not in columns:
            cursor.execute("ALTER TABLE puzzles ADD COLUMN source TEXT")
        if "tags" not in columns:
            cursor.execute("ALTER TABLE puzzles ADD COLUMN tags TEXT")
        if "pack_version" not in columns:
            cursor.execute("ALTER TABLE puzzles ADD COLUMN pack_version TEXT")
        if "content_hash" not in columns:
            cursor.execute("ALTER TABLE puzzles ADD COLUMN content_hash TEXT")
        self.connection.commit()

    def _compute_content_hash(
        self,
        board_state: List[List[str]],
        player_color: str,
        solution: List[Tuple[int, int]],
        board_size: int,
    ) -> str:
        payload = {
            "board_size": int(board_size),
            "board_state": board_state,
            "player_color": player_color,
            "solution": [[int(x), int(y)] for x, y in solution],
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _backfill_content_hashes(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, board_size, board_state, player_color, solution, content_hash
            FROM puzzles
            """
        )
        updates: List[Tuple[str, str]] = []
        for puzzle_id, board_size, board_state_json, player_color, solution_json, content_hash in cursor.fetchall():
            if content_hash:
                continue
            try:
                board_state_raw = json.loads(board_state_json)
            except Exception:
                board_state_raw = []
            size = int(board_size) if board_size else len(board_state_raw) or 19
            if isinstance(board_state_raw, list):
                board_state = self._normalize_board_state(board_state_raw, size)
            else:
                board_state = [['' for _ in range(size)] for _ in range(size)]
            solution = self._deserialize_solution(solution_json)
            color = self._normalize_color(player_color) or 'black'
            digest = self._compute_content_hash(board_state, color, solution, size)
            updates.append((digest, puzzle_id))
        if updates:
            cursor.executemany(
                "UPDATE puzzles SET content_hash = ? WHERE id = ?",
                updates,
            )
            self.connection.commit()

    def _normalize_color(self, value: Any) -> str:
        if value is None:
            return ''
        token = str(value).strip().lower()
        if token in ('b', 'black', '1'):
            return 'black'
        if token in ('w', 'white', '2'):
            return 'white'
        return ''

    def _build_board_from_stones(self, size: int, stones: List[Any]) -> List[List[str]]:
        board = [['' for _ in range(size)] for _ in range(size)]
        for stone in stones or []:
            if isinstance(stone, dict):
                x = stone.get('x')
                y = stone.get('y')
                color = stone.get('color') or stone.get('c')
            elif isinstance(stone, (list, tuple)) and len(stone) >= 3:
                x, y, color = stone[0], stone[1], stone[2]
            else:
                continue

            try:
                x = int(x)
                y = int(y)
            except Exception:
                continue

            color = self._normalize_color(color)
            if not color:
                continue

            if 0 <= x < size and 0 <= y < size:
                board[y][x] = color
        return board

    def _normalize_board_state(self, board_state: List[Any], size: int) -> List[List[str]]:
        board = [['' for _ in range(size)] for _ in range(size)]
        for y in range(min(size, len(board_state))):
            row = board_state[y] or []
            for x in range(min(size, len(row))):
                color = self._normalize_color(row[x])
                if color:
                    board[y][x] = color
        return board

    def _parse_solution(self, data: Any) -> List[Tuple[int, int]]:
        sequence: List[Tuple[int, int]] = []
        if not data or not isinstance(data, (list, tuple)):
            return sequence

        for item in data:
            if isinstance(item, dict):
                x = item.get('x')
                y = item.get('y')
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                x, y = item[0], item[1]
            else:
                continue

            try:
                x = int(x)
                y = int(y)
            except Exception:
                continue

            sequence.append((x, y))
        return sequence

    def _parse_wrong_moves(self, data: Any) -> Dict[Tuple[int, int], str]:
        result: Dict[Tuple[int, int], str] = {}
        if not data:
            return result

        if isinstance(data, dict):
            for key, msg in data.items():
                x = y = None
                if isinstance(key, str) and ',' in key:
                    parts = key.split(',', 1)
                    try:
                        x = int(parts[0].strip())
                        y = int(parts[1].strip())
                    except Exception:
                        x = y = None
                elif isinstance(key, (list, tuple)) and len(key) >= 2:
                    try:
                        x = int(key[0])
                        y = int(key[1])
                    except Exception:
                        x = y = None
                if x is None or y is None:
                    continue
                result[(x, y)] = str(msg) if msg is not None else ''
            return result

        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                x = item.get('x')
                y = item.get('y')
                msg = item.get('message') or item.get('hint') or item.get('comment') or ''
                try:
                    x = int(x)
                    y = int(y)
                except Exception:
                    continue
                result[(x, y)] = str(msg)
        return result

    def _serialize_wrong_moves(self, wrong_moves: Dict[Tuple[int, int], str]) -> str:
        if not wrong_moves:
            return ''
        payload = {f"{x},{y}": msg for (x, y), msg in wrong_moves.items()}
        return json.dumps(payload, ensure_ascii=False)

    def _deserialize_wrong_moves(self, value: str) -> Dict[Tuple[int, int], str]:
        if not value:
            return {}
        try:
            data = json.loads(value)
        except Exception:
            return {}
        return self._parse_wrong_moves(data)

    def _deserialize_solution(self, value: str) -> List[Tuple[int, int]]:
        if not value:
            return []
        try:
            data = json.loads(value)
        except Exception:
            return []
        return self._parse_solution(data)

    def _puzzle_exists(self, puzzle_id: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM puzzles WHERE id = ? LIMIT 1", (puzzle_id,))
        return cursor.fetchone() is not None

    def _ensure_unique_id(self, puzzle_id: str) -> str:
        candidate = puzzle_id.strip() if puzzle_id else "imported"
        if not self._puzzle_exists(candidate):
            return candidate
        return f"{candidate}_{uuid.uuid4().hex[:6]}"

    def _get_puzzle_source(self, puzzle_id: str) -> str:
        cursor = self.connection.cursor()
        cursor.execute("SELECT source FROM puzzles WHERE id = ? LIMIT 1", (puzzle_id,))
        row = cursor.fetchone()
        return str(row[0]) if row and row[0] is not None else ''

    def has_puzzle_source(self, source: str) -> bool:
        if not source:
            return False
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM puzzles WHERE source = ? LIMIT 1", (source,))
        return cursor.fetchone() is not None

    def _find_puzzle_by_hash(self, content_hash: str) -> Optional[Tuple[str, str]]:
        if not content_hash:
            return None
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT id, source FROM puzzles WHERE content_hash = ? LIMIT 1",
            (content_hash,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        return (str(row[0]), str(row[1]) if row[1] is not None else '')

    def get_pack_info(self, pack_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT pack_id, name, version, languages, description FROM puzzle_packs WHERE pack_id = ?",
            (pack_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        languages = []
        if row[3]:
            try:
                languages = json.loads(row[3])
            except Exception:
                languages = []
        return {
            "id": str(row[0]),
            "name": str(row[1] or ''),
            "version": str(row[2] or ''),
            "languages": languages,
            "description": str(row[4] or ''),
        }

    def set_pack_info(self, pack_meta: Dict[str, Any]) -> None:
        if not pack_meta:
            return
        pack_id = str(pack_meta.get('id') or '').strip()
        if not pack_id:
            return
        languages = pack_meta.get('languages') or []
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO puzzle_packs
            (pack_id, name, version, languages, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                pack_id,
                str(pack_meta.get('name') or ''),
                str(pack_meta.get('version') or ''),
                json.dumps(languages, ensure_ascii=False),
                str(pack_meta.get('description') or ''),
            ),
        )
        self.connection.commit()

    def list_translations(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT puzzle_id, language, title, objective, hint, explanation, wrong_moves
            FROM puzzle_translations
            """
        )
        translations: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for row in cursor.fetchall():
            puzzle_id, language, title, objective, hint, explanation, wrong_moves_json = row
            wrong_moves: Dict[str, str] = {}
            if wrong_moves_json:
                try:
                    data = json.loads(wrong_moves_json)
                    if isinstance(data, dict):
                        wrong_moves = {str(k): str(v) for k, v in data.items()}
                except Exception:
                    wrong_moves = {}
            translations.setdefault(str(puzzle_id), {})[str(language)] = {
                "title": str(title or ''),
                "objective": str(objective or ''),
                "hint": str(hint or ''),
                "explanation": str(explanation or ''),
                "wrong_moves": wrong_moves,
            }
        return translations

    def upsert_translations(
        self,
        puzzle_id: str,
        translations: Dict[str, Dict[str, Any]],
    ) -> None:
        if not puzzle_id or not translations:
            return
        rows = []
        for language, data in translations.items():
            if not language:
                continue
            wrong_moves_json = json.dumps(
                data.get('wrong_moves') or {},
                ensure_ascii=False,
            )
            rows.append(
                (
                    puzzle_id,
                    language,
                    str(data.get('title') or ''),
                    str(data.get('objective') or ''),
                    str(data.get('hint') or ''),
                    str(data.get('explanation') or ''),
                    wrong_moves_json,
                )
            )
        if not rows:
            return
        cursor = self.connection.cursor()
        cursor.executemany(
            """
            INSERT OR REPLACE INTO puzzle_translations
            (puzzle_id, language, title, objective, hint, explanation, wrong_moves)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.connection.commit()

    def sync_pack_translations(
        self,
        pack_id: str,
        translations_by_puzzle: Dict[str, Dict[str, Dict[str, Any]]],
    ) -> int:
        if not pack_id or not translations_by_puzzle:
            return 0
        pack_source = f"pack:{pack_id}"
        updated = 0
        for puzzle_id, lang_payload in translations_by_puzzle.items():
            source = self._get_puzzle_source(puzzle_id)
            if source not in (pack_source, "builtin", ""):
                continue
            self.upsert_translations(puzzle_id, lang_payload)
            updated += 1
        return updated

    def add_puzzle(
        self,
        puzzle: Puzzle,
        source: str = "",
        tags: Optional[List[str]] = None,
        pack_version: str = "",
        content_hash: str = "",
    ):
        board_state_json = json.dumps(puzzle.board_state, ensure_ascii=False)
        solution_json = json.dumps(
            [[int(x), int(y)] for x, y in puzzle.solution],
            ensure_ascii=False,
        )
        wrong_moves_json = self._serialize_wrong_moves(puzzle.wrong_moves)
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        if not content_hash:
            content_hash = self._compute_content_hash(
                puzzle.board_state,
                puzzle.player_color,
                puzzle.solution,
                len(puzzle.board_state),
            )

        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO puzzles (
                id, title, difficulty, board_size, board_state, player_color,
                objective, solution, wrong_moves, hint, explanation, tags, source,
                pack_version, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                puzzle.id,
                puzzle.title,
                int(puzzle.difficulty),
                int(len(puzzle.board_state)),
                board_state_json,
                puzzle.player_color,
                puzzle.objective,
                solution_json,
                wrong_moves_json,
                puzzle.hint,
                puzzle.explanation,
                tags_json,
                source or '',
                pack_version or '',
                content_hash or '',
            ),
        )
        self.connection.commit()

    def merge_puzzle(
        self,
        puzzle: Puzzle,
        strategy: str = "copy",
        source: str = "",
        tags: Optional[List[str]] = None,
        pack_version: str = "",
    ) -> Tuple[str, bool]:
        strategy = (strategy or "copy").strip().lower()
        content_hash = self._compute_content_hash(
            puzzle.board_state,
            puzzle.player_color,
            puzzle.solution,
            len(puzzle.board_state),
        )
        existing_id = puzzle.id if self._puzzle_exists(puzzle.id) else ""
        existing_hash = self._find_puzzle_by_hash(content_hash)

        if strategy == "skip":
            if existing_id:
                return existing_id, False
            if existing_hash:
                return existing_hash[0], False

        if strategy == "overwrite":
            if existing_id:
                puzzle.id = existing_id
                self.add_puzzle(
                    puzzle,
                    source=source,
                    tags=tags,
                    pack_version=pack_version,
                    content_hash=content_hash,
                )
                return puzzle.id, True
            if existing_hash:
                puzzle.id = existing_hash[0]
                self.add_puzzle(
                    puzzle,
                    source=source,
                    tags=tags,
                    pack_version=pack_version,
                    content_hash=content_hash,
                )
                return puzzle.id, True

        if existing_id or existing_hash:
            puzzle.id = self._ensure_unique_id(puzzle.id)

        self.add_puzzle(
            puzzle,
            source=source,
            tags=tags,
            pack_version=pack_version,
            content_hash=content_hash,
        )
        return puzzle.id, True

    def list_puzzles(self) -> List[Puzzle]:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id, title, difficulty, board_size, board_state, player_color,
                   objective, solution, wrong_moves, hint, explanation
            FROM puzzles
            ORDER BY id
            """
        )
        puzzles: List[Puzzle] = []
        for row in cursor.fetchall():
            puzzle = self._row_to_puzzle(row)
            if puzzle:
                puzzles.append(puzzle)
        return puzzles

    def list_puzzle_ids(self) -> List[str]:
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM puzzles")
        return [row[0] for row in cursor.fetchall()]

    def count_puzzles(self) -> int:
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM puzzles")
        row = cursor.fetchone()
        return int(row[0]) if row else 0

    def _row_to_puzzle(self, row: Tuple[Any, ...]) -> Optional[Puzzle]:
        (
            puzzle_id,
            title,
            difficulty,
            board_size,
            board_state_json,
            player_color,
            objective,
            solution_json,
            wrong_moves_json,
            hint,
            explanation,
        ) = row

        try:
            board_state_raw = json.loads(board_state_json)
        except Exception:
            board_state_raw = []

        size = int(board_size) if board_size else len(board_state_raw) or 19
        if isinstance(board_state_raw, list):
            board_state = self._normalize_board_state(board_state_raw, size)
        else:
            board_state = [['' for _ in range(size)] for _ in range(size)]

        solution = self._deserialize_solution(solution_json)
        wrong_moves = self._deserialize_wrong_moves(wrong_moves_json or '')
        player_color = self._normalize_color(player_color) or 'black'

        return Puzzle(
            id=str(puzzle_id),
            title=str(title),
            difficulty=int(difficulty) if difficulty else 1,
            board_state=board_state,
            player_color=player_color,
            objective=str(objective),
            solution=solution,
            wrong_moves=wrong_moves,
            hint=str(hint or ''),
            explanation=str(explanation or ''),
        )

    def import_from_json(self, file_path: str, strategy: str = "copy") -> int:
        text = self._read_text(file_path)
        if not text:
            return 0
        try:
            data = json.loads(text)
        except Exception:
            return 0

        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            items = data.get('puzzles') or data.get('items') or data.get('data') or []
            if isinstance(items, dict):
                items = list(items.values())
        else:
            return 0

        count = 0
        base_name = Path(file_path).stem
        for index, item in enumerate(items, start=1):
            fallback_title = f"{base_name} #{index}"
            fallback_id = f"imported_{uuid.uuid4().hex[:8]}"
            puzzle = self._puzzle_from_dict(item, fallback_title, fallback_id)
            if puzzle:
                tags = []
                if isinstance(item, dict):
                    tags = item.get('tags') or item.get('tag') or []
                    if isinstance(tags, str):
                        tags = [tags]
                    if not isinstance(tags, list):
                        tags = []
                _, changed = self.merge_puzzle(
                    puzzle,
                    strategy=strategy,
                    source=Path(file_path).name,
                    tags=tags,
                )
                if changed:
                    count += 1
        return count

    def import_from_sgf(self, file_path: str, strategy: str = "copy") -> int:
        text = self._read_text(file_path)
        if not text:
            return 0

        trees = self._split_sgf_trees(text)
        count = 0
        for index, tree in enumerate(trees, start=1):
            puzzle = self._puzzle_from_sgf(tree, Path(file_path).name, index)
            if puzzle:
                _, changed = self.merge_puzzle(
                    puzzle,
                    strategy=strategy,
                    source=Path(file_path).name,
                )
                if changed:
                    count += 1
        return count

    def _read_pack_meta(self, pack_dir: Path) -> Optional[Dict[str, Any]]:
        try:
            meta_text = (pack_dir / "pack.json").read_text(encoding="utf-8")
            meta = json.loads(meta_text)
        except Exception:
            return None
        if not isinstance(meta, dict):
            return None
        return meta

    def read_pack_meta(self, pack_dir: Path) -> Optional[Dict[str, Any]]:
        return self._read_pack_meta(pack_dir)

    def _read_pack_puzzles(self, pack_dir: Path) -> List[Dict[str, Any]]:
        try:
            puzzles_text = (pack_dir / "puzzles.json").read_text(encoding="utf-8")
            data = json.loads(puzzles_text)
        except Exception:
            return []
        if isinstance(data, list):
            return data
        return []

    def _read_pack_translations(
        self, pack_dir: Path, languages: List[str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        translations: Dict[str, Dict[str, Dict[str, Any]]] = {}
        i18n_dir = pack_dir / "i18n"
        for lang in languages or []:
            path = i18n_dir / f"{lang}.json"
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8")
                data = json.loads(text)
            except Exception:
                continue
            if isinstance(data, dict):
                translations[lang] = data
        return translations

    def import_pack(
        self,
        pack_dir: str,
        strategy: str = "overwrite",
        protect_user: bool = True,
    ) -> Tuple[int, List[str]]:
        errors: List[str] = []
        base_dir = Path(pack_dir)
        meta = self._read_pack_meta(base_dir)
        if not meta:
            return 0, ["pack.json missing or invalid"]

        pack_id = str(meta.get("id") or "default").strip() or "default"
        pack_version = str(meta.get("version") or "")
        languages = meta.get("languages") or []
        if not isinstance(languages, list):
            languages = []
        translations = self._read_pack_translations(base_dir, languages)
        base_language = "zh" if "zh" in translations else (languages[0] if languages else "")
        pack_source = f"pack:{pack_id}"
        translations_by_puzzle: Dict[str, Dict[str, Dict[str, Any]]] = {}
        for lang, mapping in translations.items():
            if not isinstance(mapping, dict):
                continue
            for puzzle_id, payload in mapping.items():
                if isinstance(payload, dict):
                    translations_by_puzzle.setdefault(str(puzzle_id), {})[lang] = payload

        puzzles = self._read_pack_puzzles(base_dir)
        count = 0
        for data in puzzles:
            if not isinstance(data, dict):
                continue
            puzzle_id = str(data.get("id") or "").strip()
            if not puzzle_id:
                errors.append("puzzles.json: missing puzzle id")
                continue

            text_data = translations.get(base_language, {}).get(puzzle_id, {}) if base_language else {}
            puzzle = self._puzzle_from_pack_dict(data, text_data)
            if not puzzle:
                errors.append(f"{puzzle_id}: invalid puzzle definition")
                continue

            tags = data.get("tags") or []
            if isinstance(tags, str):
                tags = [tags]
            if not isinstance(tags, list):
                tags = []

            local_strategy = strategy
            if protect_user:
                existing_source = self._get_puzzle_source(puzzle.id)
                if existing_source and existing_source not in (pack_source, "builtin", ""):
                    local_strategy = "copy"
                content_hash = self._compute_content_hash(
                    puzzle.board_state,
                    puzzle.player_color,
                    puzzle.solution,
                    len(puzzle.board_state),
                )
                existing_hash = self._find_puzzle_by_hash(content_hash)
                if (
                    existing_hash
                    and existing_hash[1]
                    and existing_hash[1] not in (pack_source, "builtin", "")
                ):
                    local_strategy = "skip"

            merged_id, changed = self.merge_puzzle(
                puzzle,
                strategy=local_strategy,
                source=pack_source,
                tags=tags,
                pack_version=pack_version,
            )
            if translations_by_puzzle:
                payload = translations_by_puzzle.get(puzzle_id)
                if payload:
                    self.upsert_translations(merged_id, payload)
            if changed:
                count += 1

        self.set_pack_info(meta)
        return count, errors

    def remove_pack(self, pack_id: str) -> None:
        if not pack_id:
            return
        pack_source = f"pack:{pack_id}"
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM puzzles WHERE source = ?", (pack_source,))
        cursor.execute(
            "DELETE FROM puzzle_translations WHERE puzzle_id NOT IN (SELECT id FROM puzzles)"
        )
        cursor.execute("DELETE FROM puzzle_packs WHERE pack_id = ?", (pack_id,))
        self.connection.commit()

    def _puzzle_from_dict(
        self,
        data: Any,
        fallback_title: str,
        fallback_id: str,
    ) -> Optional[Puzzle]:
        if not isinstance(data, dict):
            return None

        title = str(data.get('title') or data.get('name') or fallback_title).strip()
        difficulty = data.get('difficulty') or data.get('level') or 1
        try:
            difficulty = int(difficulty)
        except Exception:
            difficulty = 1
        difficulty = max(1, min(5, difficulty))

        size = data.get('board_size') or data.get('size') or 19
        try:
            size = int(size)
        except Exception:
            size = 19

        board_state = data.get('board_state')
        if isinstance(board_state, list):
            size = len(board_state) or size
            board_state = self._normalize_board_state(board_state, size)
        else:
            stones = data.get('stones') or data.get('setup') or []
            board_state = self._build_board_from_stones(size, stones)

        player_color = self._normalize_color(
            data.get('player_color') or data.get('player') or data.get('color') or 'black'
        ) or 'black'

        objective = str(data.get('objective') or data.get('goal') or '请走出最佳一手')
        solution = self._parse_solution(data.get('solution') or data.get('moves') or [])
        if not solution:
            return None

        wrong_moves = self._parse_wrong_moves(
            data.get('wrong_moves') or data.get('wrong') or data.get('wrong_move') or {}
        )
        hint = str(data.get('hint') or '')
        explanation = str(data.get('explanation') or data.get('comment') or '')

        puzzle_id = str(data.get('id') or fallback_id).strip() or fallback_id

        return Puzzle(
            id=puzzle_id,
            title=title,
            difficulty=difficulty,
            board_state=board_state,
            player_color=player_color,
            objective=objective,
            solution=solution,
            wrong_moves=wrong_moves,
            hint=hint,
            explanation=explanation,
        )

    def _puzzle_from_pack_dict(
        self,
        data: Any,
        text_data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Puzzle]:
        if not isinstance(data, dict):
            return None

        puzzle_id = str(data.get('id') or '').strip()
        if not puzzle_id:
            return None

        difficulty = data.get('difficulty') or data.get('level') or 1
        try:
            difficulty = int(difficulty)
        except Exception:
            difficulty = 1
        difficulty = max(1, min(5, difficulty))

        size = data.get('board_size') or data.get('size') or 19
        try:
            size = int(size)
        except Exception:
            size = 19

        board_state = data.get('board_state')
        if isinstance(board_state, list):
            size = len(board_state) or size
            board_state = self._normalize_board_state(board_state, size)
        else:
            stones = data.get('stones') or data.get('setup') or []
            board_state = self._build_board_from_stones(size, stones)

        player_color = self._normalize_color(
            data.get('player_color') or data.get('player') or data.get('color') or 'black'
        ) or 'black'

        solution = self._parse_solution(data.get('solution') or data.get('moves') or [])
        if not solution:
            return None

        text_data = text_data or {}
        title = str(text_data.get('title') or data.get('title') or puzzle_id).strip()
        objective = str(text_data.get('objective') or data.get('objective') or '请走出最佳一手')
        hint = str(text_data.get('hint') or data.get('hint') or '')
        explanation = str(text_data.get('explanation') or data.get('explanation') or '')
        wrong_moves = self._parse_wrong_moves(
            text_data.get('wrong_moves') or data.get('wrong_moves') or {}
        )

        return Puzzle(
            id=puzzle_id,
            title=title,
            difficulty=difficulty,
            board_state=board_state,
            player_color=player_color,
            objective=objective,
            solution=solution,
            wrong_moves=wrong_moves,
            hint=hint,
            explanation=explanation,
        )

    def _read_text(self, file_path: str) -> str:
        encodings = ('utf-8', 'utf-8-sig', 'gbk', 'latin-1')
        for encoding in encodings:
            try:
                return Path(file_path).read_text(encoding=encoding)
            except Exception:
                continue
        return ''

    def _scan_sgf_value(self, text: str, index: int) -> Tuple[str, int]:
        if index >= len(text) or text[index] != '[':
            return '', index
        index += 1
        value_chars: List[str] = []
        while index < len(text):
            ch = text[index]
            if ch == '\\':
                index += 1
                if index >= len(text):
                    break
                if text[index] in '\r\n':
                    index += 1
                    continue
                value_chars.append(text[index])
                index += 1
                continue
            if ch == ']':
                index += 1
                break
            value_chars.append(ch)
            index += 1
        return ''.join(value_chars), index

    def _split_sgf_trees(self, text: str) -> List[str]:
        trees: List[str] = []
        depth = 0
        start = None
        index = 0
        while index < len(text):
            ch = text[index]
            if ch == '[':
                _, index = self._scan_sgf_value(text, index)
                continue
            if ch == '(':
                if depth == 0:
                    start = index
                depth += 1
                index += 1
                continue
            if ch == ')':
                depth -= 1
                index += 1
                if depth == 0 and start is not None:
                    trees.append(text[start:index])
                    start = None
                continue
            index += 1

        if not trees and text.strip():
            trees = [text.strip()]
        return trees

    def _parse_sgf_main_line_nodes(self, text: str) -> List[Dict[str, List[str]]]:
        content = text.strip()
        if not content:
            return []

        nodes: List[Dict[str, List[str]]] = []
        index = 0

        def skip_whitespace() -> None:
            nonlocal index
            while index < len(content) and content[index].isspace():
                index += 1

        def parse_identifier() -> str:
            nonlocal index
            start = index
            while index < len(content) and content[index].isupper():
                index += 1
            return content[start:index]

        def parse_node() -> Optional[Dict[str, List[str]]]:
            nonlocal index
            if index >= len(content) or content[index] != ';':
                return None
            index += 1
            props: Dict[str, List[str]] = {}
            while index < len(content):
                skip_whitespace()
                if index >= len(content) or content[index] in ';()':
                    break
                if not content[index].isupper():
                    index += 1
                    continue
                prop = parse_identifier()
                values: List[str] = []
                while index < len(content) and content[index] == '[':
                    value, index = self._scan_sgf_value(content, index)
                    values.append(value)
                if prop:
                    props[prop] = values
            return props

        def skip_variation() -> None:
            nonlocal index
            if index >= len(content) or content[index] != '(':
                return
            depth = 0
            while index < len(content):
                ch = content[index]
                if ch == '[':
                    _, index = self._scan_sgf_value(content, index)
                    continue
                if ch == '(':
                    depth += 1
                    index += 1
                    continue
                if ch == ')':
                    depth -= 1
                    index += 1
                    if depth == 0:
                        break
                    continue
                index += 1

        def parse_variation_main_line() -> List[Dict[str, List[str]]]:
            nonlocal index
            if index >= len(content) or content[index] != '(':
                return []
            index += 1
            line: List[Dict[str, List[str]]] = []
            while index < len(content):
                skip_whitespace()
                if index >= len(content):
                    break
                ch = content[index]
                if ch == ';':
                    node = parse_node()
                    if node:
                        line.append(node)
                    continue
                if ch == '(':
                    child_nodes = parse_variation_main_line()
                    line.extend(child_nodes)
                    while True:
                        skip_whitespace()
                        if index < len(content) and content[index] == '(':
                            skip_variation()
                            continue
                        break
                    continue
                if ch == ')':
                    index += 1
                    break
                index += 1
            return line

        while index < len(content) and content[index] != '(':
            index += 1
        if index < len(content) and content[index] == '(':
            nodes = parse_variation_main_line()

        return nodes

    def _sgf_to_point(self, coord: str) -> Tuple[int, int]:
        if not coord or len(coord) < 2:
            return (-1, -1)
        x = ord(coord[0]) - ord('a')
        y = ord(coord[1]) - ord('a')
        return (x, y)

    def _expand_sgf_points(self, value: str) -> List[Tuple[int, int]]:
        if not value:
            return []
        if ':' in value and len(value) >= 5:
            start, end = value.split(':', 1)
            x1, y1 = self._sgf_to_point(start)
            x2, y2 = self._sgf_to_point(end)
            if x1 < 0 or y1 < 0 or x2 < 0 or y2 < 0:
                return []
            points = []
            for x in range(min(x1, x2), max(x1, x2) + 1):
                for y in range(min(y1, y2), max(y1, y2) + 1):
                    points.append((x, y))
            return points
        x, y = self._sgf_to_point(value)
        if x < 0 or y < 0:
            return []
        return [(x, y)]

    def _parse_sgf_difficulty(self, root: Dict[str, List[str]]) -> int:
        for key in ('DI', 'DL', 'LV'):
            value = root.get(key)
            if not value:
                continue
            try:
                return max(1, min(5, int(float(value[0]))))
            except Exception:
                continue
        return 3

    def _puzzle_from_sgf(
        self,
        sgf_text: str,
        label: str,
        index: int,
    ) -> Optional[Puzzle]:
        nodes = self._parse_sgf_main_line_nodes(sgf_text)
        if not nodes:
            return None

        root = nodes[0]
        size_value = (root.get('SZ') or ['19'])[0]
        try:
            size = int(size_value)
        except Exception:
            size = 19

        stones: List[Tuple[int, int, str]] = []
        for prop, color in (('AB', 'black'), ('AW', 'white')):
            for raw in root.get(prop, []) or []:
                for x, y in self._expand_sgf_points(raw):
                    stones.append((x, y, color))

        board_state = self._build_board_from_stones(size, stones)

        solution: List[Tuple[int, int]] = []
        player_color = ''
        for node in nodes[1:]:
            if 'B' in node:
                color = 'black'
                coord = node['B'][0] if node['B'] else ''
            elif 'W' in node:
                color = 'white'
                coord = node['W'][0] if node['W'] else ''
            else:
                continue

            if not coord:
                continue

            x, y = self._sgf_to_point(coord)
            if x < 0 or y < 0:
                continue

            solution.append((x, y))
            if not player_color:
                player_color = color

        if not solution:
            return None

        if not player_color:
            pl = (root.get('PL') or [''])[0].strip().lower()
            if pl in ('w', 'white'):
                player_color = 'white'
            else:
                player_color = 'black'

        title = (root.get('GN') or root.get('N') or [f"{label} #{index}"])[0]
        title = title.strip() or f"{label} #{index}"
        comment = (root.get('C') or [''])[0].strip()
        objective = comment.splitlines()[0].strip() if comment else "请走出最佳一手"
        difficulty = self._parse_sgf_difficulty(root)
        puzzle_id = self._ensure_unique_id(f"sgf_{uuid.uuid4().hex[:8]}")

        return Puzzle(
            id=puzzle_id,
            title=title,
            difficulty=difficulty,
            board_state=board_state,
            player_color=player_color,
            objective=objective,
            solution=solution,
            wrong_moves={},
            hint='',
            explanation=comment,
        )

class TeachingSystem:
    """教学系统"""
    
    def __init__(
        self,
        translator=None,
        content_db: Optional[ContentDatabase] = None,
        user_db=None,
        user_id: str = "default",
    ):
        # translator 目前仅作占位，便于未来本地化提示
        self.translator = translator
        self.content_db = content_db or get_content_db()
        self.user_db = user_db or get_user_db()
        self.user_id = user_id or "default"
        self._content_language = (
            getattr(translator, 'language', None) if translator else None
        ) or 'zh'
        self._puzzle_texts: Dict[str, Dict[str, Dict[str, Any]]] = {}
        self.lessons: Dict[str, Lesson] = {}
        self.puzzles: Dict[str, Puzzle] = {}
        self.puzzle_db: Optional[PuzzleDatabase] = None
        self.user_progress: Dict[str, Any] = {
            'completed_lessons': [],
            'completed_puzzles': [],
            'current_lesson': None,
            'total_score': 0,
            'statistics': {}
        }
        
        self._load_lessons()
        self._load_puzzles()
        self._load_user_progress()
    
    def _load_lessons(self):
        """加载课程"""
        self.lessons = {}
        if self._load_lessons_from_content():
            return

        # 规则课程
        self.lessons['rules_basic'] = self._create_rules_lesson()
        
        # 基础课程
        self.lessons['basics_capture'] = self._create_capture_lesson()
        self.lessons['basics_territory'] = self._create_territory_lesson()
        
        # 战术课程
        self.lessons['tactics_ladder'] = self._create_ladder_lesson()
        self.lessons['tactics_net'] = self._create_net_lesson()

    def _load_user_progress(self) -> None:
        if not self.user_db:
            return
        try:
            summary = self.user_db.get_user_summary(self.user_id)
            completed_lessons = self.user_db.list_completed_lessons(self.user_id)
            completed_puzzles = self.user_db.list_completed_puzzles(self.user_id)
        except Exception:
            return

        self.user_progress['completed_lessons'] = completed_lessons
        self.user_progress['completed_puzzles'] = completed_puzzles
        self.user_progress['current_lesson'] = summary.get('current_lesson')
        self.user_progress['total_score'] = int(summary.get('total_score') or 0)

        for lesson_id in completed_lessons:
            steps = self.user_db.list_lesson_steps(self.user_id, lesson_id)
            self.user_progress[lesson_id] = {'completed_steps': set(steps)}

    def _load_lessons_from_content(self) -> bool:
        if not self.content_db:
            return False
        language = self._content_language
        lesson_rows = self.content_db.list_lessons(language)
        if not lesson_rows and language != 'zh':
            language = 'zh'
            lesson_rows = self.content_db.list_lessons(language)
        if not lesson_rows:
            return False

        type_map = {item.value: item for item in LessonType}
        difficulty_map = {item.value: item for item in DifficultyLevel}

        for lesson_row in lesson_rows:
            lesson_id = lesson_row.get('id')
            if not lesson_id:
                continue
            steps_data = self.content_db.list_lesson_steps(lesson_id, language)
            if not steps_data and language != 'zh':
                steps_data = self.content_db.list_lesson_steps(lesson_id, 'zh')
            content_items: List[LessonContent] = []
            for step in steps_data:
                content_items.append(
                    LessonContent(
                        step=int(step.get('step') or 0),
                        type=str(step.get('type') or ''),
                        title=str(step.get('title') or ''),
                        content=step.get('content') or {},
                    )
                )

            lesson_type = type_map.get(str(lesson_row.get('type') or '').strip())
            difficulty_value = int(lesson_row.get('difficulty') or 1)
            difficulty = difficulty_map.get(difficulty_value, DifficultyLevel.BEGINNER)
            if not lesson_type:
                lesson_type = LessonType.BASICS

            self.lessons[lesson_id] = Lesson(
                id=lesson_id,
                title=str(lesson_row.get('title') or ''),
                type=lesson_type,
                difficulty=difficulty,
                description=str(lesson_row.get('description') or ''),
                content=content_items,
                prerequisites=lesson_row.get('prerequisites') or [],
                objectives=lesson_row.get('objectives') or [],
                estimated_time=int(lesson_row.get('estimated_time') or 0),
            )

        return bool(self.lessons)
    
    def _create_rules_lesson(self) -> Lesson:
        """创建规则课程"""
        content = [
            LessonContent(
                step=1,
                type='text',
                title='围棋简介',
                content={
                    'text': """围棋是一种两人对弈的策略棋盘游戏，起源于中国，已有4000多年历史。

围棋的基本规则非常简单：
1. 黑白双方轮流下子
2. 棋子下在交叉点上
3. 被围住的棋子会被吃掉
4. 占地多的一方获胜

但是，简单的规则蕴含着无穷的变化，这正是围棋的魅力所在。""",
                    'image': None
                }
            ),
            LessonContent(
                step=2,
                type='demo',
                title='如何落子',
                content={
                    'text': '棋子下在交叉点上，不是格子里。点击交叉点即可落子。',
                    'demo_moves': [(9, 9, 'black'), (9, 10, 'white')]
                }
            ),
            LessonContent(
                step=3,
                type='text',
                title='气的概念',
                content={
                    'text': """气是围棋中最重要的概念之一。

一个棋子的"气"是指与它直接相邻的空交叉点。
- 中央的棋子最多有4口气
- 边上的棋子最多有3口气
- 角上的棋子最多有2口气

当一个棋子或一块棋的气全部被对方占据时，就会被提取。"""
                }
            ),
            LessonContent(
                step=4,
                type='puzzle',
                title='练习：提子',
                content={
                    'puzzle_id': 'capture_basic_1'
                }
            )
        ]
        
        return Lesson(
            id='rules_basic',
            title='围棋基本规则',
            type=LessonType.RULES,
            difficulty=DifficultyLevel.BEGINNER,
            description='学习围棋的基本规则和概念',
            content=content,
            objectives=[
                '了解围棋的基本规则',
                '掌握气的概念',
                '学会基本的提子'
            ],
            estimated_time=20
        )
    
    def _create_capture_lesson(self) -> Lesson:
        """创建吃子课程"""
        content = [
            LessonContent(
                step=1,
                type='text',
                title='吃子的基本方法',
                content={
                    'text': """吃子是围棋的基本技术之一。常见的吃子方法包括：

1. **直接吃**：当对方棋子只剩一口气时，直接占据最后一口气
2. **征子**：利用连续叫吃，将对方棋子驱赶到边角吃掉
3. **门吃**：堵住对方棋子的逃路，使其无法逃脱
4. **双吃**：同时威胁两块棋，对方只能救一块"""
                }
            ),
            LessonContent(
                step=2,
                type='demo',
                title='征子演示',
                content={
                    'text': '征子是一种连续叫吃的技术，观察黑棋如何追击白子。',
                    'demo_moves': [
                        (9, 9, 'white'),
                        (10, 9, 'black'),
                        (9, 10, 'white'),
                        (10, 10, 'black'),
                        (9, 11, 'white'),
                        (10, 11, 'black')
                    ]
                }
            ),
            LessonContent(
                step=3,
                type='puzzle',
                title='练习：征子',
                content={
                    'puzzle_id': 'ladder_basic_1'
                }
            )
        ]
        
        return Lesson(
            id='basics_capture',
            title='基本吃子技术',
            type=LessonType.BASICS,
            difficulty=DifficultyLevel.BEGINNER,
            description='学习各种基本的吃子方法',
            content=content,
            prerequisites=['rules_basic'],
            objectives=[
                '掌握直接吃子',
                '学会征子技术',
                '理解门吃和双吃'
            ],
            estimated_time=30
        )
    
    def _create_territory_lesson(self) -> Lesson:
        """创建围地课程"""
        return Lesson(
            id='basics_territory',
            title='围地基础',
            type=LessonType.BASICS,
            difficulty=DifficultyLevel.ELEMENTARY,
            description='学习如何围地和计算地盘',
            content=[],
            prerequisites=['rules_basic'],
            objectives=['理解地盘概念', '学会基本围地'],
            estimated_time=25
        )
    
    def _create_ladder_lesson(self) -> Lesson:
        """创建征子课程"""
        return Lesson(
            id='tactics_ladder',
            title='征子战术',
            type=LessonType.TACTICS,
            difficulty=DifficultyLevel.ELEMENTARY,
            description='深入学习征子及其变化',
            content=[],
            prerequisites=['basics_capture'],
            objectives=['掌握征子判断', '学会征子相关战术'],
            estimated_time=40
        )
    
    def _create_net_lesson(self) -> Lesson:
        """创建网罩课程"""
        return Lesson(
            id='tactics_net',
            title='网罩战术',
            type=LessonType.TACTICS,
            difficulty=DifficultyLevel.INTERMEDIATE,
            description='学习网罩的技巧',
            content=[],
            prerequisites=['basics_capture'],
            objectives=['理解网罩原理', '掌握网罩技巧'],
            estimated_time=35
        )
    
    def _load_puzzles(self):
        """加载棋题（数据库 + 默认题库包）"""
        self.puzzle_db = PuzzleDatabase(self._default_puzzle_db_path())
        self._sync_default_pack()
        self.reload_puzzles()

    def _default_puzzle_db_path(self) -> str:
        base_dir = Path(__file__).resolve().parents[1]
        return str(base_dir / 'saves' / 'puzzles.db')

    def _default_pack_dir(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return base_dir / 'assets' / 'puzzle_packs' / 'default'

    def _version_tuple(self, version: str) -> Tuple[int, ...]:
        parts = []
        for raw in str(version or '').split('.'):
            digits = ''.join(ch for ch in raw if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        return tuple(parts or [0])

    def _is_version_newer(self, new_version: str, old_version: str) -> bool:
        return self._version_tuple(new_version) > self._version_tuple(old_version)

    def reload_puzzles(self) -> None:
        """刷新内存中的题目列表。"""
        if not self.puzzle_db:
            return
        self.puzzles = {puzzle.id: puzzle for puzzle in self.puzzle_db.list_puzzles()}
        self._puzzle_texts = self.puzzle_db.list_translations()

    def _sync_default_pack(self) -> None:
        if not self.puzzle_db:
            return
        pack_dir = self._default_pack_dir()
        if not pack_dir.exists():
            return
        meta = self.puzzle_db.read_pack_meta(pack_dir)
        if not meta:
            return
        pack_id = str(meta.get('id') or 'default').strip() or 'default'
        installed = self.puzzle_db.get_pack_info(pack_id)
        has_puzzles = self.puzzle_db.count_puzzles() > 0
        has_builtin = self.puzzle_db.has_puzzle_source("builtin") or self.puzzle_db.has_puzzle_source(
            f"pack:{pack_id}"
        )
        should_install = False
        if installed is None:
            should_install = (not has_puzzles) or has_builtin
        if installed and meta.get('version'):
            if self._is_version_newer(
                str(meta.get('version')), str(installed.get('version') or '')
            ):
                should_install = True
        if should_install:
            self.puzzle_db.import_pack(str(pack_dir), strategy="overwrite", protect_user=True)
        translations = self.puzzle_db._read_pack_translations(
            pack_dir, meta.get('languages') or []
        )
        if translations:
            translations_by_puzzle: Dict[str, Dict[str, Dict[str, Any]]] = {}
            for lang, mapping in translations.items():
                if not isinstance(mapping, dict):
                    continue
                for puzzle_id, payload in mapping.items():
                    if isinstance(payload, dict):
                        translations_by_puzzle.setdefault(str(puzzle_id), {})[lang] = payload
            if translations_by_puzzle:
                self.puzzle_db.sync_pack_translations(pack_id, translations_by_puzzle)

    def rebuild_default_pack(self) -> Tuple[int, List[str]]:
        if not self.puzzle_db:
            return 0, ["puzzle database not initialized"]
        pack_dir = self._default_pack_dir()
        if not pack_dir.exists():
            return 0, ["default pack missing"]
        meta = self.puzzle_db.read_pack_meta(pack_dir) or {}
        pack_id = str(meta.get('id') or 'default').strip() or 'default'
        self.puzzle_db.remove_pack(pack_id)
        count, errors = self.puzzle_db.import_pack(
            str(pack_dir), strategy="overwrite", protect_user=True
        )
        if count > 0:
            self.reload_puzzles()
        return count, errors

    def import_puzzles(
        self,
        file_paths: List[str],
        strategy: str = "copy",
    ) -> Tuple[int, List[str]]:
        """从文件导入题库，返回(新增数量, 错误信息列表)。"""
        if not self.puzzle_db:
            return 0, ["puzzle database not initialized"]

        total_added = 0
        errors: List[str] = []
        for path in file_paths or []:
            if not path:
                continue
            suffix = Path(path).suffix.lower()
            try:
                if suffix == '.json':
                    added = self.puzzle_db.import_from_json(path, strategy=strategy)
                elif suffix == '.sgf':
                    added = self.puzzle_db.import_from_sgf(path, strategy=strategy)
                else:
                    errors.append(f"{Path(path).name}: unsupported format")
                    continue
                if added == 0:
                    errors.append(f"{Path(path).name}: no valid puzzles")
                total_added += added
            except Exception as exc:
                errors.append(f"{Path(path).name}: {exc}")

        if total_added > 0:
            self.reload_puzzles()
        return total_added, errors

    def _build_puzzle_board(self, size: int, stones: List[Tuple[int, int, str]]) -> List[List[str]]:
        board = [['' for _ in range(size)] for _ in range(size)]
        for x, y, color in stones:
            if color not in ('black', 'white'):
                continue
            if 0 <= x < size and 0 <= y < size:
                board[y][x] = color
        return board
    
    def get_lesson(self, lesson_id: str) -> Optional[Lesson]:
        """获取课程"""
        return self.lessons.get(lesson_id)
    
    def get_puzzle(self, puzzle_id: str) -> Optional[Puzzle]:
        """获取棋题"""
        return self.puzzles.get(puzzle_id)

    def _current_language(self) -> str:
        translator = self.translator
        if translator and getattr(translator, "language", None):
            return translator.language
        return "zh"

    def get_puzzle_text(self, puzzle: Optional[Puzzle], field: str) -> str:
        """获取棋题文本（支持多语言）。"""
        if not puzzle:
            return ""
        text_bundle = self._puzzle_texts.get(puzzle.id)
        if text_bundle:
            lang = self._current_language()
            lang_data = (
                text_bundle.get(lang)
                or text_bundle.get("zh")
                or text_bundle.get("en")
                or {}
            )
            value = lang_data.get(field)
            if value:
                return str(value)
        return str(getattr(puzzle, field, "") or "")

    def get_puzzle_wrong_move_message(
        self, puzzle: Optional[Puzzle], x: int, y: int
    ) -> str:
        """获取指定落子错误提示（支持多语言）。"""
        if not puzzle:
            return ""
        text_bundle = self._puzzle_texts.get(puzzle.id)
        if text_bundle:
            lang = self._current_language()
            lang_data = (
                text_bundle.get(lang)
                or text_bundle.get("zh")
                or text_bundle.get("en")
                or {}
            )
            wrong_moves = lang_data.get("wrong_moves") or {}
            key = f"{x},{y}"
            if key in wrong_moves:
                return str(wrong_moves[key])

        if puzzle.wrong_moves:
            if (x, y) in puzzle.wrong_moves:
                return str(puzzle.wrong_moves[(x, y)])
            key = f"{x},{y}"
            if key in puzzle.wrong_moves:
                return str(puzzle.wrong_moves[key])
        return ""
    
    def start_lesson(self, lesson_id: str) -> bool:
        """开始课程"""
        lesson = self.get_lesson(lesson_id)
        if not lesson:
            return False
        
        # 检查先修课程
        for prereq in lesson.prerequisites:
            if prereq not in self.user_progress['completed_lessons']:
                return False
        
        self.user_progress['current_lesson'] = lesson_id
        if self.user_db:
            try:
                self.user_db.set_user_summary(
                    self.user_id,
                    self.user_progress.get('total_score', 0),
                    lesson_id,
                )
            except Exception:
                pass
        return True
    
    def complete_lesson_step(self, lesson_id: str, step: int):
        """完成课程步骤"""
        if lesson_id not in self.user_progress:
            self.user_progress[lesson_id] = {'completed_steps': set()}
        
        self.user_progress[lesson_id]['completed_steps'].add(step)
        if self.user_db:
            try:
                self.user_db.record_lesson_step(self.user_id, lesson_id, step)
            except Exception:
                pass
        
        # 检查是否完成整个课程
        lesson = self.get_lesson(lesson_id)
        if lesson:
            progress = lesson.get_progress(self.user_progress[lesson_id]['completed_steps'])
            if progress >= 1.0:
                self.complete_lesson(lesson_id)
    
    def complete_lesson(self, lesson_id: str):
        """完成课程"""
        if lesson_id not in self.user_progress['completed_lessons']:
            self.user_progress['completed_lessons'].append(lesson_id)
            self.user_progress['total_score'] += 100
            if self.user_db:
                try:
                    self.user_db.record_lesson_completed(self.user_id, lesson_id, score=100)
                    self.user_db.set_user_summary(
                        self.user_id,
                        self.user_progress['total_score'],
                        self.user_progress.get('current_lesson'),
                    )
                except Exception:
                    pass
    
    def check_puzzle_solution(self, puzzle_id: str, x: int, y: int) -> Tuple[bool, str]:
        """检查棋题答案"""
        puzzle = self.get_puzzle(puzzle_id)
        if not puzzle:
            translator = _resolve_translator(getattr(self, "translator", None))
            return False, translator.get("puzzle_not_found")

        correct, feedback = puzzle.check_move(x, y, translator=self.translator)
        if self.user_db:
            try:
                self.user_db.record_puzzle_attempt(
                    self.user_id,
                    puzzle_id,
                    success=correct,
                    time_spent=0,
                    hints_used=0,
                )
            except Exception:
                pass
        if not correct:
            localized = self.get_puzzle_wrong_move_message(puzzle, x, y)
            if localized:
                feedback = localized
        else:
            if puzzle_id not in self.user_progress['completed_puzzles']:
                self.user_progress['completed_puzzles'].append(puzzle_id)
            if self.user_db:
                try:
                    self.user_db.mark_puzzle_completed(self.user_id, puzzle_id)
                except Exception:
                    pass
        return correct, feedback
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """获取用户统计"""
        if self.user_db:
            try:
                summary = self.user_db.get_user_summary(self.user_id)
                self.user_progress['total_score'] = int(summary.get('total_score') or 0)
                self.user_progress['current_lesson'] = summary.get('current_lesson')
                self.user_progress['completed_lessons'] = self.user_db.list_completed_lessons(
                    self.user_id
                )
                self.user_progress['completed_puzzles'] = self.user_db.list_completed_puzzles(
                    self.user_id
                )
            except Exception:
                pass

        total_lessons = len(self.lessons)
        completed_lessons = len(self.user_progress['completed_lessons'])
        
        return {
            'total_score': self.user_progress['total_score'],
            'lessons_completed': completed_lessons,
            'lessons_total': total_lessons,
            'completion_rate': completed_lessons / total_lessons if total_lessons > 0 else 0,
            'puzzles_solved': len(self.user_progress['completed_puzzles'])
        }


class InteractiveLesson(tk.Frame):
    """互动课程UI组件"""
    
    def __init__(self, parent, teaching_system: TeachingSystem, **kwargs):
        super().__init__(parent, **kwargs)
        self.teaching_system = teaching_system
        self.current_lesson: Optional[Lesson] = None
        self.current_step = 0
        
        self._create_widgets()

    def _t(self, key: str, **kwargs) -> str:
        translator = _resolve_translator(getattr(self.teaching_system, "translator", None))
        return translator.get(key, **kwargs)
    
    def _create_widgets(self):
        """创建控件"""
        # 标题
        self.title_label = ttk.Label(
            self,
            text=self._t("interactive_lesson_title"),
            font=('Arial', 14, 'bold'),
        )
        self.title_label.pack(pady=10)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, length=400)
        self.progress_bar.pack(pady=5)
        
        # 内容区域
        content_frame = ttk.Frame(self)
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # 文本内容
        self.content_text = tk.Text(content_frame, wrap='word', height=15)
        self.content_text.pack(fill='both', expand=True)
        
        # 控制按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        self.prev_button = ttk.Button(
            button_frame,
            text=self._t("step_prev"),
            command=self.prev_step,
        )
        self.prev_button.pack(side='left', padx=5)
        
        self.next_button = ttk.Button(
            button_frame,
            text=self._t("step_next"),
            command=self.next_step,
        )
        self.next_button.pack(side='left', padx=5)
        
        self.check_button = ttk.Button(
            button_frame,
            text=self._t("check_answer"),
            command=self.check_answer,
        )
        self.check_button.pack(side='left', padx=5)
        self.check_button.pack_forget()  # 初始隐藏
    
    def load_lesson(self, lesson_id: str):
        """加载课程"""
        self.current_lesson = self.teaching_system.get_lesson(lesson_id)
        if not self.current_lesson:
            messagebox.showerror(
                self._t("error"),
                self._t("lesson_not_found"),
            )
            return
        
        # 检查先修课程
        if not self.teaching_system.start_lesson(lesson_id):
            messagebox.showwarning(
                self._t("warning"),
                self._t("lesson_prereq_required"),
            )
            return
        
        self.current_step = 0
        self._update_display()
    
    def _update_display(self):
        """更新显示"""
        if not self.current_lesson:
            return
        
        # 更新标题
        self.title_label.config(text=self.current_lesson.title)
        
        # 更新进度
        total_steps = len(self.current_lesson.content)
        if total_steps > 0:
            progress = (self.current_step + 1) / total_steps * 100
            self.progress_var.set(progress)
        
        # 更新内容
        if self.current_step < len(self.current_lesson.content):
            content = self.current_lesson.content[self.current_step]
            self._display_content(content)
        
        # 更新按钮状态
        self.prev_button.config(state='normal' if self.current_step > 0 else 'disabled')
        self.next_button.config(state='normal' if self.current_step < total_steps - 1 else 'disabled')
    
    def _display_content(self, content: LessonContent):
        """显示内容"""
        self.content_text.delete('1.0', 'end')
        
        # 显示标题
        self.content_text.insert('end', f"{content.title}\n\n", 'title')
        
        # 根据类型显示内容
        if content.type == 'text':
            self.content_text.insert('end', content.content.get('text', ''))
            self.check_button.pack_forget()
            
        elif content.type == 'demo':
            self.content_text.insert('end', content.content.get('text', ''))
            self.content_text.insert('end', "\n\n" + self._t("lesson_demo_hint"))
            self.check_button.pack_forget()
            
        elif content.type == 'puzzle':
            puzzle_id = content.content.get('puzzle_id')
            puzzle = self.teaching_system.get_puzzle(puzzle_id)
            if puzzle:
                translator = _resolve_translator(getattr(self.teaching_system, "translator", None))
                objective_label = translator.get('problem_objective')
                hint_label = translator.get('hint')
                objective = self.teaching_system.get_puzzle_text(puzzle, "objective")
                hint = self.teaching_system.get_puzzle_text(puzzle, "hint")
                if objective:
                    self.content_text.insert('end', f"{objective_label}: {objective}\n")
                if hint:
                    self.content_text.insert('end', f"\n{hint_label}: {hint}")
            self.check_button.pack(side='left', padx=5)
            
        elif content.type == 'quiz':
            self.content_text.insert('end', self._t("lesson_quiz_prompt"))
            self.check_button.pack(side='left', padx=5)
        
        # 配置文本标签样式
        self.content_text.tag_config('title', font=('Arial', 12, 'bold'))
    
    def prev_step(self):
        """上一步"""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_display()
    
    def next_step(self):
        """下一步"""
        if self.current_lesson and self.current_step < len(self.current_lesson.content) - 1:
            # 标记当前步骤完成
            self.teaching_system.complete_lesson_step(self.current_lesson.id, self.current_step)
            
            self.current_step += 1
            self._update_display()
        elif self.current_lesson and self.current_step == len(self.current_lesson.content) - 1:
            # 课程完成
            self.teaching_system.complete_lesson(self.current_lesson.id)
            messagebox.showinfo(
                self._t("lesson_completed_title"),
                self._t("lesson_completed_message"),
            )
    
    def check_answer(self):
        """检查答案（用于互动内容）"""
        # 这里需要与棋盘交互
        messagebox.showinfo(
            self._t("hint"),
            self._t("lesson_place_stone_prompt"),
        )


class TacticalPuzzles(tk.Frame):
    """战术训练UI组件"""
    
    def __init__(self, parent, teaching_system: TeachingSystem, **kwargs):
        super().__init__(parent, **kwargs)
        self.teaching_system = teaching_system
        self.current_puzzle: Optional[Puzzle] = None
        
        self._create_widgets()

    def _t(self, key: str, **kwargs) -> str:
        translator = _resolve_translator(getattr(self.teaching_system, "translator", None))
        return translator.get(key, **kwargs)
    
    def _create_widgets(self):
        """创建控件"""
        # 标题
        title_label = ttk.Label(
            self, text=self._t("tactical_training_title"), font=('Arial', 14, 'bold')
        )
        title_label.pack(pady=10)
        
        # 难度选择
        difficulty_frame = ttk.Frame(self)
        difficulty_frame.pack(pady=5)
        
        ttk.Label(difficulty_frame, text=self._t("difficulty_label")).pack(side='left')
        
        self.difficulty_var = tk.IntVar(value=1)
        for i in range(1, 6):
            ttk.Radiobutton(difficulty_frame, text=f"★{'★' * (i-1)}", 
                          variable=self.difficulty_var, value=i).pack(side='left')
        
        # 题目信息
        info_frame = ttk.LabelFrame(self, text=self._t("puzzle_section_title"))
        info_frame.pack(fill='x', padx=10, pady=5)
        
        self.puzzle_title = ttk.Label(info_frame, text="", font=('Arial', 12))
        self.puzzle_title.pack(anchor='w', padx=5, pady=2)
        
        self.objective_label = ttk.Label(info_frame, text="")
        self.objective_label.pack(anchor='w', padx=5, pady=2)
        
        self.hint_label = ttk.Label(info_frame, text="", foreground='blue')
        self.hint_label.pack(anchor='w', padx=5, pady=2)
        
        # 控制按钮
        button_frame = ttk.Frame(self)
        button_frame.pack(pady=10)
        
        ttk.Button(
            button_frame, text=self._t("new_puzzle"), command=self.new_puzzle
        ).pack(side='left', padx=5)
        ttk.Button(
            button_frame, text=self._t("show_hint"), command=self.show_hint
        ).pack(side='left', padx=5)
        ttk.Button(
            button_frame, text=self._t("show_solution"), command=self.show_solution
        ).pack(side='left', padx=5)
        
        # 统计信息
        stats_frame = ttk.LabelFrame(self, text=self._t("tactical_stats_title"))
        stats_frame.pack(fill='x', padx=10, pady=5)
        
        self.stats_label = ttk.Label(
            stats_frame,
            text=self._t("tactical_stats_format", solved=0, accuracy=0),
        )
        self.stats_label.pack(padx=5, pady=5)
    
    def new_puzzle(self):
        """加载新题目"""
        # 根据难度筛选题目
        difficulty = self.difficulty_var.get()
        
        # 找到符合难度的题目
        puzzles = [p for p in self.teaching_system.puzzles.values() 
                  if p.difficulty == difficulty]
        
        if puzzles:
            import random
            self.current_puzzle = random.choice(puzzles)
            self._update_display()
            self.on_puzzle_loaded(self.current_puzzle)
    
    def _update_display(self):
        """更新显示"""
        if not self.current_puzzle:
            return

        translator = _resolve_translator(getattr(self.teaching_system, "translator", None))
        objective_label = translator.get('problem_objective')
        title = self.teaching_system.get_puzzle_text(self.current_puzzle, "title")
        objective = self.teaching_system.get_puzzle_text(self.current_puzzle, "objective")
        self.puzzle_title.config(text=title or self.current_puzzle.title)
        self.objective_label.config(text=f"{objective_label}: {objective}")
        self.hint_label.config(text="")
    
    def show_hint(self):
        """显示提示"""
        if self.current_puzzle:
            hint = self.teaching_system.get_puzzle_text(self.current_puzzle, "hint")
            if hint:
                translator = _resolve_translator(getattr(self.teaching_system, "translator", None))
                hint_label = translator.get('hint')
                self.hint_label.config(text=f"{hint_label}: {hint}")
    
    def show_solution(self):
        """显示答案"""
        if self.current_puzzle:
            translator = _resolve_translator(getattr(self.teaching_system, "translator", None))
            label = translator.get('problem_solution')
            explanation = self.teaching_system.get_puzzle_text(
                self.current_puzzle, "explanation"
            )
            solution_text = f"{label}: " + " → ".join(
                f"({x},{y})" for x, y in self.current_puzzle.solution
            )
            message = solution_text + (f"\n\n{explanation}" if explanation else "")
            messagebox.showinfo(label, message)
    
    def check_move(self, x: int, y: int) -> Tuple[bool, str]:
        """检查着法"""
        if not self.current_puzzle:
            return False, self._t("puzzle_select_prompt")
        
        correct, feedback = self.current_puzzle.check_move(x, y, translator=self.teaching_system.translator)
        if getattr(self.teaching_system, "user_db", None):
            try:
                self.teaching_system.user_db.record_puzzle_attempt(
                    self.teaching_system.user_id,
                    self.current_puzzle.id,
                    success=correct,
                    time_spent=0,
                    hints_used=0,
                )
                if correct:
                    self.teaching_system.user_db.mark_puzzle_completed(
                        self.teaching_system.user_id,
                        self.current_puzzle.id,
                    )
            except Exception:
                pass
        if not correct:
            localized = self.teaching_system.get_puzzle_wrong_move_message(
                self.current_puzzle, x, y
            )
            if localized:
                feedback = localized
        
        # 更新统计
        # TODO: 实现统计更新
        
        return correct, feedback
    
    def on_puzzle_loaded(self, puzzle: Puzzle):
        """题目加载回调（供外部调用）"""
        pass


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ":memory:"
        self.connection = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        self.connection = sqlite3.connect(self.db_path)
        cursor = self.connection.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_progress (
                user_id TEXT,
                lesson_id TEXT,
                step_completed INTEGER,
                completion_date TIMESTAMP,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, lesson_id, step_completed)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS puzzle_attempts (
                user_id TEXT,
                puzzle_id TEXT,
                attempt_date TIMESTAMP,
                success BOOLEAN,
                time_spent INTEGER,
                hints_used INTEGER DEFAULT 0
            )
        """)
        
        self.connection.commit()
    
    def record_lesson_progress(self, user_id: str, lesson_id: str, 
                              step: int, score: int = 0):
        """记录课程进度"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user_progress 
            (user_id, lesson_id, step_completed, completion_date, score)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (user_id, lesson_id, step, score))
        self.connection.commit()
    
    def record_puzzle_attempt(self, user_id: str, puzzle_id: str,
                             success: bool, time_spent: int, hints_used: int = 0):
        """记录棋题尝试"""
        cursor = self.connection.cursor()
        cursor.execute("""
            INSERT INTO puzzle_attempts
            (user_id, puzzle_id, attempt_date, success, time_spent, hints_used)
            VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
        """, (user_id, puzzle_id, success, time_spent, hints_used))
        self.connection.commit()
    
    def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计"""
        cursor = self.connection.cursor()
        
        # 课程完成情况
        cursor.execute("""
            SELECT COUNT(DISTINCT lesson_id), SUM(score)
            FROM user_progress
            WHERE user_id = ?
        """, (user_id,))
        lessons_completed, total_score = cursor.fetchone()
        
        # 棋题统计
        cursor.execute("""
            SELECT 
                COUNT(*) as total_attempts,
                SUM(success) as successes,
                AVG(time_spent) as avg_time,
                SUM(hints_used) as total_hints
            FROM puzzle_attempts
            WHERE user_id = ?
        """, (user_id,))
        
        puzzle_stats = cursor.fetchone()
        
        return {
            'lessons_completed': lessons_completed or 0,
            'total_score': total_score or 0,
            'puzzle_attempts': puzzle_stats[0] or 0,
            'puzzle_successes': puzzle_stats[1] or 0,
            'puzzle_success_rate': (puzzle_stats[1] / puzzle_stats[0] * 100) if puzzle_stats[0] else 0,
            'avg_puzzle_time': puzzle_stats[2] or 0,
            'hints_used': puzzle_stats[3] or 0
        }
    
    def get_lesson_progress(self, user_id: str, lesson_id: str) -> List[int]:
        """获取课程进度"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT step_completed
            FROM user_progress
            WHERE user_id = ? AND lesson_id = ?
            ORDER BY step_completed
        """, (user_id, lesson_id))
        
        return [row[0] for row in cursor.fetchall()]


class RulesTutorial:
    """规则教程"""
    
    def __init__(self, content_db: Optional[ContentDatabase] = None, language: str = 'zh'):
        self.content_db = content_db or get_content_db()
        self.language = language or 'zh'
        self.rules_content = self._load_rules()

    def _load_rules(self) -> Dict[str, str]:
        if self.content_db:
            rules = self.content_db.list_rules(self.language)
            if rules:
                return {rule_id: data.get('text', '') for rule_id, data in rules.items()}

        return {
            'chinese': self._get_chinese_rules(),
            'japanese': self._get_japanese_rules(),
            'aga': self._get_aga_rules()
        }
    
    def _get_chinese_rules(self) -> str:
        """中国规则说明"""
        return """中国规则（数子法）

基本原则：
1. 黑方先行，轮流落子
2. 提取对方无气之子
3. 禁止全局同形再现
4. 虚手表示放弃一手

计分方法：
- 数子法：计算己方活子数 + 围住的空点
- 黑方贴还3.75子（相当于7.5目）
- 子空皆地，总和多者胜

特点：
- 简单直观
- 不需要保留死子
- 收官阶段可以随意填子"""
    
    def _get_japanese_rules(self) -> str:
        """日本规则说明"""
        return """日本规则（数目法）

基本原则：
1. 黑方先行，轮流落子
2. 提取对方无气之子
3. 禁止立即回提（劫）
4. 连续两次虚手结束对局

计分方法：
- 数目法：计算围住的空点 + 提子 + 死子
- 白方贴6.5目
- 只数空，不数子

特点：
- 需要判定死活
- 收官需要技巧
- 有特殊规则（如双活无目）"""
    
    def _get_aga_rules(self) -> str:
        """AGA规则说明"""
        return """AGA规则（美国围棋协会规则）

基本原则：
- 综合中日规则特点
- 黑方先行，白方贴7.5目
- 使用区域计分法

计分方法：
- 类似中国规则的数子法
- 但白方每虚手要交还一个子给黑方
- 结果与日本规则基本一致

特点：
- 规则清晰明确
- 适合比赛使用
- 减少争议"""
    
    def get_rules_text(self, rule_type: str) -> str:
        """获取规则文本"""
        return self.rules_content.get(rule_type, "未知规则类型")


class BasicTutorial:
    """基础教程"""
    
    def __init__(self, content_db: Optional[ContentDatabase] = None, language: str = 'zh'):
        self.content_db = content_db or get_content_db()
        self.language = language or 'zh'
        self.tutorials = self._load_tutorials()

    def _load_tutorials(self) -> Dict[str, str]:
        if self.content_db:
            tutorials = {}
            for topic in ('opening', 'middle_game', 'endgame', 'life_death', 'ko'):
                text = self.content_db.get_tutorial_text(topic, self.language)
                if text:
                    tutorials[topic] = text
            if tutorials:
                return tutorials

        return {
            'opening': "布局要点...",
            'middle_game': "中盘战斗...",
            'endgame': "收官技巧...",
            'life_death': "死活要点...",
            'ko': "劫的处理..."
        }
    
    def get_tutorial(self, topic: str) -> str:
        """获取教程内容"""
        return self.tutorials.get(topic, "教程内容暂未完成")
