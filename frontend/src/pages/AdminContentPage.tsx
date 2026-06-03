import { Database, Plus } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";

const resources = [
  "languages",
  "tracks",
  "levels",
  "modules",
  "lessons",
  "lesson-blocks",
  "questions",
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
    is_published: true
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
  }
};

export function AdminContentPage() {
  const [resource, setResource] = useState("languages");
  const [items, setItems] = useState<unknown[]>([]);
  const [json, setJson] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const sample = useMemo(() => JSON.stringify(samples[resource] ?? {}, null, 2), [resource]);

  useEffect(() => {
    setJson(sample);
  }, [sample]);

  useEffect(() => {
    load();
  }, [resource]);

  async function load() {
    setError(null);
    try {
      setItems(await api.adminList(resource));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load admin resource.");
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed.");
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
