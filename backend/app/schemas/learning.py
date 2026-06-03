from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import (
    BlockType,
    ContentStatus,
    LessonStatus,
    QuestionType,
    SkillStrength,
)


class ConceptTagOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None

    model_config = {"from_attributes": True}


class LanguageOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    sort_order: int
    is_active: bool

    model_config = {"from_attributes": True}


class TrackOut(BaseModel):
    id: int
    language_id: int
    title: str
    slug: str
    description: str | None = None
    target_audience: str | None = None
    sort_order: int
    is_published: bool

    model_config = {"from_attributes": True}


class LevelOut(BaseModel):
    id: int
    track_id: int
    title: str
    slug: str
    description: str | None = None
    sort_order: int

    model_config = {"from_attributes": True}


class ModuleOut(BaseModel):
    id: int
    level_id: int
    title: str
    slug: str
    description: str | None = None
    estimated_minutes: int
    sort_order: int

    model_config = {"from_attributes": True}


class LessonSummaryOut(BaseModel):
    id: int
    module_id: int
    title: str
    slug: str
    learning_goal: str
    estimated_minutes: int
    sort_order: int
    status: LessonStatus = LessonStatus.not_started
    skill_strength: SkillStrength = SkillStrength.not_started
    mastery_score: float = 0.0
    locked: bool = False
    content_status: ContentStatus = ContentStatus.published

    model_config = {"from_attributes": True}


class ModuleMapOut(ModuleOut):
    progress: float = 0.0
    status: LessonStatus = LessonStatus.not_started
    skill_strength: SkillStrength = SkillStrength.not_started
    lessons: list[LessonSummaryOut] = []


class LevelMapOut(LevelOut):
    modules: list[ModuleMapOut] = []


class TrackDetailOut(TrackOut):
    language: LanguageOut
    levels: list[LevelMapOut] = []
    recommended_lesson: LessonSummaryOut | None = None


class LessonBlockOut(BaseModel):
    id: int
    lesson_id: int
    block_type: BlockType
    title: str | None = None
    body: str
    code_language: str | None = None
    block_metadata: dict[str, Any] | None = None
    sort_order: int

    model_config = {"from_attributes": True}


class QuestionOptionPublicOut(BaseModel):
    id: int
    label: str
    text: str

    model_config = {"from_attributes": True}


class QuestionOptionOut(QuestionOptionPublicOut):
    question_id: int
    is_correct: bool
    explanation: str


class QuestionOut(BaseModel):
    id: int
    lesson_id: int | None = None
    slug: str | None = None
    question_type: QuestionType
    prompt: str
    difficulty: str
    explanation: str | None = None
    expected_concepts: list[str] | None = None
    rubric: dict[str, Any] | None = None
    sample_ideal_answer: str | None = None
    misconception_notes: str | None = None
    remedial_prompt: str | None = None
    content_status: ContentStatus = ContentStatus.published
    options: list[QuestionOptionPublicOut] = []
    concept_tags: list[ConceptTagOut] = []

    model_config = {"from_attributes": True}


class MiniTaskOut(BaseModel):
    id: int
    lesson_id: int
    slug: str | None = None
    title: str
    prompt: str
    acceptance_criteria: list[str] | None = None
    difficulty: str
    content_status: ContentStatus = ContentStatus.published

    model_config = {"from_attributes": True}


class DebugTaskOut(BaseModel):
    id: int
    lesson_id: int
    slug: str | None = None
    title: str
    prompt: str
    broken_code: str
    hint: str | None = None
    expected_fix_summary: str | None = None
    difficulty: str
    content_status: ContentStatus = ContentStatus.published

    model_config = {"from_attributes": True}


class LessonProgressOut(BaseModel):
    lesson_id: int
    status: LessonStatus
    reading_completed: bool
    quick_check_score: float | None = None
    explain_back_submitted: bool
    explain_back_score: float | None = None
    debug_task_completed: bool
    mini_task_completed: bool
    reflection_submitted: bool
    review_required: bool
    mastery_score: float

    model_config = {"from_attributes": True}


class LessonDetailOut(BaseModel):
    id: int
    module_id: int
    title: str
    slug: str
    learning_goal: str
    why_it_matters: str
    estimated_minutes: int
    sort_order: int
    content_status: ContentStatus = ContentStatus.published
    concept_tags: list[ConceptTagOut] = []
    blocks: list[LessonBlockOut] = []
    questions: list[QuestionOut] = []
    mini_tasks: list[MiniTaskOut] = []
    debug_tasks: list[DebugTaskOut] = []
    progress: LessonProgressOut | None = None

    model_config = {"from_attributes": True}


class LanguageCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    sort_order: int = 0
    is_active: bool = True


