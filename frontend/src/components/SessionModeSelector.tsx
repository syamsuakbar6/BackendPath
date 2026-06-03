import { Clock, Hammer, Zap } from "lucide-react";

const modes = [
  { key: "quick", label: "Quick", icon: Zap, minutes: "10-15" },
  { key: "normal", label: "Normal", icon: Clock, minutes: "25-35" },
  { key: "project", label: "Project", icon: Hammer, minutes: "45-90" }
];

export function SessionModeSelector({
  value,
  onChange
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="inline-flex rounded-md border border-line bg-white p-1">
      {modes.map((mode) => (
        <button
          key={mode.key}
          className={`focus-ring inline-flex min-h-10 items-center gap-2 rounded px-3 text-sm ${
            value === mode.key ? "bg-ink text-white" : "text-ink/70 hover:bg-paper"
          }`}
          onClick={() => onChange(mode.key)}
          title={`${mode.label} session, ${mode.minutes} minutes`}
          type="button"
        >
          <mode.icon size={15} aria-hidden />
          <span>{mode.label}</span>
        </button>
      ))}
    </div>
  );
}
