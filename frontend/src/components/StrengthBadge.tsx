import type { LessonStatus, SkillStrength } from "../types";

const strengthStyles: Record<SkillStrength, string> = {
  not_started: "border-line bg-white text-ink/60",
  learning: "border-teal/30 bg-teal/10 text-teal",
  weak: "border-berry/30 bg-berry/10 text-berry",
  stable: "border-amber/30 bg-amber/10 text-amber",
  strong: "border-moss/30 bg-moss/10 text-moss"
};

const statusStyles: Record<LessonStatus, string> = {
  not_started: "border-line bg-white text-ink/60",
  in_progress: "border-teal/30 bg-teal/10 text-teal",
  needs_review: "border-berry/30 bg-berry/10 text-berry",
  completed: "border-amber/30 bg-amber/10 text-amber",
  mastered: "border-moss/30 bg-moss/10 text-moss"
};

export function StrengthBadge({ strength }: { strength: SkillStrength }) {
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-medium ${strengthStyles[strength]}`}>
      {strength.replace("_", " ")}
    </span>
  );
}

export function StatusBadge({ status }: { status: LessonStatus }) {
  return (
    <span className={`inline-flex rounded-md border px-2 py-1 text-xs font-medium ${statusStyles[status]}`}>
      {status.replace("_", " ")}
    </span>
  );
}
