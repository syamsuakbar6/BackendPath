from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import (
    EvaluationConfidence,
    LessonStatus,
    ProofFinalStatus,
    ProofStatus,
    ProofType,
    ScoreLabel,
    SkillStrength,
)
from app.schemas.learning import LessonProgressOut, LessonSummaryOut


class LessonActionResponse(BaseModel):
    progress: LessonProgressOut
    message: str


class QuestionAnswerRequest(BaseModel):
    answer: Any


class FeedbackOut(BaseModel):
    is_correct: bool
    score: float
    what_part_is_wrong: str | None = None
    why_it_is_wrong: str | None = None
    correct_concept: str
    simple_example: str
    remedial_question: str
    explanation: str | None = None
    review_scheduled: bool = False


class QuestionAnswerResponse(BaseModel):
    attempt_id: int
    feedback: FeedbackOut
    lesson_progress: LessonProgressOut | None = None


class ExplainBackRequest(BaseModel):
    answer: str


class ConceptStrengthOut(BaseModel):
    concept: str
    strength: SkillStrength
    mastery_score: float
    wrong_count: int
    correct_count: int


class ReviewItemOut(BaseModel):
    id: int
    lesson_id: int | None = None
    question_id: int | None = None
    debug_task_id: int | None = None
    mini_task_id: int | None = None
    proof_submission_id: int | None = None
    concept: str | None = None
    lesson_title: str | None = None
    question_prompt: str | None = None
    debug_task_title: str | None = None
    mini_task_title: str | None = None
    proof_type: ProofType | None = None
    original_answer_text: str | None = None
    original_code_text: str | None = None
    original_feedback: dict[str, Any] | None = None
    missing_points: list[str] = Field(default_factory=list)
    remedial_question: str | None = None
    score_label: ScoreLabel | None = None
    score_numeric: float | None = None
    reason: str
    due_for_review: datetime
    review_count: int
    is_active: bool = True

    model_config = {"from_attributes": True}


class ProofSubmissionRequest(BaseModel):
    proof_type: ProofType
    question_id: int | None = None
    debug_task_id: int | None = None
    mini_task_id: int | None = None
    answer_text: str | None = None
    code_text: str | None = None


class ProofFeedbackOut(BaseModel):
    correct_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    feedback: str
    remedial_question: str
    evaluation_source: str = "heuristic"


class ProofSubmissionOut(BaseModel):
    id: int
    user_id: int
    lesson_id: int
    proof_type: ProofType
    question_id: int | None = None
    debug_task_id: int | None = None
    mini_task_id: int | None = None
    answer_text: str | None = None
    code_text: str | None = None
    status: ProofStatus
    score_label: ScoreLabel | None = None
    score_numeric: float | None = None
    feedback_json: ProofFeedbackOut | None = None
    heuristic_status: ProofStatus | None = None
    heuristic_score_label: ScoreLabel | None = None
    heuristic_score_numeric: float | None = None
    heuristic_feedback_json: ProofFeedbackOut | None = None
    evaluation_confidence: EvaluationConfidence | None = None
    final_evaluation_status: ProofFinalStatus | None = None
    final_score_label: ScoreLabel | None = None
    final_score_numeric: float | None = None
    final_feedback_json: ProofFeedbackOut | None = None
    overridden_by_id: int | None = None
    overridden_at: datetime | None = None
    override_note: str | None = None
    attempt_number: int
    created_at: datetime
    evaluated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AdminProofUserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str

    model_config = {"from_attributes": True}


class AdminProofLessonOut(BaseModel):
    id: int
    title: str
    slug: str

    model_config = {"from_attributes": True}


class AdminProofSubmissionOut(BaseModel):
    id: int
    user: AdminProofUserOut
    lesson: AdminProofLessonOut
    proof_type: ProofType
    question_id: int | None = None
    debug_task_id: int | None = None
    mini_task_id: int | None = None
    answer_text: str | None = None
    code_text: str | None = None
    status: ProofStatus
    score_label: ScoreLabel | None = None
    score_numeric: float | None = None
    feedback_json: ProofFeedbackOut | None = None
    heuristic_status: ProofStatus | None = None
    heuristic_score_label: ScoreLabel | None = None
    heuristic_score_numeric: float | None = None
    heuristic_feedback_json: ProofFeedbackOut | None = None
    evaluation_confidence: EvaluationConfidence | None = None
    final_evaluation_status: ProofFinalStatus | None = None
    final_score_label: ScoreLabel | None = None
    final_score_numeric: float | None = None
    final_feedback_json: ProofFeedbackOut | None = None
    overridden_by_id: int | None = None
    overridden_by_email: str | None = None
    overridden_at: datetime | None = None
    override_note: str | None = None
    attempt_number: int
    created_at: datetime
    evaluated_at: datetime | None = None
    created_review_item: bool
    review_item_ids: list[int] = Field(default_factory=list)


class AdminProofOverrideRequest(BaseModel):
    final_status: ProofFinalStatus
    override_note: str = Field(min_length=1, max_length=1000)
    score_label: ScoreLabel | None = None


class ProofEvaluationAnalyticsOut(BaseModel):
    total_submissions: int
    count_by_proof_type: dict[str, int]
    count_by_final_status: dict[str, int]
    count_by_heuristic_status: dict[str, int]
    count_by_confidence: dict[str, int]
    count_by_score_label: dict[str, int]
    override_count: int
    override_rate: float
    top_lessons_with_rejected_or_needs_review: list[dict[str, int | str]]
    top_misconceptions: list[dict[str, int | str]]


class ProofSubmissionResponse(BaseModel):
    submission: ProofSubmissionOut
    progress: LessonProgressOut
    message: str


class ReviewSubmissionRequest(BaseModel):
    answer_text: str
    code_text: str | None = None


class ReviewSubmissionResponse(BaseModel):
    review: ReviewItemOut
    passed: bool
    status: ProofStatus
    score_label: ScoreLabel
    score_numeric: float
    evaluation_confidence: EvaluationConfidence
    feedback_json: ProofFeedbackOut
    progress: LessonProgressOut | None = None
    next_due_for_review: datetime | None = None
    message: str


class MissingProofRequirementOut(BaseModel):
    key: str
    label: str
    status: str
    detail: str


class DashboardOut(BaseModel):
    active_track: str | None
    current_level: str | None
    recommended_next_lesson: LessonSummaryOut | None
    continue_lesson: LessonSummaryOut | None
    weak_concepts: list[ConceptStrengthOut]
    due_reviews: list[ReviewItemOut]
    active_due_reviews_count: int
    current_lesson_blocked_by_review: bool
    next_recommended_review_action: str | None = None
    missing_proof_requirements: list[MissingProofRequirementOut]
    consistency_label: str
    mastery_labels: list[str]
    session_modes: dict[str, int]


class SearchResultItem(BaseModel):
    type: str
    id: int
    title: str
    description: str | None = None
    parent: str | None = None


class SearchResponse(BaseModel):
    query: str
    concept_tags: list[SearchResultItem]
    lessons: list[SearchResultItem]
    questions: list[SearchResultItem]
    debug_tasks: list[SearchResultItem]
    mini_tasks: list[SearchResultItem]
    modules: list[SearchResultItem]
    tracks: list[SearchResultItem]
