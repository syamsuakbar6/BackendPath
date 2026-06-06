import {
  Archive,
  Bug,
  CheckCircle2,
  BarChart3,
  ClipboardCheck,
  Database,
  Eye,
  FileDown,
  FileUp,
  Lightbulb,
  ListFilter,
  Plus,
  Send,
  ShieldCheck
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { LessonBlockRenderer } from "../components/LessonBlockRenderer";
import type {
  AdminProofFilters,
  AdminProofOverrideRequest,
  AdminProofSubmission,
  LessonDetail,
  ProofEvaluationAnalytics
} from "../types";

const resources = [
  "languages",
  "tracks",
  "levels",
  "modules",
  "lessons",
  "lesson-blocks",
  "questions",
  "question-options",
  "debug-tasks",
  "mini-tasks",
  "concept-tags"
];

const samples: Record<string, Record<string, unknown>> = {
  languages: {
    name: "JavaScript",
    slug: "javascript",
    description: "JavaScript backend track",
    sort_order: 2,
    is_active: true
  },
  "concept-tags": {
    name: "Dependency Injection",
    slug: "dependency-injection",
    description: "Passing dependencies explicitly for testable backend code."
  },
  tracks: {
    language_id: 1,
    title: "Python Backend Project Path",
    slug: "python-backend-project-path",
    description: "Project-based backend practice.",
    target_audience: "Junior backend developer",
    sort_order: 2,
    is_published: true
  },
  levels: {
    track_id: 1,
    title: "API Builder",
    slug: "api-builder",
    description: "Build and reason about APIs.",
    sort_order: 3
  },
  modules: {
    level_id: 1,
    title: "Request Validation",
    slug: "request-validation",
    description: "Validate input before backend work.",
    estimated_minutes: 30,
    sort_order: 3
  },
  lessons: {
    module_id: 1,
    title: "Placeholder lesson",
    slug: "placeholder-lesson",
    learning_goal: "State the concept in plain language.",
    why_it_matters: "Backend code needs clear reasoning.",
    estimated_minutes: 12,
    sort_order: 9,
    is_published: false,
    content_status: "draft"
  },
  "lesson-blocks": {
    lesson_id: 1,
    block_type: "text",
    title: "Concept",
    body: "Placeholder block.",
    sort_order: 99
  },
  questions: {
    lesson_id: 1,
    question_type: "multiple_choice",
    prompt: "Which option is correct?",
    difficulty: "foundation",
    explanation: "Because it matches the concept.",
    concept_tag_ids: [1],
    options: [
      { label: "A", text: "Incorrect", is_correct: false, explanation: "This misses the concept." },
      { label: "B", text: "Correct", is_correct: true, explanation: "This matches the concept." }
    ]
  },
  "question-options": {
    question_id: 1,
    label: "C",
    text: "Additional option",
    is_correct: false,
    explanation: "This is a placeholder wrong option."
  },
  "debug-tasks": {
    lesson_id: 1,
    concept_tag_id: 1,
    title: "Debug placeholder",
    prompt: "Explain what is broken and how to fix it.",
    broken_code: "def example():\n    print('value')",
    hint: "Look for a hidden output.",
    expected_fix_summary: "Return caller-visible data.",
    difficulty: "foundation",
    content_status: "draft"
  },
  "mini-tasks": {
    lesson_id: 1,
    concept_tag_id: 1,
    title: "Mini task placeholder",
    prompt: "Apply the concept in a small backend-flavored function.",
    acceptance_criteria: ["Uses the concept intentionally", "Can be explained briefly"],
    difficulty: "foundation",
    content_status: "draft"
  }
};

export function AdminContentPage() {
  const [resource, setResource] = useState("languages");
  const [items, setItems] = useState<unknown[]>([]);
  const [json, setJson] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [lessons, setLessons] = useState<LessonDetail[]>([]);
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);
  const [lessonJson, setLessonJson] = useState("");
  const [preview, setPreview] = useState<LessonDetail | null>(null);
  const [exportedJson, setExportedJson] = useState("");
  const [proofFilters, setProofFilters] = useState<AdminProofFilters>({});
  const [proofSubmissions, setProofSubmissions] = useState<AdminProofSubmission[]>([]);
  const [selectedProof, setSelectedProof] = useState<AdminProofSubmission | null>(null);
  const [proofAnalytics, setProofAnalytics] = useState<ProofEvaluationAnalytics | null>(null);
  const [overrideDraft, setOverrideDraft] = useState<AdminProofOverrideRequest>({
    final_status: "needs_review",
    override_note: "",
    score_label: ""
  });

  const sample = useMemo(() => JSON.stringify(samples[resource] ?? {}, null, 2), [resource]);

  useEffect(() => {
    setJson(sample);
  }, [sample]);

  useEffect(() => {
    load();
  }, [resource]);

  useEffect(() => {
    loadLessons();
    loadProofSubmissions();
    loadProofAnalytics();
  }, []);

  async function load() {
    setError(null);
    try {
      setItems(await api.adminList(resource));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load admin resource.");
    }
  }

  async function loadLessons() {
    try {
      const data = (await api.adminList("lessons")) as LessonDetail[];
      setLessons(data);
      setSelectedLessonId((current) => current ?? data[0]?.id ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load lessons.");
    }
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const payload = JSON.parse(json) as Record<string, unknown>;
      await api.adminCreate(resource, payload);
      setMessage("Created.");
      await load();
      if (resource === "lessons") {
        await loadLessons();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed.");
    }
  }

  async function lessonAction(action: "publish" | "archive" | "preview" | "export") {
    if (!selectedLessonId) {
      setError("Select a lesson first.");
      return;
    }
    setError(null);
    setMessage(null);
    try {
      if (action === "publish") {
        await api.adminPublishLesson(selectedLessonId);
        setMessage("Lesson published.");
      }
      if (action === "archive") {
        await api.adminArchiveLesson(selectedLessonId);
        setMessage("Lesson archived.");
      }
      if (action === "preview") {
        setPreview(await api.adminPreviewLesson(selectedLessonId));
        setMessage("Preview loaded.");
      }
      if (action === "export") {
        const exported = await api.adminExportLesson(selectedLessonId);
        setExportedJson(JSON.stringify(exported, null, 2));
        setMessage("Lesson exported.");
      }
      await loadLessons();
      if (resource === "lessons") {
        await load();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lesson action failed.");
    }
  }

  async function importLesson(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    try {
      const payload = JSON.parse(lessonJson) as Record<string, unknown>;
      const lesson = await api.adminImportLesson(payload);
      setMessage(`Imported lesson: ${lesson.title}`);
      setLessonJson("");
      await loadLessons();
      if (resource === "lessons") {
        await load();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed.");
    }
  }

  async function loadProofSubmissions(filters: AdminProofFilters = proofFilters) {
    try {
      const data = await api.adminProofSubmissions(filters);
      setProofSubmissions(data);
      setSelectedProof(data[0] ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load proof submissions.");
    }
  }

  async function loadProofAnalytics() {
    try {
      setProofAnalytics(await api.adminProofEvaluationAnalytics());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load proof analytics.");
    }
  }

  async function applyProofFilters(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSelectedProof(null);
    await loadProofSubmissions(proofFilters);
  }

  function updateProofFilter(key: keyof AdminProofFilters, value: string) {
    setProofFilters((current) => ({ ...current, [key]: value }));
  }

  async function submitOverride(event: FormEvent) {
    event.preventDefault();
    if (!selectedProof) return;
    setError(null);
    setMessage(null);
    try {
      const updated = await api.adminOverrideProofSubmission(selectedProof.id, overrideDraft);
      setSelectedProof(updated);
      setProofSubmissions((current) => current.map((item) => (item.id === updated.id ? updated : item)));
      setMessage("Proof evaluation override saved.");
      setOverrideDraft({ final_status: "needs_review", override_note: "", score_label: "" });
      await loadProofAnalytics();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Override failed.");
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div>
        <p className="text-sm font-medium text-teal">Admin</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">Content base</h1>
      </div>
      <div className="mt-6 flex flex-wrap gap-2">
        {resources.map((item) => (
          <button
            key={item}
            className={`focus-ring h-10 rounded-md px-3 text-sm ${
              resource === item ? "bg-ink text-white" : "border border-line bg-white text-ink"
            }`}
            onClick={() => setResource(item)}
            type="button"
          >
            {item}
          </button>
        ))}
      </div>

      <section className="panel mt-6 p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-teal">Lesson lifecycle</p>
            <select
              className="focus-ring mt-2 h-11 w-full rounded-md border border-line bg-white px-3 text-sm"
              value={selectedLessonId ?? ""}
              onChange={(event) => setSelectedLessonId(Number(event.target.value))}
            >
              {lessons.map((lesson) => (
                <option key={lesson.id} value={lesson.id}>
                  {lesson.title} ({lesson.content_status})
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="focus-ring inline-flex h-10 items-center gap-2 rounded-md bg-teal px-3 text-sm font-medium text-white" onClick={() => lessonAction("publish")} type="button">
              <Send size={16} aria-hidden />
              Publish
            </button>
            <button className="focus-ring inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink" onClick={() => lessonAction("archive")} type="button">
              <Archive size={16} aria-hidden />
              Archive
            </button>
            <button className="focus-ring inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink" onClick={() => lessonAction("preview")} type="button">
              <Eye size={16} aria-hidden />
              Preview
            </button>
            <button className="focus-ring inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-medium text-ink" onClick={() => lessonAction("export")} type="button">
              <FileDown size={16} aria-hidden />
              Export
            </button>
          </div>
        </div>
        {preview ? <LessonPreview lesson={preview} /> : null}
        {exportedJson ? (
          <textarea
            className="focus-ring mt-4 min-h-52 w-full rounded-md border border-line bg-ink p-4 font-mono text-xs leading-5 text-white"
            value={exportedJson}
            onChange={(event) => setExportedJson(event.target.value)}
          />
        ) : null}
      </section>

      <form className="panel mt-6 p-5" onSubmit={importLesson}>
        <div className="flex items-center gap-2">
          <FileUp size={18} className="text-teal" aria-hidden />
          <h2 className="font-semibold text-ink">Import lesson JSON</h2>
        </div>
        <textarea
          className="focus-ring mt-4 min-h-64 w-full rounded-md border border-line bg-ink p-4 font-mono text-sm leading-6 text-white"
          value={lessonJson}
          onChange={(event) => setLessonJson(event.target.value)}
          placeholder="Paste lesson import JSON here"
        />
        <button className="focus-ring mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-teal px-4 text-sm font-medium text-white">
          <FileUp size={16} aria-hidden />
          Import lesson
        </button>
      </form>

      <section className="panel mt-6 p-5">
        <div className="flex items-center gap-2">
          <ShieldCheck size={18} className="text-teal" aria-hidden />
          <h2 className="font-semibold text-ink">Proof submissions</h2>
        </div>
        {proofAnalytics ? <ProofAnalyticsSummary analytics={proofAnalytics} /> : null}
        <form className="mt-4 grid gap-3 md:grid-cols-6" onSubmit={applyProofFilters}>
          <input
            className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm"
            placeholder="User ID"
            value={proofFilters.user_id ?? ""}
            onChange={(event) => updateProofFilter("user_id", event.target.value)}
          />
          <input
            className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm"
            placeholder="Lesson ID"
            value={proofFilters.lesson_id ?? ""}
            onChange={(event) => updateProofFilter("lesson_id", event.target.value)}
          />
          <select
            className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm"
            value={proofFilters.proof_type ?? ""}
            onChange={(event) => updateProofFilter("proof_type", event.target.value)}
          >
            <option value="">Proof type</option>
            <option value="explain_back">Explain-back</option>
            <option value="debug_task">Debug task</option>
            <option value="mini_task">Mini task</option>
            <option value="reflection">Reflection</option>
            <option value="review">Review</option>
          </select>
          <select
            className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm"
            value={proofFilters.status ?? ""}
            onChange={(event) => updateProofFilter("status", event.target.value)}
          >
            <option value="">Status</option>
            <option value="submitted">Submitted</option>
            <option value="needs_revision">Needs revision</option>
            <option value="passed">Passed</option>
            <option value="strong">Strong</option>
          </select>
          <select
            className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm"
            value={proofFilters.score_label ?? ""}
            onChange={(event) => updateProofFilter("score_label", event.target.value)}
          >
            <option value="">Score label</option>
            <option value="incorrect">Incorrect</option>
            <option value="weak">Weak</option>
            <option value="stable">Stable</option>
            <option value="strong">Strong</option>
          </select>
          <button className="focus-ring inline-flex h-10 items-center justify-center gap-2 rounded-md bg-ink px-3 text-sm font-medium text-white">
            <ListFilter size={16} aria-hidden />
            Filter
          </button>
        </form>

        <div className="mt-5 grid gap-4 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="max-h-[420px] overflow-auto rounded-md border border-line bg-paper">
            {proofSubmissions.length ? (
              proofSubmissions.map((proof) => (
                <button
                  key={proof.id}
                  type="button"
                  className={`block w-full border-b border-line px-4 py-3 text-left text-sm ${
                    selectedProof?.id === proof.id ? "bg-teal/10" : "bg-transparent hover:bg-white"
                  }`}
                  onClick={() => setSelectedProof(proof)}
                >
                  <span className="font-medium text-ink">{proof.proof_type.replace("_", " ")}</span>
                  <span className="ml-2 text-ink/55">#{proof.id}</span>
                  <span className="mt-1 block text-xs text-ink/60">
                    {proof.user.email} - {proof.lesson.title}
                  </span>
                  <span className="mt-1 block text-xs text-ink/60">
                    {proof.status} / {proof.score_label ?? "unscored"}
                    {proof.created_review_item ? " - review item created" : ""}
                  </span>
                </button>
              ))
            ) : (
              <p className="p-4 text-sm text-ink/65">No proof submissions found.</p>
            )}
          </div>

          <div className="rounded-md border border-line bg-paper p-4">
            {selectedProof ? (
              <ProofSubmissionDetail
                proof={selectedProof}
                overrideDraft={overrideDraft}
                setOverrideDraft={setOverrideDraft}
                onSubmitOverride={submitOverride}
              />
            ) : (
              <p className="text-sm text-ink/65">Select a proof submission.</p>
            )}
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <form className="panel p-5" onSubmit={submit}>
          <div className="flex items-center gap-2">
            <Plus size={18} className="text-teal" aria-hidden />
            <h2 className="font-semibold text-ink">Create {resource}</h2>
          </div>
          <textarea
            className="focus-ring mt-4 min-h-96 w-full rounded-md border border-line bg-ink p-4 font-mono text-sm leading-6 text-white"
            value={json}
            onChange={(event) => setJson(event.target.value)}
          />
          {error ? <p className="mt-3 text-sm text-berry">{error}</p> : null}
          {message ? <p className="mt-3 text-sm text-moss">{message}</p> : null}
          <button className="focus-ring mt-4 h-10 rounded-md bg-teal px-4 text-sm font-medium text-white">
            Create
          </button>
        </form>

        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <Database size={18} className="text-amber" aria-hidden />
            <h2 className="font-semibold text-ink">Existing {resource}</h2>
          </div>
          <div className="mt-4 max-h-[520px] overflow-auto rounded-md border border-line bg-paper">
            <pre className="p-4 text-xs leading-6 text-ink/75">
              {JSON.stringify(items, null, 2)}
            </pre>
          </div>
        </div>
      </section>
    </div>
  );
}

function ProofAnalyticsSummary({ analytics }: { analytics: ProofEvaluationAnalytics }) {
  return (
    <div className="mt-4 rounded-md border border-line bg-paper p-4">
      <div className="flex items-center gap-2">
        <BarChart3 size={18} className="text-amber" aria-hidden />
        <h3 className="font-semibold text-ink">Evaluation analytics</h3>
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-4">
        <Metric label="Total" value={analytics.total_submissions} />
        <Metric label="Overrides" value={analytics.override_count} />
        <Metric label="Override rate" value={`${Math.round(analytics.override_rate * 100)}%`} />
        <Metric label="Low confidence" value={analytics.count_by_confidence.low ?? 0} />
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <MiniStats title="Final status" values={analytics.count_by_final_status} />
        <MiniStats title="Proof types" values={analytics.count_by_proof_type} />
        <MiniStats title="Confidence" values={analytics.count_by_confidence} />
      </div>
      {analytics.top_lessons_with_rejected_or_needs_review.length ? (
        <div className="mt-4 rounded-md border border-line bg-white p-3">
          <p className="text-sm font-medium text-ink">Top lessons needing review</p>
          <div className="mt-2 grid gap-1 text-sm text-ink/70">
            {analytics.top_lessons_with_rejected_or_needs_review.map((item) => (
              <span key={item.lesson_id}>{item.lesson_title}: {item.count}</span>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <p className="text-xs uppercase text-ink/45">{label}</p>
      <p className="mt-1 text-xl font-semibold text-ink">{value}</p>
    </div>
  );
}

function MiniStats({ title, values }: { title: string; values: Record<string, number> }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <p className="text-sm font-medium text-ink">{title}</p>
      <div className="mt-2 grid gap-1 text-sm text-ink/70">
        {Object.entries(values).length ? (
          Object.entries(values).map(([key, value]) => <span key={key}>{key}: {value}</span>)
        ) : (
          <span>None yet</span>
        )}
      </div>
    </div>
  );
}

function ProofSubmissionDetail({
  proof,
  overrideDraft,
  setOverrideDraft,
  onSubmitOverride
}: {
  proof: AdminProofSubmission;
  overrideDraft: AdminProofOverrideRequest;
  setOverrideDraft: (value: AdminProofOverrideRequest) => void;
  onSubmitOverride: (event: FormEvent) => void;
}) {
  return (
    <div>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-teal">Submission #{proof.id}</p>
          <h3 className="mt-1 text-lg font-semibold text-ink">{proof.proof_type.replace("_", " ")}</h3>
          <p className="mt-1 text-sm text-ink/65">{proof.user.email} - {proof.lesson.title}</p>
        </div>
        <span className="rounded-md border border-line bg-white px-2 py-1 text-xs text-ink/65">
          {proof.final_evaluation_status ?? "unknown"} / {proof.final_score_label ?? "unscored"}
        </span>
      </div>
      <div className="mt-4 grid gap-3 text-sm text-ink/75 md:grid-cols-2">
        <p>Heuristic: {proof.heuristic_status ?? proof.status} / {proof.heuristic_score_label ?? "unscored"}</p>
        <p>Final: {proof.final_evaluation_status ?? "unknown"} / {proof.final_score_label ?? "unscored"}</p>
        <p>Confidence: {proof.evaluation_confidence ?? "unknown"}</p>
        <p>Final score: {proof.final_score_numeric ?? proof.score_numeric ?? "not evaluated"}</p>
        <p>Attempt: {proof.attempt_number}</p>
        <p>Created: {new Date(proof.created_at).toLocaleString()}</p>
        <p>Evaluated: {proof.evaluated_at ? new Date(proof.evaluated_at).toLocaleString() : "not evaluated"}</p>
        <p>Review item: {proof.created_review_item ? proof.review_item_ids.join(", ") : "none"}</p>
        <p>Override: {proof.override_note ? `${proof.override_note} (${proof.overridden_by_email ?? "admin"})` : "none"}</p>
      </div>
      {proof.answer_text ? (
        <div className="mt-4 rounded-md border border-line bg-white p-3">
          <p className="text-xs font-medium uppercase text-ink/45">Answer</p>
          <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink/75">{proof.answer_text}</p>
        </div>
      ) : null}
      {proof.code_text ? (
        <pre className="mt-4 overflow-auto rounded-md bg-ink p-3 text-xs leading-5 text-white">
          <code>{proof.code_text}</code>
        </pre>
      ) : null}
      <div className="mt-4 rounded-md border border-line bg-white p-3">
        <p className="text-xs font-medium uppercase text-ink/45">Heuristic feedback JSON</p>
        <pre className="mt-2 overflow-auto text-xs leading-5 text-ink/75">
          {JSON.stringify(proof.heuristic_feedback_json ?? proof.feedback_json, null, 2)}
        </pre>
      </div>
      <div className="mt-4 rounded-md border border-line bg-white p-3">
        <p className="text-xs font-medium uppercase text-ink/45">Final feedback JSON</p>
        <pre className="mt-2 overflow-auto text-xs leading-5 text-ink/75">
          {JSON.stringify(proof.final_feedback_json ?? proof.feedback_json, null, 2)}
        </pre>
      </div>
      <form className="mt-4 rounded-md border border-line bg-white p-3" onSubmit={onSubmitOverride}>
        <p className="text-sm font-medium text-ink">Admin override</p>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <select
            className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm"
            value={overrideDraft.final_status}
            onChange={(event) => setOverrideDraft({ ...overrideDraft, final_status: event.target.value as AdminProofOverrideRequest["final_status"] })}
          >
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
            <option value="needs_review">Needs review</option>
          </select>
          <select
            className="focus-ring h-10 rounded-md border border-line bg-white px-3 text-sm"
            value={overrideDraft.score_label ?? ""}
            onChange={(event) => setOverrideDraft({ ...overrideDraft, score_label: event.target.value as AdminProofOverrideRequest["score_label"] })}
          >
            <option value="">Score label optional</option>
            <option value="incorrect">Incorrect</option>
            <option value="weak">Weak</option>
            <option value="stable">Stable</option>
            <option value="strong">Strong</option>
          </select>
        </div>
        <textarea
          className="focus-ring mt-3 min-h-24 w-full rounded-md border border-line bg-paper p-3 text-sm"
          value={overrideDraft.override_note}
          onChange={(event) => setOverrideDraft({ ...overrideDraft, override_note: event.target.value })}
          placeholder="Why are you overriding this evaluation?"
        />
        <button className="focus-ring mt-3 h-10 rounded-md bg-ink px-4 text-sm font-medium text-white">
          Save override
        </button>
      </form>
    </div>
  );
}

function LessonPreview({ lesson }: { lesson: LessonDetail }) {
  const quickQuestions = lesson.questions.filter((question) => question.question_type !== "explain_back");
  const explainQuestion = lesson.questions.find((question) => question.question_type === "explain_back");

  return (
    <div className="mt-5 rounded-md border border-line bg-paper p-4">
      <div className="rounded-md border border-line bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-teal">Learner preview</p>
            <h2 className="mt-2 text-2xl font-semibold leading-tight text-ink">{lesson.title}</h2>
            <p className="mt-2 text-sm leading-6 text-ink/70">{lesson.learning_goal}</p>
          </div>
          <span className="rounded-md border border-line bg-paper px-3 py-1 text-xs font-medium text-ink">
            {lesson.content_status}
          </span>
        </div>
        <div className="mt-4 rounded-md border border-line bg-paper p-4 text-sm text-ink/75">
          <span className="font-medium text-ink">Why it matters:</span> {lesson.why_it_matters}
        </div>
      </div>

      <div className="mt-4 grid gap-4">
        {lesson.blocks.map((block) => (
          <LessonBlockRenderer key={block.id} block={block} />
        ))}
      </div>

      <section className="mt-5 grid gap-3">
        <div className="flex items-center gap-2">
          <ClipboardCheck size={18} className="text-teal" aria-hidden />
          <h3 className="font-semibold text-ink">Proof checks</h3>
        </div>
        {quickQuestions.map((question) => (
          <div key={question.id} className="rounded-md border border-line bg-white p-4">
            <p className="text-sm font-medium text-ink">{question.prompt}</p>
            <div className="mt-3 grid gap-2">
              {question.options.map((option) => (
                <div key={option.id} className="rounded-md border border-line bg-paper px-3 py-2 text-sm text-ink/75">
                  <span className="font-medium text-ink">{option.label}.</span> {option.text}
                </div>
              ))}
            </div>
          </div>
        ))}
      </section>

      {explainQuestion ? (
        <section className="mt-5 rounded-md border border-line bg-white p-4">
          <div className="flex items-center gap-2">
            <Lightbulb size={18} className="text-amber" aria-hidden />
            <h3 className="font-semibold text-ink">Explain-back</h3>
          </div>
          <p className="mt-2 text-sm text-ink/70">{explainQuestion.prompt}</p>
          <div className="mt-4 min-h-24 rounded-md border border-line bg-paper" />
        </section>
      ) : null}

      <section className="mt-5 grid gap-4 md:grid-cols-2">
        {lesson.debug_tasks.map((task) => (
          <div key={task.id} className="rounded-md border border-line bg-white p-4">
            <div className="flex items-center gap-2">
              <Bug size={18} className="text-berry" aria-hidden />
              <h3 className="font-semibold text-ink">{task.title}</h3>
            </div>
            <p className="mt-2 text-sm leading-6 text-ink/70">{task.prompt}</p>
            <pre className="mt-3 overflow-x-auto rounded-md bg-ink p-3 text-xs leading-5 text-white">
              <code>{task.broken_code}</code>
            </pre>
          </div>
        ))}
        {lesson.mini_tasks.map((task) => (
          <div key={task.id} className="rounded-md border border-line bg-white p-4">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-moss" aria-hidden />
              <h3 className="font-semibold text-ink">{task.title}</h3>
            </div>
            <p className="mt-2 text-sm leading-6 text-ink/70">{task.prompt}</p>
            {task.acceptance_criteria ? (
              <ul className="mt-3 grid gap-2 text-sm text-ink/70">
                {task.acceptance_criteria.map((item) => (
                  <li key={item} className="flex gap-2">
                    <CheckCircle2 size={15} className="mt-1 text-moss" aria-hidden />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        ))}
      </section>
    </div>
  );
}
