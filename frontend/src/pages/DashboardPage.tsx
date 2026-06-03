import { ArrowRight, BookOpen, CalendarCheck, Gauge, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { SessionModeSelector } from "../components/SessionModeSelector";
import { StatusBadge, StrengthBadge } from "../components/StrengthBadge";
import type { Dashboard } from "../types";

export function DashboardPage() {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [sessionMode, setSessionMode] = useState("quick");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .dashboard()
      .then(setDashboard)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load dashboard."));
  }, []);

  if (error) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-berry">{error}</div>;
  }

  if (!dashboard) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-sm text-ink/65">Loading dashboard...</div>;
  }

  const recommended = dashboard.continue_lesson ?? dashboard.recommended_next_lesson;
  const taskCount = dashboard.session_modes[sessionMode] ?? 2;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-medium text-teal">{dashboard.active_track ?? "No active track"}</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">Learning dashboard</h1>
          <p className="mt-2 text-sm text-ink/65">{dashboard.consistency_label}</p>
        </div>
        <SessionModeSelector value={sessionMode} onChange={setSessionMode} />
      </div>

      <section className="mt-6 grid gap-4 lg:grid-cols-[1.3fr_0.7fr]">
        <div className="panel p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-teal">Recommended next</p>
              {recommended ? (
                <>
                  <h2 className="mt-2 text-xl font-semibold text-ink">{recommended.title}</h2>
                  <p className="mt-2 text-sm leading-6 text-ink/70">{recommended.learning_goal}</p>
                </>
              ) : (
                <p className="mt-2 text-sm text-ink/65">Seed a track to begin.</p>
              )}
            </div>
            {recommended ? <StatusBadge status={recommended.status} /> : null}
          </div>
          {recommended ? (
            <div className="mt-5 flex flex-wrap items-center gap-3">
              <Link
                className="focus-ring inline-flex h-10 items-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white"
                to={`/lessons/${recommended.id}`}
              >
                Open lesson
                <ArrowRight size={16} aria-hidden />
              </Link>
              <span className="text-sm text-ink/65">{taskCount} focused tasks in this session</span>
            </div>
          ) : null}
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <Gauge size={18} className="text-teal" aria-hidden />
            <h2 className="font-semibold text-ink">Current level</h2>
          </div>
          <p className="mt-3 text-2xl font-semibold text-ink">{dashboard.current_level ?? "Not started"}</p>
          <Link className="mt-5 inline-flex text-sm font-medium text-teal" to="/skill-map">
            View skill map
          </Link>
        </div>
      </section>

      <section className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <RotateCcw size={18} className="text-berry" aria-hidden />
            <h2 className="font-semibold text-ink">Weak concepts</h2>
          </div>
          <div className="mt-4 grid gap-3">
            {dashboard.weak_concepts.length ? (
              dashboard.weak_concepts.map((concept) => (
                <div key={concept.concept} className="flex items-center justify-between gap-3">
                  <span className="text-sm text-ink">{concept.concept}</span>
                  <StrengthBadge strength={concept.strength} />
                </div>
              ))
            ) : (
              <p className="text-sm text-ink/65">No weak concepts yet.</p>
            )}
          </div>
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <CalendarCheck size={18} className="text-amber" aria-hidden />
            <h2 className="font-semibold text-ink">Due reviews</h2>
          </div>
          <div className="mt-4 grid gap-3">
            {dashboard.due_reviews.length ? (
              dashboard.due_reviews.slice(0, 4).map((review) => (
                <Link key={review.id} className="text-sm text-teal" to="/reviews">
                  {review.concept ?? review.lesson_title ?? "Review item"}
                </Link>
              ))
            ) : (
              <p className="text-sm text-ink/65">No reviews due right now.</p>
            )}
          </div>
        </div>

        <div className="panel p-5">
          <div className="flex items-center gap-2">
            <BookOpen size={18} className="text-moss" aria-hidden />
            <h2 className="font-semibold text-ink">Skill labels</h2>
          </div>
          <div className="mt-4 grid gap-2">
            {dashboard.mastery_labels.length ? (
              dashboard.mastery_labels.map((label) => (
                <span key={label} className="rounded-md border border-line bg-paper px-3 py-2 text-sm text-ink/75">
                  {label}
                </span>
              ))
            ) : (
              <p className="text-sm text-ink/65">Practice creates skill labels.</p>
            )}
          </div>
        </div>
      </section>

      {!recommended ? (
        <div className="mt-6">
          <EmptyState title="No lesson found" body="Run the seed script or add content through the admin API." />
        </div>
      ) : null}
    </div>
  );
}
