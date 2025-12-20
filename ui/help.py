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
from .themes import Theme
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
        self.rules_tutorial = rules_tutorial or RulesTutorial()
        self._rule_options = [
            ("chinese", self.translator.get("chinese_rules", "中国规则")),
            ("japanese", self.translator.get("japanese_rules", "日本规则")),
            ("aga", self.translator.get("aga_rules", "AGA规则")),
        ]
        self._resources = [
            {
                "label": "中国围棋规则（2018版）",
                "url": "https://www.qipai.org.cn/web/article/word/id/50301",
            },
            {
                "label": "日本棋院规则（英文）",
                "url": "https://www.nihonkiin.or.jp/match/ki_rules/download.html",
            },
            {
                "label": "AGA Rules of Go",
                "url": "https://www.usgo.org/aga-rules-go",
            },
            {
                "label": "Sensei's Library - Rules of Go",
                "url": "https://senseis.xmp.net/?RulesOfGo",
            },
        ]
        super().__init__(
            parent,
            title=self.translator.get("rules_help", "规则说明"),
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
                "rules_description",
                "不同规则在计分、劫争和贴目上略有差异，选择下方规则查看详情。",
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
            text=self.translator.get("rules_type", "规则"),
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
            text=self.translator.get("resources", "在线参考"),
            padding=8,
            style="Dialog.TLabelframe",
        )
        resources.pack(fill="x", pady=(4, 0))

        ttk.Label(
            resources,
            text="选择任一链接可在浏览器中查看完整规则原文。",
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
            self.content_text.insert(
                "end",
                "\n\n重点提示:\n- " + "\n- ".join(highlights),
            )
        self.content_text.configure(state="disabled")

    def _build_highlights(self, rule_key: str) -> List[str]:
        """不同规则的简要提示"""
        hints: Dict[str, List[str]] = {
            "chinese": [
                "数子法：活子与空点都计入地盘",
                "贴目常用 7.5 目",
                "收官阶段可以随手填空",
            ],
            "japanese": [
                "数目法：只数空与提子/死子",
                "贴 6.5 目，需判定死活后再数目",
                "连续两次虚手结束对局",
            ],
            "aga": [
                "区域计分，接近中国规则",
                "白方贴 7.5 目，每次虚手需交还一子",
                "规则明确，比赛常用",
            ],
        }
        return hints.get(rule_key, [])

    def _open_link(self, url: str):
        """在浏览器打开资源链接"""
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:  # pragma: no cover - UI 提示
            messagebox.showerror(
                self.translator.get("error", "错误"),
                f"无法打开链接: {exc}",
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
        self.teaching_system = teaching_system or TeachingSystem()
        self._type_labels: Dict[LessonType, str] = {
            LessonType.RULES: self.translator.get("rules", "规则"),
            LessonType.BASICS: self.translator.get("tutorial", "教程") + "·基础",
            LessonType.TACTICS: "战术训练",
            LessonType.STRATEGY: "战略思路",
            LessonType.LIFE_DEATH: "死活",
            LessonType.TESUJI: "手筋",
            LessonType.ENDGAME: "官子",
        }
        self._resources = [
            {
                "label": "在线围棋入门（OGS）",
                "url": "https://online-go.com/learn-to-play-go",
            },
            {
                "label": "AGA Learn to Play Go",
                "url": "https://www.usgo.org/learn-play-go",
            },
            {
                "label": "Sensei's Library - Beginner Exercises",
                "url": "https://senseis.xmp.net/?BeginnerExercises",
            },
        ]
        super().__init__(
            parent,
            title=self.translator.get("tutorial", "教程"),
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
            text="选择左侧课程即可查看内容，右侧可以逐步阅读并记录完成进度。",
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
            left, text="课程目录", padding=6, style="Dialog.TLabelframe"
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
            right, text="课程概览", padding=10, style="Dialog.TLabelframe"
        )
        overview.pack(fill="x")

        self.lesson_title = ttk.Label(
            overview, text="", font=("Arial", 13, "bold"), style="Dialog.TLabel"
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
            text=self.translator.get("tutorial", "教程"),
            padding=6,
            style="Dialog.TLabelframe",
        )
        lesson_frame.pack(fill="both", expand=True, pady=(8, 0))

        self.lesson_view = InteractiveLesson(lesson_frame, self.teaching_system)
        self.lesson_view.pack(fill="both", expand=True)

        resource_frame = ttk.LabelFrame(
            right, text="推荐阅读", padding=8, style="Dialog.TLabelframe"
        )
        resource_frame.pack(fill="x", pady=(8, 0))

        ttk.Label(
            resource_frame,
            text="需要更多示例或视频时，可以直接打开下列资源：",
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
        prereq = "先修: " + ("、".join(prereq_titles) if prereq_titles else "无")
        meta = f"{self._type_labels.get(lesson.type, lesson.type.value)} | 预计 {lesson.estimated_time} 分钟 | {prereq}"
        self.lesson_title.config(text=lesson.title)
        self.lesson_meta.config(text=meta)
        self.lesson_desc.config(text=lesson.description)
        if lesson.objectives:
            obj_text = "学习目标:\n- " + "\n- ".join(lesson.objectives)
        else:
            obj_text = ""
        self.objectives_label.config(text=obj_text)

        # 加载互动内容（允许预览，先修未完成时仍提示）
        try:
            self.lesson_view.load_lesson(lesson.id)
        except Exception:
            messagebox.showwarning(
                self.translator.get("warning", "警告"),
                "无法加载课程内容，请稍后再试。",
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
            text=f"已完成课程: {stats['lessons_completed']}/{stats['lessons_total']} | 棋题解决: {stats['puzzles_solved']} | 总积分: {stats['total_score']}"
        )

    def _open_link(self, url: str):
        """打开外部教程链接"""
        try:
            webbrowser.open(url, new=2)
        except Exception as exc:  # pragma: no cover - UI 提示
            messagebox.showerror(
                self.translator.get("error", "错误"),
                f"无法打开链接: {exc}",
                parent=self,
            )
