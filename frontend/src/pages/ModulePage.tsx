import { ArrowRight } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { StatusBadge, StrengthBadge } from "../components/StrengthBadge";
import type { ModuleMap } from "../types";

export function ModulePage() {
  const { id } = useParams();
  const [module, setModule] = useState<ModuleMap | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api
      .module(Number(id))
      .then(setModule)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load module."));
  }, [id]);

  if (error) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-berry">{error}</div>;
  }

  if (!module) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-ink/65">Loading module...</div>;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-teal">Module</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">{module.title}</h1>
          <p className="mt-2 text-sm leading-6 text-ink/70">{module.description}</p>
        </div>
        <StrengthBadge strength={module.skill_strength} />
      </div>
      <div className="mt-6 h-2 overflow-hidden rounded-full bg-line">
        <div className="h-full bg-teal" style={{ width: `${module.progress * 100}%` }} />
      </div>
      <div className="mt-6 grid gap-3">
        {module.lessons.map((lesson) => (
          <Link key={lesson.id} className="panel flex items-center justify-between gap-4 p-4" to={`/lessons/${lesson.id}`}>
            <div>
              <p className="font-medium text-ink">{lesson.title}</p>
              <p className="mt-1 text-sm text-ink/65">{lesson.learning_goal}</p>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge status={lesson.status} />
              <ArrowRight size={16} className="text-teal" aria-hidden />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
