import { BookOpen, Bug, CheckCircle2, ClipboardCheck, Lightbulb, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { FeedbackBox } from "../components/FeedbackBox";
import { LessonBlockRenderer } from "../components/LessonBlockRenderer";
import { QuestionInteraction } from "../components/QuestionInteraction";
import { StatusBadge } from "../components/StrengthBadge";
import type { Feedback, LessonDetail, LessonProgress } from "../types";

export function LessonPage() {
  const { id } = useParams();
  const lessonId = Number(id);
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [explainBack, setExplainBack] = useState("");
  const [explainFeedback, setExplainFeedback] = useState<Feedback | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<{ name: string; message: string } | null>(null);

  useEffect(() => {
    if (!lessonId) return;
    api
      .lesson(lessonId)
      .then(setLesson)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load lesson."));
  }, [lessonId]);

  const quickQuestions = useMemo(
    () => lesson?.questions.filter((question) => question.question_type !== "explain_back") ?? [],
    [lesson]
  );
  const explainQuestion = lesson?.questions.find((question) => question.question_type === "explain_back");

  function updateProgress(progress: LessonProgress) {
    setLesson((current) => (current ? { ...current, progress } : current));
  }

  async function runAction(
    name: string,
    action: () => Promise<{ progress: LessonProgress; message: string }>
  ) {
    setBusyAction(name);
    setError(null);
    setActionNotice(null);
    try {
      const response = await action();
      updateProgress(response.progress);
      setActionNotice({ name, message: response.message });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setBusyAction(null);
    }
  }

  async function submitExplainBack() {
    if (!explainBack.trim()) {
      setError("Write an explain-back answer first.");
      return;
    }
    setBusyAction("explain");
    setExplainFeedback(null);
    setActionNotice(null);
    try {
      const response = await api.submitExplainBack(lessonId, explainBack);
      updateProgress(response.progress);
      const score = response.progress.explain_back_score ?? 0;
      setExplainFeedback({
        is_correct: score >= 0.7,
        score,
        what_part_is_wrong: score >= 0.7 ? null : "Your explanation missed one or more expected concepts.",
        why_it_is_wrong:
          score >= 0.7 ? null : "Explain-back answers need the concept and its backend consequence.",
        correct_concept: explainQuestion?.expected_concepts?.join(", ") ?? "lesson concept",
        simple_example: explainQuestion?.sample_ideal_answer ?? lesson?.why_it_matters ?? "",
        remedial_question: explainQuestion?.remedial_prompt ?? "Which part would matter in a real API route?",
        explanation:
          score >= 0.7
            ? "Accepted by the placeholder rubric. This is still heuristic, not AI grading."
            : "Matched against the placeholder rubric.",
        review_scheduled: score < 0.7
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit explain-back.");
    } finally {
      setBusyAction(null);
    }
  }

  if (error && !lesson) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-berry">{error}</div>;
  }

  if (!lesson) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-ink/65">Loading lesson...</div>;
  }

  const progress = lesson.progress;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <header className="panel p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-teal">Lesson</p>
            <h1 className="mt-2 text-3xl font-semibold leading-tight text-ink">{lesson.title}</h1>
            <p className="mt-3 text-sm leading-6 text-ink/70">{lesson.learning_goal}</p>
          </div>
          {progress ? <StatusBadge status={progress.status} /> : null}
        </div>
        <div className="mt-5 grid gap-3 rounded-md border border-line bg-paper p-4 text-sm text-ink/75 md:grid-cols-2">
          <div>
            <span className="font-medium text-ink">Why it matters:</span> {lesson.why_it_matters}
          </div>
          <div>
            <span className="font-medium text-ink">Mastery score:</span>{" "}
            {Math.round((progress?.mastery_score ?? 0) * 100)}%
          </div>
        </div>
        <ProofProgress progress={progress} />
        <div className="mt-5 flex flex-wrap gap-2">
          <button
            className="focus-ring inline-flex h-10 items-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white disabled:opacity-60"
            onClick={() => runAction("start", () => api.startLesson(lesson.id))}
            disabled={busyAction === "start" || Boolean(progress)}
            type="button"
          >
            <BookOpen size={16} aria-hidden />
            {progress ? "Started" : "Start"}
          </button>
          <button
            className="focus-ring inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-4 text-sm font-medium text-ink disabled:opacity-60"
            onClick={() => runAction("reading", () => api.completeReading(lesson.id))}
            disabled={busyAction === "reading" || Boolean(progress?.reading_completed)}
            type="button"
          >
            <CheckCircle2 size={16} aria-hidden />
            {progress?.reading_completed ? "Reading recorded" : "Finish reading"}
          </button>
        </div>
        {actionNotice && ["start", "reading"].includes(actionNotice.name) ? (
          <ActionNotice message={actionNotice.message} />
        ) : null}
        {error ? <p className="mt-4 text-sm text-berry">{error}</p> : null}
      </header>

      <div className="mt-6 grid gap-4">
        {lesson.blocks.map((block) => (
          <LessonBlockRenderer key={block.id} block={block} />
        ))}
      </div>

      <section className="mt-6 grid gap-4">
        <div className="flex items-center gap-2">
          <ClipboardCheck size={18} className="text-teal" aria-hidden />
          <h2 className="text-xl font-semibold text-ink">Proof checks</h2>
        </div>
        {quickQuestions.map((question) => (
          <QuestionInteraction key={question.id} question={question} onProgress={updateProgress} />
        ))}
      </section>

      <section className="panel mt-6 p-5">
        <div className="flex items-center gap-2">
          <Lightbulb size={18} className="text-amber" aria-hidden />
          <h2 className="text-xl font-semibold text-ink">Explain-back</h2>
        </div>
        <p className="mt-2 text-sm text-ink/65">{explainQuestion?.prompt}</p>
        <textarea
          className="focus-ring mt-4 min-h-32 w-full rounded-md border border-line bg-white p-3 text-sm"
          value={explainBack}
          onChange={(event) => setExplainBack(event.target.value)}
        />
        <button
          className="focus-ring mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white disabled:opacity-60"
          onClick={submitExplainBack}
          disabled={busyAction === "explain"}
          type="button"
        >
          <Send size={16} aria-hidden />
          Submit explain-back
        </button>
        {explainFeedback ? <FeedbackBox feedback={explainFeedback} /> : null}
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2">
        {lesson.debug_tasks.map((task) => (
          <div key={task.id} className="panel p-5">
            <div className="flex items-center gap-2">
              <Bug size={18} className="text-berry" aria-hidden />
              <h2 className="font-semibold text-ink">{task.title}</h2>
            </div>
            <p className="mt-2 text-sm leading-6 text-ink/70">{task.prompt}</p>
            <pre className="mt-4 overflow-x-auto rounded-md bg-ink p-4 text-sm leading-6 text-white">
              <code>{task.broken_code}</code>
            </pre>
            <button
              className="focus-ring mt-4 h-10 rounded-md border border-line bg-white px-4 text-sm font-medium text-ink disabled:opacity-60"
              onClick={() => runAction("debug", () => api.completeDebugTask(lesson.id))}
              disabled={busyAction === "debug" || Boolean(progress?.debug_task_completed)}
              type="button"
            >
              {progress?.debug_task_completed ? "Debug proof recorded" : "Mark debug proof"}
            </button>
            {actionNotice?.name === "debug" ? <ActionNotice message={actionNotice.message} /> : null}
          </div>
        ))}
        {lesson.mini_tasks.map((task) => (
          <div key={task.id} className="panel p-5">
            <div className="flex items-center gap-2">
              <ClipboardCheck size={18} className="text-moss" aria-hidden />
              <h2 className="font-semibold text-ink">{task.title}</h2>
            </div>
            <p className="mt-2 text-sm leading-6 text-ink/70">{task.prompt}</p>
            {task.acceptance_criteria ? (
              <ul className="mt-4 grid gap-2 text-sm text-ink/70">
                {task.acceptance_criteria.map((item) => (
                  <li key={item} className="flex gap-2">
                    <CheckCircle2 size={15} className="mt-1 text-moss" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : null}
            <button
              className="focus-ring mt-4 h-10 rounded-md border border-line bg-white px-4 text-sm font-medium text-ink disabled:opacity-60"
              onClick={() => runAction("mini", () => api.completeMiniTask(lesson.id))}
              disabled={busyAction === "mini" || Boolean(progress?.mini_task_completed)}
              type="button"
            >
              {progress?.mini_task_completed ? "Mini proof recorded" : "Mark mini proof"}
            </button>
            {actionNotice?.name === "mini" ? <ActionNotice message={actionNotice.message} /> : null}
          </div>
        ))}
      </section>

      <section className="panel mt-6 flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="font-semibold text-ink">End checkpoint</p>
          <p className="mt-1 text-sm text-ink/65">Reflection records attention, but mastery still depends on proof points.</p>
        </div>
        <button
          className="focus-ring h-10 rounded-md bg-teal px-4 text-sm font-medium text-white disabled:opacity-60"
          onClick={() => runAction("reflection", () => api.submitReflection(lesson.id))}
          disabled={busyAction === "reflection" || Boolean(progress?.reflection_submitted)}
          type="button"
        >
          {progress?.reflection_submitted ? "Reflection recorded" : "Record reflection"}
        </button>
      </section>
      {actionNotice?.name === "reflection" ? <ActionNotice message={actionNotice.message} /> : null}
    </div>
  );
}

function ProofProgress({ progress }: { progress?: LessonProgress | null }) {
  const items = [
    { label: "Reading", done: Boolean(progress?.reading_completed) },
    { label: "Quick check", done: (progress?.quick_check_score ?? 0) >= 0.7 },
    { label: "Explain-back", done: (progress?.explain_back_score ?? 0) >= 0.7 },
    { label: "Debug", done: Boolean(progress?.debug_task_completed) },
    { label: "Mini task", done: Boolean(progress?.mini_task_completed) },
    { label: "Reflection", done: Boolean(progress?.reflection_submitted) }
  ];

  return (
    <div className="mt-5 rounded-md border border-line bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm font-medium text-ink">Proof point status</p>
        <p className="text-xs text-ink/55">
          {items.filter((item) => item.done).length} of {items.length} recorded
        </p>
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <div
            key={item.label}
            className={`flex min-h-10 items-center gap-2 rounded-md border px-3 py-2 text-sm ${
              item.done
                ? "border-moss/30 bg-moss/10 text-ink"
                : "border-line bg-paper text-ink/60"
            }`}
          >
            <CheckCircle2
              size={16}
              className={item.done ? "text-moss" : "text-ink/25"}
              aria-hidden
            />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActionNotice({ message }: { message: string }) {
  return (
    <p
      className="mt-3 rounded-md border border-moss/30 bg-moss/10 px-3 py-2 text-sm text-ink"
      aria-live="polite"
    >
      {message}
    </p>
  );
}
