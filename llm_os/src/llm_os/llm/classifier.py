"""
Task Classifier

Classifies user inputs by complexity to route to appropriate models.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Pattern


class TaskType(Enum):
    """Types of tasks based on complexity."""
    SIMPLE = auto()      # Basic commands: "open firefox", "list files"
    MODERATE = auto()    # Multi-step: "create folder and move files"
    COMPLEX = auto()     # Planning needed: "set up development environment"
    REASONING = auto()   # Deep thinking: "debug this error", "analyze code"
    CREATIVE = auto()    # Creative tasks: "write a script", "explain concept"


@dataclass
class ClassificationResult:
    """Result of task classification."""
    task_type: TaskType
    confidence: float
    matched_patterns: list[str]
    suggested_model_tier: str  # "fast", "default", "best", "reasoning"


class TaskClassifier:
    """
    Classifies user inputs to determine task complexity.

    This helps route requests to appropriate models:
    - Simple tasks -> Fast, cheap models
    - Complex tasks -> More capable models
    - Reasoning tasks -> Specialized reasoning models
    """

    # Pattern definitions for each task type
    SIMPLE_PATTERNS: list[tuple[Pattern[str], str]] = [
        (re.compile(r"^open\s+\w+$", re.IGNORECASE), "open_app"),
        (re.compile(r"^close\s+\w+$", re.IGNORECASE), "close_app"),
        (re.compile(r"^(show|list|display)\s+(files?|folder|directory)", re.IGNORECASE), "list_files"),
        (re.compile(r"^what\s+(time|date)", re.IGNORECASE), "time_query"),
        (re.compile(r"^(show|get|check)\s+(memory|cpu|disk|system)", re.IGNORECASE), "system_info"),
        (re.compile(r"^(clear|cls)$", re.IGNORECASE), "clear"),
        (re.compile(r"^(exit|quit|bye)$", re.IGNORECASE), "exit"),
        (re.compile(r"^help$", re.IGNORECASE), "help"),
        (re.compile(r"^pwd$", re.IGNORECASE), "pwd"),
        (re.compile(r"^whoami$", re.IGNORECASE), "whoami"),
    ]

    MODERATE_PATTERNS: list[tuple[Pattern[str], str]] = [
        (re.compile(r"create\s+.+\s+and\s+", re.IGNORECASE), "multi_step"),
        (re.compile(r"move\s+.+\s+to\s+", re.IGNORECASE), "move_files"),
        (re.compile(r"copy\s+.+\s+to\s+", re.IGNORECASE), "copy_files"),
        (re.compile(r"rename\s+", re.IGNORECASE), "rename"),
        (re.compile(r"(install|uninstall)\s+", re.IGNORECASE), "package_mgmt"),
        (re.compile(r"download\s+", re.IGNORECASE), "download"),
        (re.compile(r"search\s+(for|the)\s+", re.IGNORECASE), "search"),
        (re.compile(r"find\s+(all|files?|where)", re.IGNORECASE), "find"),
        (re.compile(r"(git|commit|push|pull|clone)\s+", re.IGNORECASE), "git_operation"),
        (re.compile(r"run\s+(the\s+)?(test|build|script)", re.IGNORECASE), "run_command"),
    ]

    COMPLEX_PATTERNS: list[tuple[Pattern[str], str]] = [
        (re.compile(r"set\s*up\s+", re.IGNORECASE), "setup"),
        (re.compile(r"configure\s+", re.IGNORECASE), "configure"),
        (re.compile(r"create\s+(a\s+)?(new\s+)?(project|app|application)", re.IGNORECASE), "create_project"),
        (re.compile(r"migrate\s+", re.IGNORECASE), "migrate"),
        (re.compile(r"refactor\s+", re.IGNORECASE), "refactor"),
        (re.compile(r"deploy\s+", re.IGNORECASE), "deploy"),
        (re.compile(r"backup\s+.+\s+and\s+", re.IGNORECASE), "backup"),
        (re.compile(r"automate\s+", re.IGNORECASE), "automate"),
        (re.compile(r"(build|compile)\s+(the\s+)?(project|app)", re.IGNORECASE), "build"),
    ]

    REASONING_PATTERNS: list[tuple[Pattern[str], str]] = [
        (re.compile(r"(debug|fix)\s+(this|the)\s+(error|bug|issue)", re.IGNORECASE), "debug"),
        (re.compile(r"(analyze|analyse)\s+", re.IGNORECASE), "analyze"),
        (re.compile(r"why\s+(is|does|did|are|do)\s+", re.IGNORECASE), "why_question"),
        (re.compile(r"what\s+(caused|is\s+causing|went\s+wrong)", re.IGNORECASE), "diagnose"),
        (re.compile(r"(figure\s+out|understand)\s+", re.IGNORECASE), "understand"),
        (re.compile(r"(optimize|improve)\s+(the\s+)?(performance|speed)", re.IGNORECASE), "optimize"),
        (re.compile(r"compare\s+.+\s+(with|to|and)\s+", re.IGNORECASE), "compare"),
        (re.compile(r"(review|audit)\s+(the\s+)?code", re.IGNORECASE), "code_review"),
    ]

    CREATIVE_PATTERNS: list[tuple[Pattern[str], str]] = [
        (re.compile(r"(write|create)\s+(a\s+)?(script|code|program|function)", re.IGNORECASE), "write_code"),
        (re.compile(r"explain\s+(how|what|why)", re.IGNORECASE), "explain"),
        (re.compile(r"(summarize|summary)\s+", re.IGNORECASE), "summarize"),
        (re.compile(r"(generate|create)\s+(a\s+)?(readme|documentation|doc)", re.IGNORECASE), "generate_docs"),
        (re.compile(r"(help\s+me\s+)?(write|draft)\s+", re.IGNORECASE), "write"),
        (re.compile(r"(suggest|recommend)\s+", re.IGNORECASE), "suggest"),
    ]

    # Complexity indicators (words that suggest higher complexity)
    COMPLEXITY_INDICATORS = {
        "high": [
            "all", "every", "entire", "complete", "comprehensive",
            "multiple", "several", "various", "different",
            "complex", "advanced", "detailed", "thorough",
        ],
        "medium": [
            "some", "few", "certain", "specific",
            "then", "after", "before", "when", "if",
        ],
        "low": [
            "just", "only", "simple", "quick", "basic",
            "single", "one", "this", "that",
        ]
    }

    def __init__(self):
        """Initialize the classifier."""
        pass

    def classify(self, user_input: str) -> ClassificationResult:
        """
        Classify a user input by complexity.

        Args:
            user_input: The user's natural language input

        Returns:
            ClassificationResult with task type and metadata
        """
        user_input = user_input.strip()
        matched_patterns: list[str] = []

        # Check patterns in order of specificity
        task_type = TaskType.MODERATE  # Default
        confidence = 0.5

        # Check simple patterns first
        for pattern, name in self.SIMPLE_PATTERNS:
            if pattern.search(user_input):
                matched_patterns.append(name)
                task_type = TaskType.SIMPLE
                confidence = 0.9

        # Check reasoning patterns (high priority if matched)
        if task_type != TaskType.SIMPLE:
            for pattern, name in self.REASONING_PATTERNS:
                if pattern.search(user_input):
                    matched_patterns.append(name)
                    task_type = TaskType.REASONING
                    confidence = 0.85

        # Check complex patterns
        if task_type == TaskType.MODERATE:
            for pattern, name in self.COMPLEX_PATTERNS:
                if pattern.search(user_input):
                    matched_patterns.append(name)
                    task_type = TaskType.COMPLEX
                    confidence = 0.8

        # Check creative patterns
        if task_type == TaskType.MODERATE:
            for pattern, name in self.CREATIVE_PATTERNS:
                if pattern.search(user_input):
                    matched_patterns.append(name)
                    task_type = TaskType.CREATIVE
                    confidence = 0.75

        # Check moderate patterns
        if task_type == TaskType.MODERATE:
            for pattern, name in self.MODERATE_PATTERNS:
                if pattern.search(user_input):
                    matched_patterns.append(name)
                    confidence = 0.7
                    break

        # Adjust based on complexity indicators
        task_type, confidence = self._adjust_for_complexity(
            user_input, task_type, confidence
        )

        # Adjust based on input length
        task_type, confidence = self._adjust_for_length(
            user_input, task_type, confidence
        )

        # Determine suggested model tier
        model_tier = self._get_model_tier(task_type)

        return ClassificationResult(
            task_type=task_type,
            confidence=confidence,
            matched_patterns=matched_patterns,
            suggested_model_tier=model_tier,
        )

    def _adjust_for_complexity(
        self,
        user_input: str,
        task_type: TaskType,
        confidence: float,
    ) -> tuple[TaskType, float]:
        """Adjust classification based on complexity indicators."""
        words = user_input.lower().split()

        high_count = sum(1 for w in words if w in self.COMPLEXITY_INDICATORS["high"])
        low_count = sum(1 for w in words if w in self.COMPLEXITY_INDICATORS["low"])

        # High complexity indicators push toward complex
        if high_count >= 2 and task_type in (TaskType.SIMPLE, TaskType.MODERATE):
            task_type = TaskType.COMPLEX
            confidence = min(confidence + 0.1, 0.95)

        # Low complexity indicators push toward simple
        if low_count >= 2 and task_type == TaskType.MODERATE:
            task_type = TaskType.SIMPLE
            confidence = min(confidence + 0.1, 0.95)

        return task_type, confidence

    def _adjust_for_length(
        self,
        user_input: str,
        task_type: TaskType,
        confidence: float,
    ) -> tuple[TaskType, float]:
        """Adjust classification based on input length."""
        word_count = len(user_input.split())

        # Very short inputs are likely simple
        if word_count <= 3 and task_type == TaskType.MODERATE:
            task_type = TaskType.SIMPLE
            confidence = min(confidence + 0.15, 0.95)

        # Very long inputs suggest complexity
        if word_count > 30 and task_type in (TaskType.SIMPLE, TaskType.MODERATE):
            task_type = TaskType.COMPLEX
            confidence = min(confidence + 0.1, 0.95)

        return task_type, confidence

    def _get_model_tier(self, task_type: TaskType) -> str:
        """Get suggested model tier for task type."""
        tier_mapping = {
            TaskType.SIMPLE: "fast",
            TaskType.MODERATE: "default",
            TaskType.COMPLEX: "best",
            TaskType.REASONING: "reasoning",
            TaskType.CREATIVE: "default",
        }
        return tier_mapping.get(task_type, "default")

    def get_task_description(self, task_type: TaskType) -> str:
        """Get human-readable description of task type."""
        descriptions = {
            TaskType.SIMPLE: "Simple, single-step task",
            TaskType.MODERATE: "Multi-step task with clear steps",
            TaskType.COMPLEX: "Complex task requiring planning",
            TaskType.REASONING: "Task requiring analysis and reasoning",
            TaskType.CREATIVE: "Creative or generative task",
        }
        return descriptions.get(task_type, "Unknown task type")