class TrackCreate(BaseModel):
    language_id: int
    title: str
    slug: str
    description: str | None = None
    target_audience: str | None = None
    sort_order: int = 0
    is_published: bool = True


class LevelCreate(BaseModel):
    track_id: int
    title: str
    slug: str
    description: str | None = None
    sort_order: int = 0


class ModuleCreate(BaseModel):
    level_id: int
    title: str
    slug: str
    description: str | None = None
    estimated_minutes: int = 30
    sort_order: int = 0


class LessonCreate(BaseModel):
    module_id: int
    title: str
    slug: str
    learning_goal: str
    why_it_matters: str
    estimated_minutes: int = 12
    sort_order: int = 0
    is_published: bool = False
    content_status: ContentStatus = ContentStatus.draft


class LessonBlockCreate(BaseModel):
    lesson_id: int
    block_type: BlockType
    title: str | None = None
    body: str
    code_language: str | None = None
    block_metadata: dict[str, Any] | None = None
    sort_order: int = 0


class ConceptTagCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None


class QuestionOptionCreate(BaseModel):
    label: str
    text: str
    is_correct: bool = False
    explanation: str


class QuestionOptionAdminCreate(QuestionOptionCreate):
    question_id: int


class QuestionCreate(BaseModel):
    lesson_id: int | None = None
    slug: str | None = None
    question_type: QuestionType
    prompt: str
    difficulty: str = "foundation"
    correct_answer: str | None = None
    explanation: str | None = None
    expected_concepts: list[str] | None = None
    rubric: dict[str, Any] | None = None
    sample_ideal_answer: str | None = None
    misconception_notes: str | None = None
    remedial_prompt: str | None = None
    sort_order: int = 0
    content_status: ContentStatus = ContentStatus.draft
    concept_tag_ids: list[int] = Field(default_factory=list)
    options: list[QuestionOptionCreate] = Field(default_factory=list)


class MiniTaskCreate(BaseModel):
    lesson_id: int
    concept_tag_id: int | None = None
    slug: str | None = None
    title: str
    prompt: str
    acceptance_criteria: list[str] | None = None
    difficulty: str = "foundation"
    content_status: ContentStatus = ContentStatus.draft


class DebugTaskCreate(BaseModel):
    lesson_id: int
    concept_tag_id: int | None = None
    slug: str | None = None
    title: str
    prompt: str
    broken_code: str
    hint: str | None = None
    expected_fix_summary: str | None = None
    difficulty: str = "foundation"
    content_status: ContentStatus = ContentStatus.draft


class LessonImportConceptTag(BaseModel):
    name: str
    slug: str
    description: str | None = None


class LessonImportBlock(BaseModel):
    block_type: BlockType
    title: str | None = None
    body: str
    code_language: str | None = None
    block_metadata: dict[str, Any] | None = None
    sort_order: int = 0


class LessonImportQuestion(BaseModel):
    slug: str | None = None
    question_type: QuestionType
    prompt: str
    difficulty: str = "foundation"
    correct_answer: str | None = None
    explanation: str | None = None
    expected_concepts: list[str] | None = None
    rubric: dict[str, Any] | None = None
    sample_ideal_answer: str | None = None
    misconception_notes: str | None = None
    remedial_prompt: str | None = None
    sort_order: int = 0
    content_status: ContentStatus | None = None
    concept_tag_slugs: list[str] = Field(default_factory=list)
    options: list[QuestionOptionCreate] = Field(default_factory=list)


class LessonImportDebugTask(BaseModel):
    slug: str | None = None
    title: str
    prompt: str
    broken_code: str
    hint: str | None = None
    expected_fix_summary: str | None = None
    difficulty: str = "foundation"
    content_status: ContentStatus | None = None
    concept_tag_slug: str | None = None


class LessonImportMiniTask(BaseModel):
    slug: str | None = None
    title: str
    prompt: str
    acceptance_criteria: list[str] | None = None
    difficulty: str = "foundation"
    content_status: ContentStatus | None = None
    concept_tag_slug: str | None = None


class LessonImportPayload(BaseModel):
    module_id: int
    title: str
    slug: str
    learning_goal: str
    why_it_matters: str
    estimated_minutes: int = 12
    sort_order: int = 0
    content_status: ContentStatus = ContentStatus.draft
    concept_tags: list[LessonImportConceptTag] = Field(default_factory=list)
    blocks: list[LessonImportBlock] = Field(default_factory=list)
    questions: list[LessonImportQuestion] = Field(default_factory=list)
    debug_tasks: list[LessonImportDebugTask] = Field(default_factory=list)
    mini_tasks: list[LessonImportMiniTask] = Field(default_factory=list)


class LessonValidationResponse(BaseModel):
    lesson_id: int
    valid: bool
    errors: list[str]
