import { BookOpen, Bug, CheckCircle2, ClipboardCheck, Lightbulb, Send } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import { LessonBlockRenderer } from "../components/LessonBlockRenderer";
import { QuestionInteraction } from "../components/QuestionInteraction";
import { StatusBadge } from "../components/StrengthBadge";
import type { LessonDetail, LessonProgress, ProofSubmission, ProofType } from "../types";

export function LessonPage() {
  const { id } = useParams();
  const lessonId = Number(id);
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [proofSubmissions, setProofSubmissions] = useState<ProofSubmission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [explainBack, setExplainBack] = useState("");
  const [debugForms, setDebugForms] = useState<Record<number, { bug: string; cause: string; fix: string }>>({});
  const [miniForms, setMiniForms] = useState<Record<number, { code: string; explanation: string }>>({});
  const [reflectionForm, setReflectionForm] = useState({ understood: "", confusing: "", useCase: "" });
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<{ name: string; message: string } | null>(null);

  useEffect(() => {
    if (!lessonId) return;
    api
      .lesson(lessonId)
      .then(setLesson)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load lesson."));
    api
      .lessonProofs(lessonId)
      .then(setProofSubmissions)
      .catch(() => setProofSubmissions([]));
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

  function upsertProof(submission: ProofSubmission) {
    setProofSubmissions((current) => [
      submission,
      ...current.filter((item) => item.id !== submission.id)
    ]);
  }

  async function submitProof(
    name: string,
    payload: Parameters<typeof api.submitProof>[1]
  ) {
    setBusyAction(name);
    setError(null);
    setActionNotice(null);
    try {
      const response = await api.submitProof(lessonId, payload);
      updateProgress(response.progress);
      upsertProof(response.submission);
      setActionNotice({ name, message: response.message });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit proof.");
    } finally {
      setBusyAction(null);
    }
  }

  async function submitExplainBack() {
    if (!explainBack.trim()) {
      setError("Write an explain-back answer first.");
      return;
    }
    await submitProof("explain", {
      proof_type: "explain_back",
      question_id: explainQuestion?.id,
      answer_text: explainBack
    });
  }

  if (error && !lesson) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-berry">{error}</div>;
  }

  if (!lesson) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-ink/65">Loading lesson...</div>;
  }

  const progress = lesson.progress;
  const latestExplainProof = latestProof(proofSubmissions, "explain_back", {
    question_id: explainQuestion?.id
  });

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
        {latestExplainProof ? <ProofEvaluationBox submission={latestExplainProof} /> : null}
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
            <div className="mt-4 grid gap-3">
              <ProofTextarea
                label="What is the bug?"
                value={debugForms[task.id]?.bug ?? ""}
                onChange={(value) =>
                  setDebugForms((current) => ({
                    ...current,
                    [task.id]: { bug: value, cause: current[task.id]?.cause ?? "", fix: current[task.id]?.fix ?? "" }
                  }))
                }
              />
              <ProofTextarea
                label="Why is it wrong?"
                value={debugForms[task.id]?.cause ?? ""}
                onChange={(value) =>
                  setDebugForms((current) => ({
                    ...current,
                    [task.id]: { bug: current[task.id]?.bug ?? "", cause: value, fix: current[task.id]?.fix ?? "" }
                  }))
                }
              />
              <ProofTextarea
                label="How would you fix it?"
                value={debugForms[task.id]?.fix ?? ""}
                onChange={(value) =>
                  setDebugForms((current) => ({
                    ...current,
                    [task.id]: { bug: current[task.id]?.bug ?? "", cause: current[task.id]?.cause ?? "", fix: value }
                  }))
                }
              />
            </div>
            <button
              className="focus-ring mt-4 h-10 rounded-md border border-line bg-white px-4 text-sm font-medium text-ink disabled:opacity-60"
              onClick={() =>
                submitProof(`debug-${task.id}`, {
                  proof_type: "debug_task",
                  debug_task_id: task.id,
                  answer_text: [
                    `Bug: ${debugForms[task.id]?.bug ?? ""}`,
                    `Cause: ${debugForms[task.id]?.cause ?? ""}`,
                    `Fix: ${debugForms[task.id]?.fix ?? ""}`
                  ].join("\n")
                })
              }
              disabled={busyAction === `debug-${task.id}`}
              type="button"
            >
              Submit debug proof
            </button>
            {actionNotice?.name === `debug-${task.id}` ? <ActionNotice message={actionNotice.message} /> : null}
            {latestProof(proofSubmissions, "debug_task", { debug_task_id: task.id }) ? (
              <ProofEvaluationBox submission={latestProof(proofSubmissions, "debug_task", { debug_task_id: task.id })!} />
            ) : null}
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
            <label className="mt-4 block">
              <span className="text-sm font-medium text-ink">Your solution/code</span>
              <textarea
                className="focus-ring mt-2 min-h-36 w-full rounded-md border border-line bg-white p-3 font-mono text-sm"
                value={miniForms[task.id]?.code ?? ""}
                onChange={(event) =>
                  setMiniForms((current) => ({
                    ...current,
                    [task.id]: { code: event.target.value, explanation: current[task.id]?.explanation ?? "" }
                  }))
                }
              />
            </label>
            <ProofTextarea
              label="Short explanation"
              value={miniForms[task.id]?.explanation ?? ""}
              onChange={(value) =>
                setMiniForms((current) => ({
                  ...current,
                  [task.id]: { code: current[task.id]?.code ?? "", explanation: value }
                }))
              }
            />
            <button
              className="focus-ring mt-4 h-10 rounded-md border border-line bg-white px-4 text-sm font-medium text-ink disabled:opacity-60"
              onClick={() =>
                submitProof(`mini-${task.id}`, {
                  proof_type: "mini_task",
                  mini_task_id: task.id,
                  answer_text: miniForms[task.id]?.explanation ?? "",
                  code_text: miniForms[task.id]?.code ?? ""
                })
              }
              disabled={busyAction === `mini-${task.id}`}
              type="button"
            >
              Submit mini task proof
            </button>
            {actionNotice?.name === `mini-${task.id}` ? <ActionNotice message={actionNotice.message} /> : null}
            {latestProof(proofSubmissions, "mini_task", { mini_task_id: task.id }) ? (
              <ProofEvaluationBox submission={latestProof(proofSubmissions, "mini_task", { mini_task_id: task.id })!} />
            ) : null}
          </div>
        ))}
      </section>

      <section className="panel mt-6 flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
        <div className="flex-1">
          <p className="font-semibold text-ink">End checkpoint</p>
          <p className="mt-1 text-sm text-ink/65">Reflection records attention, but mastery still depends on proof points.</p>
          <div className="mt-4 grid gap-3">
            <ProofTextarea
              label="What did you understand?"
              value={reflectionForm.understood}
              onChange={(value) => setReflectionForm((current) => ({ ...current, understood: value }))}
            />
            <ProofTextarea
              label="What is still confusing?"
              value={reflectionForm.confusing}
              onChange={(value) => setReflectionForm((current) => ({ ...current, confusing: value }))}
            />
            <ProofTextarea
              label="Where would you use this?"
              value={reflectionForm.useCase}
              onChange={(value) => setReflectionForm((current) => ({ ...current, useCase: value }))}
            />
          </div>
        </div>
        <button
          className="focus-ring h-10 rounded-md bg-teal px-4 text-sm font-medium text-white disabled:opacity-60 md:self-end"
          onClick={() =>
            submitProof("reflection", {
              proof_type: "reflection",
              answer_text: [
                `Understood: ${reflectionForm.understood}`,
                `Still confusing: ${reflectionForm.confusing}`,
                `Use case: ${reflectionForm.useCase}`
              ].join("\n")
            })
          }
          disabled={busyAction === "reflection"}
          type="button"
        >
          Submit reflection
        </button>
      </section>
      {actionNotice?.name === "reflection" ? <ActionNotice message={actionNotice.message} /> : null}
      {latestProof(proofSubmissions, "reflection") ? (
        <ProofEvaluationBox submission={latestProof(proofSubmissions, "reflection")!} />
      ) : null}
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

