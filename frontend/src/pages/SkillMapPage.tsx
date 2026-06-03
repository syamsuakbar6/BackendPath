import { Lock, Unlock } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import { StatusBadge, StrengthBadge } from "../components/StrengthBadge";
import type { Track, TrackDetail } from "../types";

export function SkillMapPage() {
  const [tracks, setTracks] = useState<Track[]>([]);
  const [track, setTrack] = useState<TrackDetail | null>(null);
  const [selectedTrackId, setSelectedTrackId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .tracks()
      .then((items) => {
        setTracks(items);
        setSelectedTrackId(items[0]?.id ?? null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load tracks."));
  }, []);

  useEffect(() => {
    if (!selectedTrackId) return;
    api
      .track(selectedTrackId)
      .then(setTrack)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load track."));
  }, [selectedTrackId]);

  if (error) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-berry">{error}</div>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-medium text-teal">Roadmap</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">Skill map</h1>
        </div>
        {tracks.length ? (
          <select
            className="focus-ring h-11 rounded-md border border-line bg-white px-3 text-sm"
            value={selectedTrackId ?? ""}
            onChange={(event) => setSelectedTrackId(Number(event.target.value))}
          >
            {tracks.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title}
              </option>
            ))}
          </select>
        ) : null}
      </div>

      {track?.recommended_lesson ? (
        <section className="panel mt-6 flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-teal">Next step</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">{track.recommended_lesson.title}</h2>
          </div>
          <Link
            className="focus-ring inline-flex h-10 items-center rounded-md bg-ink px-4 text-sm font-medium text-white"
            to={`/lessons/${track.recommended_lesson.id}`}
          >
            Open lesson
          </Link>
        </section>
      ) : null}

      <div className="mt-6 grid gap-6">
        {track ? (
          track.levels.map((level) => (
            <section key={level.id} className="section-band py-5">
              <div className="mx-auto max-w-6xl">
                <h2 className="text-xl font-semibold text-ink">{level.title}</h2>
                <p className="mt-1 text-sm text-ink/65">{level.description}</p>
                <div className="mt-4 grid gap-4 md:grid-cols-2">
                  {level.modules.map((module) => (
                    <div key={module.id} className="panel p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <Link className="text-lg font-semibold text-ink hover:text-teal" to={`/modules/${module.id}`}>
                            {module.title}
                          </Link>
                          <p className="mt-1 text-sm leading-6 text-ink/65">{module.description}</p>
                        </div>
                        <StrengthBadge strength={module.skill_strength} />
                      </div>
                      <div className="mt-4 h-2 overflow-hidden rounded-full bg-line">
                        <div className="h-full bg-teal" style={{ width: `${module.progress * 100}%` }} />
                      </div>
                      <div className="mt-4 grid gap-2">
                        {module.lessons.map((lesson) => (
                          <Link
                            key={lesson.id}
                            to={lesson.locked ? "#" : `/lessons/${lesson.id}`}
                            className={`flex items-center justify-between gap-3 rounded-md border p-3 text-sm ${
                              lesson.locked
                                ? "cursor-not-allowed border-line bg-paper text-ink/45"
                                : "border-line bg-white text-ink hover:border-teal/40"
                            }`}
                          >
                            <span className="flex items-center gap-2">
                              {lesson.locked ? <Lock size={15} aria-hidden /> : <Unlock size={15} aria-hidden />}
                              {lesson.title}
                            </span>
                            <StatusBadge status={lesson.status} />
                          </Link>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          ))
        ) : (
          <EmptyState title="No track loaded" body="Run the backend seed script to create the sample path." />
        )}
      </div>
    </div>
  );
}
