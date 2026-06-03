import {
  Archive,
  Bug,
  CheckCircle2,
  ClipboardCheck,
  Database,
  Eye,
  FileDown,
  FileUp,
  Lightbulb,
  Plus,
  Send
} from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import { LessonBlockRenderer } from "../components/LessonBlockRenderer";
import type { LessonDetail } from "../types";

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

  const sample = useMemo(() => JSON.stringify(samples[resource] ?? {}, null, 2), [resource]);

  useEffect(() => {
    setJson(sample);
  }, [sample]);

  useEffect(() => {
    load();
  }, [resource]);

  useEffect(() => {
    loadLessons();
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