function ProofTextarea({
  label,
  value,
  onChange
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="text-sm font-medium text-ink">{label}</span>
      <textarea
        className="focus-ring mt-2 min-h-24 w-full rounded-md border border-line bg-white p-3 text-sm"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

function ProofEvaluationBox({ submission }: { submission: ProofSubmission }) {
  const passed = isPassingProof(submission);
  const feedback = submission.feedback_json;
  return (
    <div
      className={`mt-4 rounded-md border p-4 ${
        passed ? "border-moss/30 bg-moss/10" : "border-berry/30 bg-berry/10"
      }`}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="font-medium text-ink">
          {passed ? "Proof accepted" : "Needs revision"} - score{" "}
          {Math.round((submission.score_numeric ?? 0) * 100)}%
        </p>
        <span className="rounded-md border border-line bg-white px-2 py-1 text-xs text-ink/65">
          attempt {submission.attempt_number}
        </span>
      </div>
      {feedback ? (
        <div className="mt-3 grid gap-3 text-sm leading-6 text-ink/76">
          <p>{feedback.feedback}</p>
          {feedback.correct_points.length ? (
            <div>
              <p className="font-medium text-ink">Correct points</p>
              <ul className="mt-1 grid gap-1">
                {feedback.correct_points.map((item) => (
                  <li key={item} className="flex gap-2">
                    <CheckCircle2 size={15} className="mt-1 text-moss" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {feedback.missing_points.length ? (
            <div>
              <p className="font-medium text-ink">Missing points</p>
              <ul className="mt-1 grid gap-1">
                {feedback.missing_points.map((item) => (
                  <li key={item} className="text-ink/70">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <p className="rounded-md bg-white/70 p-3">{feedback.remedial_question}</p>
        </div>
      ) : null}
    </div>
  );
}

function latestProof(
  submissions: ProofSubmission[],
  proofType: ProofType,
  ids: { question_id?: number; debug_task_id?: number; mini_task_id?: number } = {}
) {
  return submissions.find((submission) => {
    if (submission.proof_type !== proofType) return false;
    if (ids.question_id && submission.question_id !== ids.question_id) return false;
    if (ids.debug_task_id && submission.debug_task_id !== ids.debug_task_id) return false;
    if (ids.mini_task_id && submission.mini_task_id !== ids.mini_task_id) return false;
    return true;
  });
}

function isPassingProof(submission: ProofSubmission) {
  return submission.status === "passed" || submission.status === "strong";
}
