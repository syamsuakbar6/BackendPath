export type UserRole = "learner" | "admin";
export type LessonStatus =
  | "not_started"
  | "in_progress"
  | "needs_review"
  | "completed"
  | "mastered";
export type SkillStrength = "not_started" | "learning" | "weak" | "stable" | "strong";
export type ContentStatus = "draft" | "published" | "archived";
export type BlockType =
  | "text"
  | "code"
  | "warning"
  | "example_good"
  | "example_bad"
  | "question"
  | "reflection"
  | "mini_task"
  | "debug_task"
  | "checklist";
export type QuestionType =
  | "multiple_choice"
  | "true_false"
  | "short_answer"
  | "explain_back"
  | "scenario_question";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  current_streak: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: "bearer";
  user: User;
}

export interface Language {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
  sort_order: number;
  is_active: boolean;
}

export interface Track {
  id: number;
  language_id: number;
  title: string;
  slug: string;
  description?: string | null;
  target_audience?: string | null;
  sort_order: number;
  is_published: boolean;
}

export interface ConceptTag {
  id: number;
  name: string;
  slug: string;
  description?: string | null;
}

export interface LessonProgress {
  lesson_id: number;
  status: LessonStatus;
  reading_completed: boolean;
  quick_check_score?: number | null;
  explain_back_submitted: boolean;
  explain_back_score?: number | null;
  debug_task_completed: boolean;
  mini_task_completed: boolean;
  reflection_submitted: boolean;
  review_required: boolean;
  mastery_score: number;
}

export interface LessonSummary {
  id: number;
  module_id: number;
  title: string;
  slug: string;
  learning_goal: string;
  estimated_minutes: number;
  sort_order: number;
  status: LessonStatus;
  skill_strength: SkillStrength;
  mastery_score: number;
  locked: boolean;
  content_status: ContentStatus;
}

export interface ModuleMap {
  id: number;
  level_id: number;
  title: string;
  slug: string;
  description?: string | null;
  estimated_minutes: number;
  sort_order: number;
  progress: number;
  status: LessonStatus;
  skill_strength: SkillStrength;
  lessons: LessonSummary[];
}

export interface LevelMap {
  id: number;
  track_id: number;
  title: string;
  slug: string;
  description?: string | null;
  sort_order: number;
  modules: ModuleMap[];
}

export interface TrackDetail extends Track {
  language: Language;
  levels: LevelMap[];
  recommended_lesson?: LessonSummary | null;
}

export interface LessonBlock {
  id: number;
  lesson_id: number;
  block_type: BlockType;
  title?: string | null;
  body: string;
  code_language?: string | null;
  block_metadata?: Record<string, unknown> | null;
  sort_order: number;
}

export interface QuestionOption {
  id: number;
  label: string;
  text: string;
}

export interface Question {
  id: number;
  lesson_id?: number | null;
  question_type: QuestionType;
  prompt: string;
  difficulty: string;
  explanation?: string | null;
  expected_concepts?: string[] | null;
  rubric?: Record<string, string> | null;
  sample_ideal_answer?: string | null;
  misconception_notes?: string | null;
  remedial_prompt?: string | null;
  content_status: ContentStatus;
  options: QuestionOption[];
  concept_tags: ConceptTag[];
}

export interface MiniTask {
  id: number;
  lesson_id: number;
  title: string;
  prompt: string;
  acceptance_criteria?: string[] | null;
  difficulty: string;
  content_status: ContentStatus;
}

export interface DebugTask {
  id: number;
  lesson_id: number;
  title: string;
  prompt: string;
  broken_code: string;
  hint?: string | null;
  expected_fix_summary?: string | null;
  difficulty: string;
  content_status: ContentStatus;
}

export interface LessonDetail {
  id: number;
  module_id: number;
  title: string;
  slug: string;
  learning_goal: string;
  why_it_matters: string;
  estimated_minutes: number;
  sort_order: number;
  content_status: ContentStatus;
  concept_tags: ConceptTag[];
  blocks: LessonBlock[];
  questions: Question[];
  mini_tasks: MiniTask[];
  debug_tasks: DebugTask[];
  progress?: LessonProgress | null;
}

export interface Feedback {
  is_correct: boolean;
  score: number;
  what_part_is_wrong?: string | null;
  why_it_is_wrong?: string | null;
  correct_concept: string;
  simple_example: string;
  remedial_question: string;
  explanation?: string | null;
  review_scheduled: boolean;
}

export interface QuestionAnswerResponse {
  attempt_id: number;
  feedback: Feedback;
  lesson_progress?: LessonProgress | null;
}

export interface ReviewItem {
  id: number;
  concept?: string | null;
  lesson_title?: string | null;
  question_prompt?: string | null;
  reason: string;
  due_for_review: string;
  review_count: number;
}

export interface Dashboard {
  active_track?: string | null;
  current_level?: string | null;
  recommended_next_lesson?: LessonSummary | null;
  continue_lesson?: LessonSummary | null;
  weak_concepts: Array<{
    concept: string;
    strength: SkillStrength;
    mastery_score: number;
    wrong_count: number;
    correct_count: number;
  }>;
  due_reviews: ReviewItem[];
  consistency_label: string;
  mastery_labels: string[];
  session_modes: Record<string, number>;
}

export interface SearchResultItem {
  type: string;
  id: number;
  title: string;
  description?: string | null;
  parent?: string | null;
}

export interface SearchResponse {
  query: string;
  concept_tags: SearchResultItem[];
  lessons: SearchResultItem[];
  questions: SearchResultItem[];
  debug_tasks: SearchResultItem[];
  mini_tasks: SearchResultItem[];
  modules: SearchResultItem[];
  tracks: SearchResultItem[];
}
