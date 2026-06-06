from enum import Enum


class UserRole(str, Enum):
    learner = "learner"
    admin = "admin"


class ContentStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class ProofType(str, Enum):
    explain_back = "explain_back"
    debug_task = "debug_task"
    mini_task = "mini_task"
    reflection = "reflection"
    review = "review"


class ProofStatus(str, Enum):
    submitted = "submitted"
    needs_revision = "needs_revision"
    passed = "passed"
    strong = "strong"


class ScoreLabel(str, Enum):
    incorrect = "incorrect"
    weak = "weak"
    stable = "stable"
    strong = "strong"


class BlockType(str, Enum):
    text = "text"
    code = "code"
    warning = "warning"
    example_good = "example_good"
    example_bad = "example_bad"
    common_mistake = "common_mistake"
    question = "question"
    reflection = "reflection"
    mini_task = "mini_task"
    debug_task = "debug_task"
    checklist = "checklist"


class QuestionType(str, Enum):
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    short_answer = "short_answer"
    explain_back = "explain_back"
    scenario_question = "scenario_question"


class LessonStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    needs_review = "needs_review"
    completed = "completed"
    mastered = "mastered"


class SkillStrength(str, Enum):
    not_started = "not_started"
    learning = "learning"
    weak = "weak"
    stable = "stable"
    strong = "strong"
