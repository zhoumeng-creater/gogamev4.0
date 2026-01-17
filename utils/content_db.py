import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _default_user_data_dir() -> Path:
    return Path.home() / ".go_master"


def _ensure_dir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


class ContentDatabase:
    """Content database for lessons, rules, joseki, patterns, help resources, etc."""

    def __init__(self, db_path: Optional[str] = None, pack_dir: Optional[str] = None):
        self.db_path = str(db_path) if db_path else str(_default_user_data_dir() / "content.db")
        self.pack_dir = Path(pack_dir) if pack_dir else self._default_pack_dir()
        _ensure_dir(Path(self.db_path).parent)
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._init_database()
        self._sync_default_pack()

    def close(self) -> None:
        try:
            self.connection.close()
        except Exception:
            pass

    def _default_pack_dir(self) -> Path:
        try:
            base = Path(sys._MEIPASS)
        except Exception:
            base = Path(__file__).resolve().parents[1]
        return base / "assets" / "content_packs" / "default"

    def _init_database(self) -> None:
        cursor = self.connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_packs (
                pack_id TEXT PRIMARY KEY,
                name TEXT,
                version TEXT,
                languages TEXT,
                description TEXT,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rules_texts (
                pack_id TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                language TEXT NOT NULL,
                text TEXT,
                highlights TEXT,
                PRIMARY KEY (pack_id, rule_id, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                pack_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                type TEXT,
                difficulty INTEGER,
                estimated_time INTEGER,
                prerequisites TEXT,
                sort_order INTEGER,
                PRIMARY KEY (pack_id, lesson_id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lesson_texts (
                pack_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                language TEXT NOT NULL,
                title TEXT,
                description TEXT,
                objectives TEXT,
                PRIMARY KEY (pack_id, lesson_id, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lesson_steps (
                pack_id TEXT NOT NULL,
                lesson_id TEXT NOT NULL,
                step INTEGER NOT NULL,
                language TEXT NOT NULL,
                type TEXT,
                title TEXT,
                content TEXT,
                PRIMARY KEY (pack_id, lesson_id, step, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tutorials (
                pack_id TEXT NOT NULL,
                topic_id TEXT NOT NULL,
                language TEXT NOT NULL,
                text TEXT,
                PRIMARY KEY (pack_id, topic_id, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS joseki_sequences (
                pack_id TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT,
                difficulty INTEGER,
                popularity INTEGER,
                key TEXT,
                tags TEXT,
                data TEXT,
                PRIMARY KEY (pack_id, name)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patterns (
                pack_id TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT,
                data TEXT,
                PRIMARY KEY (pack_id, name)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS resources (
                pack_id TEXT NOT NULL,
                category TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                language TEXT NOT NULL,
                label TEXT,
                url TEXT,
                sort_order INTEGER,
                PRIMARY KEY (pack_id, category, resource_id, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements (
                pack_id TEXT NOT NULL,
                key TEXT NOT NULL,
                language TEXT NOT NULL,
                label TEXT,
                PRIMARY KEY (pack_id, key, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comment_evaluations (
                pack_id TEXT NOT NULL,
                key TEXT NOT NULL,
                symbol TEXT,
                language TEXT NOT NULL,
                label TEXT,
                PRIMARY KEY (pack_id, key, language)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS translations (
                pack_id TEXT NOT NULL,
                language TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                PRIMARY KEY (pack_id, language, key)
            )
            """
        )
        self.connection.commit()

    def _table_columns(self, table: str) -> List[str]:
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]

    def _version_tuple(self, version: str) -> Tuple[int, ...]:
        parts: List[int] = []
        for raw in str(version or "").split("."):
            digits = "".join(ch for ch in raw if ch.isdigit())
            parts.append(int(digits) if digits else 0)
        return tuple(parts or [0])

    def _is_version_newer(self, new_version: str, old_version: str) -> bool:
        return self._version_tuple(new_version) > self._version_tuple(old_version)

    def read_pack_meta(self, pack_dir: Path) -> Optional[Dict[str, Any]]:
        try:
            meta_text = (pack_dir / "pack.json").read_text(encoding="utf-8")
            meta = json.loads(meta_text)
        except Exception:
            return None
        if not isinstance(meta, dict):
            return None
        return meta

    def get_pack_info(self, pack_id: str) -> Optional[Dict[str, Any]]:
        if not pack_id:
            return None
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT pack_id, name, version, languages, description FROM content_packs WHERE pack_id = ?",
            (pack_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        languages: List[str] = []
        if row[3]:
            try:
                languages = json.loads(row[3])
            except Exception:
                languages = []
        return {
            "id": str(row[0]),
            "name": str(row[1] or ""),
            "version": str(row[2] or ""),
            "languages": languages,
            "description": str(row[4] or ""),
        }

    def set_pack_info(self, meta: Dict[str, Any]) -> None:
        if not meta:
            return
        pack_id = str(meta.get("id") or "").strip()
        if not pack_id:
            return
        languages = meta.get("languages") or []
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO content_packs (pack_id, name, version, languages, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                pack_id,
                str(meta.get("name") or ""),
                str(meta.get("version") or ""),
                json.dumps(languages, ensure_ascii=False),
                str(meta.get("description") or ""),
            ),
        )
        self.connection.commit()

    def _sync_default_pack(self) -> None:
        pack_dir = self.pack_dir
        if not pack_dir.exists():
            return
        meta = self.read_pack_meta(pack_dir)
        if not meta:
            return
        pack_id = str(meta.get("id") or "default").strip() or "default"
        installed = self.get_pack_info(pack_id)
        should_install = False
        if installed is None:
            should_install = True
        elif meta.get("version"):
            if self._is_version_newer(str(meta.get("version")), str(installed.get("version") or "")):
                should_install = True
        if should_install:
            self.import_pack(str(pack_dir), strategy="overwrite")

    def _read_json(self, path: Path) -> Any:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    def _clear_pack_rows(self, pack_id: str) -> None:
        cursor = self.connection.cursor()
        tables = [
            "rules_texts",
            "lessons",
            "lesson_texts",
            "lesson_steps",
            "tutorials",
            "joseki_sequences",
            "patterns",
            "resources",
            "achievements",
            "comment_evaluations",
            "translations",
        ]
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE pack_id = ?", (pack_id,))
        self.connection.commit()

    def import_pack(self, pack_dir: str, strategy: str = "overwrite") -> Tuple[int, List[str]]:
        errors: List[str] = []
        base_dir = Path(pack_dir)
        meta = self.read_pack_meta(base_dir)
        if not meta:
            return 0, ["pack.json missing or invalid"]
        pack_id = str(meta.get("id") or "default").strip() or "default"
        if strategy == "overwrite":
            self._clear_pack_rows(pack_id)

        cursor = self.connection.cursor()
        inserted = 0

        rules_data = self._read_json(base_dir / "rules.json")
        for item in (rules_data or {}).get("rules", rules_data or []) or []:
            if not isinstance(item, dict):
                continue
            rule_id = str(item.get("id") or "").strip()
            language = str(item.get("language") or "zh").strip() or "zh"
            if not rule_id:
                continue
            text = str(item.get("text") or "")
            highlights = json.dumps(item.get("highlights") or [], ensure_ascii=False)
            cursor.execute(
                """
                INSERT OR REPLACE INTO rules_texts (pack_id, rule_id, language, text, highlights)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pack_id, rule_id, language, text, highlights),
            )
            inserted += 1

        lessons_data = self._read_json(base_dir / "lessons.json")
        for item in (lessons_data or {}).get("lessons", lessons_data or []) or []:
            if not isinstance(item, dict):
                continue
            lesson_id = str(item.get("id") or "").strip()
            if not lesson_id:
                continue
            prerequisites = item.get("prerequisites") or []
            cursor.execute(
                """
                INSERT OR REPLACE INTO lessons
                (pack_id, lesson_id, type, difficulty, estimated_time, prerequisites, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pack_id,
                    lesson_id,
                    str(item.get("type") or ""),
                    int(item.get("difficulty") or 1),
                    int(item.get("estimated_time") or 0),
                    json.dumps(prerequisites, ensure_ascii=False),
                    int(item.get("sort_order") or 0),
                ),
            )
            language = str(item.get("language") or "zh").strip() or "zh"
            cursor.execute(
                """
                INSERT OR REPLACE INTO lesson_texts
                (pack_id, lesson_id, language, title, description, objectives)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    pack_id,
                    lesson_id,
                    language,
                    str(item.get("title") or ""),
                    str(item.get("description") or ""),
                    json.dumps(item.get("objectives") or [], ensure_ascii=False),
                ),
            )
            inserted += 1

        steps_data = self._read_json(base_dir / "lesson_steps.json")
        for item in (steps_data or {}).get("steps", steps_data or []) or []:
            if not isinstance(item, dict):
                continue
            lesson_id = str(item.get("lesson_id") or "").strip()
            if not lesson_id:
                continue
            step = int(item.get("step") or 0)
            language = str(item.get("language") or "zh").strip() or "zh"
            cursor.execute(
                """
                INSERT OR REPLACE INTO lesson_steps
                (pack_id, lesson_id, step, language, type, title, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pack_id,
                    lesson_id,
                    step,
                    language,
                    str(item.get("type") or ""),
                    str(item.get("title") or ""),
                    json.dumps(item.get("content") or {}, ensure_ascii=False),
                ),
            )
            inserted += 1

        tutorials_data = self._read_json(base_dir / "tutorials.json")
        for item in (tutorials_data or {}).get("tutorials", tutorials_data or []) or []:
            if not isinstance(item, dict):
                continue
            topic_id = str(item.get("topic") or "").strip()
            if not topic_id:
                continue
            language = str(item.get("language") or "zh").strip() or "zh"
            cursor.execute(
                """
                INSERT OR REPLACE INTO tutorials (pack_id, topic_id, language, text)
                VALUES (?, ?, ?, ?)
                """,
                (pack_id, topic_id, language, str(item.get("text") or "")),
            )
            inserted += 1

        joseki_data = self._read_json(base_dir / "joseki_sequences.json")
        for item in (joseki_data or {}).get("joseki_sequences", joseki_data or []) or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            cursor.execute(
                """
                INSERT OR REPLACE INTO joseki_sequences
                (pack_id, name, type, difficulty, popularity, key, tags, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pack_id,
                    name,
                    str(item.get("type") or ""),
                    int(item.get("difficulty") or 0),
                    int(item.get("popularity") or 0),
                    str(item.get("key") or ""),
                    json.dumps(item.get("tags") or [], ensure_ascii=False),
                    json.dumps(item, ensure_ascii=False),
                ),
            )
            inserted += 1

        patterns_data = self._read_json(base_dir / "patterns.json")
        for item in (patterns_data or {}).get("patterns", patterns_data or []) or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            cursor.execute(
                """
                INSERT OR REPLACE INTO patterns (pack_id, name, category, data)
                VALUES (?, ?, ?, ?)
                """,
                (
                    pack_id,
                    name,
                    str(item.get("category") or ""),
                    json.dumps(item, ensure_ascii=False),
                ),
            )
            inserted += 1

        resources_data = self._read_json(base_dir / "resources.json")
        for item in (resources_data or {}).get("resources", resources_data or []) or []:
            if not isinstance(item, dict):
                continue
            category = str(item.get("category") or "").strip()
            resource_id = str(item.get("id") or "").strip()
            if not category or not resource_id:
                continue
            language = str(item.get("language") or "zh").strip() or "zh"
            cursor.execute(
                """
                INSERT OR REPLACE INTO resources
                (pack_id, category, resource_id, language, label, url, sort_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pack_id,
                    category,
                    resource_id,
                    language,
                    str(item.get("label") or ""),
                    str(item.get("url") or ""),
                    int(item.get("sort_order") or 0),
                ),
            )
            inserted += 1

        achievements_data = self._read_json(base_dir / "achievements.json")
        for item in (achievements_data or {}).get("achievements", achievements_data or []) or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if not key:
                continue
            language = str(item.get("language") or "zh").strip() or "zh"
            cursor.execute(
                """
                INSERT OR REPLACE INTO achievements (pack_id, key, language, label)
                VALUES (?, ?, ?, ?)
                """,
                (
                    pack_id,
                    key,
                    language,
                    str(item.get("label") or ""),
                ),
            )
            inserted += 1

        evals_data = self._read_json(base_dir / "comment_evaluations.json")
        for item in (evals_data or {}).get("evaluations", evals_data or []) or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            if not key:
                continue
            language = str(item.get("language") or "zh").strip() or "zh"
            cursor.execute(
                """
                INSERT OR REPLACE INTO comment_evaluations
                (pack_id, key, symbol, language, label)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    pack_id,
                    key,
                    str(item.get("symbol") or ""),
                    language,
                    str(item.get("label") or ""),
                ),
            )
            inserted += 1

        translations_data = self._read_json(base_dir / "translations.json")
        translations_payload = None
        if isinstance(translations_data, dict):
            translations_payload = translations_data.get("translations") or translations_data
        if isinstance(translations_payload, dict):
            for language, mapping in translations_payload.items():
                if not isinstance(mapping, dict):
                    continue
                for key, value in mapping.items():
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO translations (pack_id, language, key, value)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            pack_id,
                            str(language),
                            str(key),
                            str(value),
                        ),
                    )
                    inserted += 1

        self.connection.commit()
        self.set_pack_info(meta)
        return inserted, errors

    def _select_pack_id(self) -> str:
        cursor = self.connection.cursor()
        cursor.execute("SELECT pack_id FROM content_packs ORDER BY installed_at DESC LIMIT 1")
        row = cursor.fetchone()
        return str(row[0]) if row else "default"

    def list_rules(self, language: str = "zh") -> Dict[str, Dict[str, Any]]:
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT rule_id, language, text, highlights
            FROM rules_texts
            WHERE pack_id = ?
            """,
            (pack_id,),
        )
        rows = cursor.fetchall()
        result: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            rule_id = str(row[0])
            lang = str(row[1])
            if lang != language:
                continue
            highlights = []
            if row[3]:
                try:
                    highlights = json.loads(row[3])
                except Exception:
                    highlights = []
            result[rule_id] = {
                "text": str(row[2] or ""),
                "highlights": highlights,
            }
        return result

    def get_rule_text(self, rule_id: str, language: str = "zh") -> Optional[Dict[str, Any]]:
        if not rule_id:
            return None
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT text, highlights
            FROM rules_texts
            WHERE pack_id = ? AND rule_id = ? AND language = ?
            """,
            (pack_id, rule_id, language),
        )
        row = cursor.fetchone()
        if not row:
            return None
        highlights = []
        if row[1]:
            try:
                highlights = json.loads(row[1])
            except Exception:
                highlights = []
        return {"text": str(row[0] or ""), "highlights": highlights}

    def list_lessons(self, language: str = "zh") -> List[Dict[str, Any]]:
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT l.lesson_id, l.type, l.difficulty, l.estimated_time, l.prerequisites, l.sort_order,
                   t.title, t.description, t.objectives
            FROM lessons l
            LEFT JOIN lesson_texts t
              ON t.lesson_id = l.lesson_id AND t.pack_id = l.pack_id AND t.language = ?
            WHERE l.pack_id = ?
            ORDER BY l.sort_order, l.lesson_id
            """,
            (language, pack_id),
        )
        lessons: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            prerequisites = []
            objectives = []
            if row[4]:
                try:
                    prerequisites = json.loads(row[4])
                except Exception:
                    prerequisites = []
            if row[8]:
                try:
                    objectives = json.loads(row[8])
                except Exception:
                    objectives = []
            lessons.append(
                {
                    "id": str(row[0]),
                    "type": str(row[1] or ""),
                    "difficulty": int(row[2] or 1),
                    "estimated_time": int(row[3] or 0),
                    "prerequisites": prerequisites,
                    "title": str(row[6] or ""),
                    "description": str(row[7] or ""),
                    "objectives": objectives,
                }
            )
        return lessons

    def list_lesson_steps(self, lesson_id: str, language: str = "zh") -> List[Dict[str, Any]]:
        if not lesson_id:
            return []
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT step, type, title, content
            FROM lesson_steps
            WHERE pack_id = ? AND lesson_id = ? AND language = ?
            ORDER BY step
            """,
            (pack_id, lesson_id, language),
        )
        steps: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            content = {}
            if row[3]:
                try:
                    content = json.loads(row[3])
                except Exception:
                    content = {}
            steps.append(
                {
                    "step": int(row[0] or 0),
                    "type": str(row[1] or ""),
                    "title": str(row[2] or ""),
                    "content": content,
                }
            )
        return steps

    def get_tutorial_text(self, topic_id: str, language: str = "zh") -> Optional[str]:
        if not topic_id:
            return None
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT text FROM tutorials
            WHERE pack_id = ? AND topic_id = ? AND language = ?
            """,
            (pack_id, topic_id, language),
        )
        row = cursor.fetchone()
        return str(row[0] or "") if row else None

    def list_patterns(self) -> List[Dict[str, Any]]:
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT data FROM patterns WHERE pack_id = ?",
            (pack_id,),
        )
        patterns: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[0]) if row[0] else None
            except Exception:
                data = None
            if isinstance(data, dict):
                patterns.append(data)
        return patterns

    def list_joseki_sequences(self) -> List[Dict[str, Any]]:
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT data FROM joseki_sequences WHERE pack_id = ?",
            (pack_id,),
        )
        sequences: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[0]) if row[0] else None
            except Exception:
                data = None
            if isinstance(data, dict):
                sequences.append(data)
        return sequences

    def list_resources(self, category: str, language: str = "zh") -> List[Dict[str, Any]]:
        if not category:
            return []
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT resource_id, label, url, sort_order
            FROM resources
            WHERE pack_id = ? AND category = ? AND language = ?
            ORDER BY sort_order, resource_id
            """,
            (pack_id, category, language),
        )
        resources: List[Dict[str, Any]] = []
        for row in cursor.fetchall():
            resources.append(
                {
                    "id": str(row[0]),
                    "label": str(row[1] or ""),
                    "url": str(row[2] or ""),
                    "sort_order": int(row[3] or 0),
                }
            )
        return resources

    def list_achievements(self, language: str = "zh") -> Dict[str, str]:
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT key, label
            FROM achievements
            WHERE pack_id = ? AND language = ?
            """,
            (pack_id, language),
        )
        result: Dict[str, str] = {}
        for row in cursor.fetchall():
            result[str(row[0])] = str(row[1] or "")
        return result

    def list_comment_evaluations(self, language: str = "zh") -> Dict[str, Dict[str, str]]:
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT key, symbol, label
            FROM comment_evaluations
            WHERE pack_id = ? AND language = ?
            """,
            (pack_id, language),
        )
        result: Dict[str, Dict[str, str]] = {}
        for row in cursor.fetchall():
            result[str(row[0])] = {
                "symbol": str(row[1] or ""),
                "label": str(row[2] or ""),
            }
        return result

    def list_translations(self) -> Dict[str, Dict[str, str]]:
        pack_id = self._select_pack_id()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT language, key, value FROM translations WHERE pack_id = ?",
            (pack_id,),
        )
        translations: Dict[str, Dict[str, str]] = {}
        for row in cursor.fetchall():
            language = str(row[0])
            translations.setdefault(language, {})[str(row[1])] = str(row[2])
        return translations


_global_content_db: Optional[ContentDatabase] = None


def get_content_db() -> ContentDatabase:
    global _global_content_db
    if _global_content_db is None:
        _global_content_db = ContentDatabase()
    return _global_content_db

