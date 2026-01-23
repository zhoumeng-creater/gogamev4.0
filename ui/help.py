"""
帮助与学习相关的对话框
包含规则说明和内置教程浏览
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from typing import Optional, Dict, List

from .dialogs import BaseDialog
from .translator import Translator
from .themes import Theme, theme_font
from utils.content_db import get_content_db
from features.teaching import (
    RulesTutorial,
    TeachingSystem,
    InteractiveLesson,
    LessonType,
    Lesson,
)


class RulesHelpDialog(BaseDialog):
    """规则说明对话框"""

    def __init__(
        self,
        parent,
        translator: Optional[Translator] = None,
        theme: Optional[Theme] = None,
        rules_tutorial: Optional[RulesTutorial] = None,
        **kwargs,
    ):
        self.translator = translator or Translator()
        self.theme = theme or Theme(name="default")
        self.content_db = get_content_db()
        self.rules_tutorial = rules_tutorial or RulesTutorial(
            content_db=self.content_db,
            language=getattr(self.translator, "language", "zh"),
        )
        self._rule_options = [
            ("chinese", self.translator.get("chinese_rules")),
            ("japanese", self.translator.get("japanese_rules")),
            ("aga", self.translator.get("aga_rules")),
        ]
        self._resources = self._load_resources("rules_help")
        super().__init__(
            parent,
            title=self.translator.get("rules_help"),
            translator=self.translator,
            theme=self.theme,
            modal=kwargs.get("modal", True),
            auto_wait=False,
        )
        # BaseDialog 会在 __init__ 结束时居中，此处再调整尺寸并手动等待
        self.geometry("760x580")
        self._center_window()
        if self._modal:
            self.wait_window()

    def _create_widgets(self):
        """创建规则说明内容"""
        main_frame = ttk.Frame(self, padding=12, style="Dialog.TFrame")
        main_frame.pack(fill="both", expand=True)

        intro = ttk.Label(
            main_frame,
            text=self.translator.get(
                "rules_help_intro",
            ),
            wraplength=720,
            justify="left",
            style="Dialog.TLabel",
        )
        intro.pack(fill="x", pady=(0, 10))

        selection_frame = ttk.Frame(main_frame, style="Dialog.TFrame")
        selection_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(
            selection_frame,
            text=self.translator.get("rules_type"),
            style="Dialog.TLabel",
        ).pack(side="left")

        self.rule_var = tk.StringVar(value=self._rule_options[0][1])
        rule_selector = ttk.Combobox(
            selection_frame,
            state="readonly",
            textvariable=self.rule_var,
            values=[label for _, label in self._rule_options],
            width=25,
        )
        rule_selector.pack(side="left", padx=(8, 0))
        rule_selector.current(0)
        rule_selector.bind("<<ComboboxSelected>>", self._on_rule_change)

        content_frame = ttk.Frame(main_frame, style="Dialog.TFrame")
        content_frame.pack(fill="both", expand=True)

        self.content_text = tk.Text(
            content_frame,
            wrap="word",
            height=20,
            bg=self.theme.ui_panel_background,
            fg=self.theme.ui_text_primary,
            relief="solid",
            borderwidth=1,
        )
        self.content_text.pack(fill="both", expand=True, pady=(4, 6))
        self.content_text.configure(state="disabled")

        resources = ttk.LabelFrame(
            main_frame,
            text=self.translator.get("resources"),
            padding=8,
            style="Dialog.TLabelframe",
        )
        resources.pack(fill="x", pady=(4, 0))

        ttk.Label(
            resources,
            text=self.translator.get("rules_help_resources_hint"),
            style="Dialog.TLabel",
            wraplength=720,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        for resource in self._resources:
            ttk.Button(
                resources,
                text=resource["label"],
                command=lambda url=resource["url"]: self._open_link(url),
            ).pack(anchor="w", pady=2)

        # 初始化显示
        self._update_rules_text(self._rule_options[0][0])

    def _on_rule_change(self, _event=None):
        """规则选择变更"""
        rule_key = next(
            (key for key, label in self._rule_options if label == self.rule_var.get()),
            self._rule_options[0][0],
        )
        self._update_rules_text(rule_key)

    def _update_rules_text(self, rule_key: str):
        """更新规则文本显示"""
        content = self.rules_tutorial.get_rules_text(rule_key)
        highlights = self._build_highlights(rule_key)
        self.content_text.configure(state="normal")
        self.content_text.delete("1.0", "end")
        self.content_text.insert("end", content.strip())
        if highlights:
            title = self.translator.get("rules_help_highlights_title")
            self.content_text.insert(
                "end",
                f"\n\n{title}:\n- " + "\n- ".join(highlights),
            )
        self.content_text.configure(state="disabled")

    def _build_highlights(self, rule_key: str) -> List[str]:
        """不同规则的简要提示"""
        language = getattr(self.translator, "language", "zh")
        try:
            rule_data = self.content_db.get_rule_text(rule_key, language)
            if rule_data and rule_data.get("highlights"):
                return list(rule_data.get("highlights") or [])
        except Exception:
            pass

        hints: Dict[str, List[str]] = {
            "chinese": [
                self.translator.get("rules_highlight_chinese_1"),
                self.translator.get("rules_highlight_chinese_2"),
                self.translator.get("rules_highlight_chinese_3"),
            ],
            "japanese": [
                self.translator.get("rules_highlight_japanese_1"),
                self.translator.get("rules_highlight_japanese_2"),
                self.translator.get("rules_highlight_japanese_3"),
            ],
            "aga": [
                self.translator.get("rules_highlight_aga_1"),
                self.translator.get("rules_highlight_aga_2"),
                self.translator.get("rules_highlight_aga_3"),
            ],
        }
        return [hint for hint in hints.get(rule_key, []) if hint]

    def _load_resources(self, category: str) -> List[Dict[str, str]]:
        language = getattr(self.translator, "language", "zh")
        try:
            resources = self.content_db.list_resources(category, language)
        except Exception:
            resources = []
        return resources or []

    def _open_link(self, url: str):
        """在浏览器打开资源链接"""
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:  # pragma: no cover - UI 提示
            messagebox.showerror(
                self.translator.get("error"),
                self.translator.get("open_link_failed", error=exc),
                parent=self,
            )


class TutorialDialog(BaseDialog):
    """教程对话框"""

    def __init__(
        self,
        parent,
        teaching_system: Optional[TeachingSystem] = None,
        translator: Optional[Translator] = None,
        theme: Optional[Theme] = None,
        **kwargs,
    ):
        self.translator = translator or Translator()
        self.theme = theme or Theme(name="default")
        self.content_db = get_content_db()
        self.teaching_system = teaching_system or TeachingSystem(
            self.translator,
            content_db=self.content_db,
        )
        self._type_labels: Dict[LessonType, str] = {
            LessonType.RULES: self.translator.get("lesson_type_rules"),
            LessonType.BASICS: self.translator.get("lesson_type_basics"),
            LessonType.TACTICS: self.translator.get("lesson_type_tactics"),
            LessonType.STRATEGY: self.translator.get("lesson_type_strategy"),
            LessonType.LIFE_DEATH: self.translator.get("lesson_type_life_death"),
            LessonType.TESUJI: self.translator.get("lesson_type_tesuji"),
            LessonType.ENDGAME: self.translator.get("lesson_type_endgame"),
        }
        self._resources = self._load_resources("tutorial")
        super().__init__(
            parent,
            title=self.translator.get("tutorial"),
            translator=self.translator,
            theme=self.theme,
            modal=kwargs.get("modal", True),
            auto_wait=False,
        )
        self.geometry("960x640")
        self._center_window()
        if self._modal:
            self.wait_window()

    def _create_widgets(self):
        """创建教程浏览界面"""
        main_frame = ttk.Frame(self, padding=12, style="Dialog.TFrame")
        main_frame.pack(fill="both", expand=True)

        intro = ttk.Label(
            main_frame,
            text=self.translator.get("tutorial_intro"),
            wraplength=920,
            justify="left",
            style="Dialog.TLabel",
        )
        intro.pack(fill="x", pady=(0, 10))

        body = ttk.Frame(main_frame, style="Dialog.TFrame")
        body.pack(fill="both", expand=True)

        # 左侧课程树
        left = ttk.Frame(body, width=240, style="Dialog.TFrame")
        left.pack(side="left", fill="y", padx=(0, 10))

        tree_frame = ttk.LabelFrame(
            left,
            text=self.translator.get("tutorial_tree_title"),
            padding=6,
            style="Dialog.TLabelframe",
        )
        tree_frame.pack(fill="both", expand=True)

        self.lesson_tree = ttk.Treeview(tree_frame, show="tree")
        self.lesson_tree.pack(fill="both", expand=True)
        self.lesson_tree.bind("<<TreeviewSelect>>", self._on_lesson_selected)

        self.stats_label = ttk.Label(
            left, text="", style="Dialog.TLabel", wraplength=220, justify="left"
        )
        self.stats_label.pack(fill="x", pady=(8, 0))

        # 右侧内容
        right = ttk.Frame(body, style="Dialog.TFrame")
        right.pack(side="left", fill="both", expand=True)

        overview = ttk.LabelFrame(
            right,
            text=self.translator.get("tutorial_overview_title"),
            padding=10,
            style="Dialog.TLabelframe",
        )
        overview.pack(fill="x")

        self.lesson_title = ttk.Label(
            overview,
            text="",
            font=theme_font(self.theme, self.theme.font_size_large, weight="bold"),
            style="Dialog.TLabel",
        )
        self.lesson_title.pack(anchor="w")

        self.lesson_meta = ttk.Label(
            overview, text="", style="Dialog.TLabel", wraplength=640, justify="left"
        )
        self.lesson_meta.pack(anchor="w", pady=2)

        self.lesson_desc = ttk.Label(
            overview, text="", style="Dialog.TLabel", wraplength=640, justify="left"
        )
        self.lesson_desc.pack(anchor="w", pady=(4, 0))

        self.objectives_label = ttk.Label(
            overview,
            text="",
            style="Dialog.TLabel",
            wraplength=640,
            justify="left",
        )
        self.objectives_label.pack(anchor="w", pady=(4, 0))

        lesson_frame = ttk.LabelFrame(
            right,
            text=self.translator.get("tutorial"),
            padding=6,
            style="Dialog.TLabelframe",
        )
        lesson_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.lesson_view = InteractiveLesson(lesson_frame, self.teaching_system)
        self.lesson_view.pack(fill="both", expand=True)

        resource_frame = ttk.LabelFrame(
            right,
            text=self.translator.get("tutorial_resources_title"),
            padding=8,
            style="Dialog.TLabelframe",
        )
        resource_frame.pack(fill="x", pady=(8, 0))

        ttk.Label(
            resource_frame,
            text=self.translator.get("tutorial_resources_hint"),
            style="Dialog.TLabel",
            wraplength=640,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        for res in self._resources:
            ttk.Button(
                resource_frame,
                text=res["label"],
                command=lambda url=res["url"]: self._open_link(url),
            ).pack(anchor="w", pady=2)

    def _load_resources(self, category: str) -> List[Dict[str, str]]:
        language = getattr(self.translator, "language", "zh")
        try:
            resources = self.content_db.list_resources(category, language)
        except Exception:
            resources = []
        return resources or []

        self._populate_tree()
        self._update_stats()

    def _populate_tree(self):
        """填充课程树"""
        type_nodes: Dict[LessonType, str] = {}
        for lesson in sorted(
            self.teaching_system.lessons.values(), key=lambda l: l.difficulty.value
        ):
            parent = type_nodes.get(lesson.type)
            if not parent:
                parent = self.lesson_tree.insert(
                    "",
                    "end",
                    text=self._type_labels.get(lesson.type, lesson.type.value),
                    open=True,
                )
                type_nodes[lesson.type] = parent
            self.lesson_tree.insert(parent, "end", iid=lesson.id, text=lesson.title)

        # 默认选择基础规则课程
        if "rules_basic" in self.teaching_system.lessons:
            self.lesson_tree.selection_set("rules_basic")
            self._display_lesson(self.teaching_system.lessons["rules_basic"])

    def _on_lesson_selected(self, _event=None):
        """选择课程"""
        selection = self.lesson_tree.selection()
        if not selection:
            return
        lesson_id = selection[0]
        lesson = self.teaching_system.get_lesson(lesson_id)
        if lesson:
            self._display_lesson(lesson)

    def _display_lesson(self, lesson: Lesson):
        """展示课程详情并加载内容"""
        prereq_titles = self._format_prerequisites(lesson.prerequisites)
        prereq_label = self.translator.get("lesson_prerequisites")
        prereq_text = "、".join(prereq_titles) if prereq_titles else self.translator.get("none")
        prereq = f"{prereq_label}{prereq_text}"
        meta = self.translator.get(
            "lesson_meta_format",
            lesson_type=self._type_labels.get(lesson.type, lesson.type.value),
            minutes=lesson.estimated_time,
            prerequisites=prereq,
        )
        self.lesson_title.config(text=lesson.title)
        self.lesson_meta.config(text=meta)
        self.lesson_desc.config(text=lesson.description)
        if lesson.objectives:
            obj_text = (
                self.translator.get("lesson_objectives_title")
                + ":\n- "
                + "\n- ".join(lesson.objectives)
            )
        else:
            obj_text = ""
        self.objectives_label.config(text=obj_text)

        # 加载互动内容（允许预览，先修未完成时仍提示）
        try:
            self.lesson_view.load_lesson(lesson.id)
        except Exception:
            messagebox.showwarning(
                self.translator.get("warning"),
                self.translator.get("lesson_load_failed"),
                parent=self,
            )
        self._update_stats()

    def _format_prerequisites(self, prereqs: List[str]) -> List[str]:
        """将先修课程ID转换为标题"""
        titles: List[str] = []
        for pid in prereqs:
            lesson = self.teaching_system.get_lesson(pid)
            titles.append(lesson.title if lesson else pid)
        return titles

    def _update_stats(self):
        """更新统计信息"""
        stats = self.teaching_system.get_user_statistics()
        self.stats_label.config(
            text=self.translator.get(
                "tutorial_stats_format",
                completed=stats["lessons_completed"],
                total=stats["lessons_total"],
                puzzles=stats["puzzles_solved"],
                score=stats["total_score"],
            )
        )

    def _open_link(self, url: str):
        """打开外部教程链接"""
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:  # pragma: no cover - UI 提示
            messagebox.showerror(
                self.translator.get("error"),
                self.translator.get("open_link_failed", error=exc),
                parent=self,
            )
