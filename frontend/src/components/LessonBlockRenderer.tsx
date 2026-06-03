import {
  AlertTriangle,
  CheckCircle2,
  Code2,
  MessageSquare,
  Pencil,
  SearchCode,
  Sparkles,
  XCircle
} from "lucide-react";
import type { LessonBlock } from "../types";

const blockStyles: Record<string, string> = {
  text: "border-line bg-white",
  code: "border-ink/15 bg-ink text-white",
  warning: "border-amber/30 bg-amber/10",
  example_good: "border-moss/30 bg-moss/10",
  example_bad: "border-berry/30 bg-berry/10",
  common_mistake: "border-berry/30 bg-berry/10",
  question: "border-teal/30 bg-teal/10",
  reflection: "border-line bg-white",
  mini_task: "border-amber/30 bg-white",
  debug_task: "border-berry/30 bg-white",
  checklist: "border-moss/30 bg-white"
};

const icons = {
  text: Sparkles,
  code: Code2,
  warning: AlertTriangle,
  example_good: CheckCircle2,
  example_bad: XCircle,
  common_mistake: AlertTriangle,
  question: MessageSquare,
  reflection: Pencil,
  mini_task: Pencil,
  debug_task: SearchCode,
  checklist: CheckCircle2
};

export function LessonBlockRenderer({ block }: { block: LessonBlock }) {
  const Icon = icons[block.block_type];
  const isCode = block.block_type === "code" || block.block_type.includes("example");
  const items = Array.isArray(block.block_metadata?.items)
    ? (block.block_metadata?.items as string[])
    : null;

  return (
    <section className={`rounded-md border p-5 ${blockStyles[block.block_type]}`}>
      <div className="mb-3 flex items-center gap-2">
        <Icon size={18} aria-hidden />
        <h2 className="text-base font-semibold text-current">{block.title}</h2>
      </div>
      {isCode ? (
        <pre className="overflow-x-auto rounded-md bg-ink p-4 text-sm leading-6 text-white">
          <code>{block.body}</code>
        </pre>
      ) : items ? (
        <ul className="grid gap-2 text-sm text-ink/75">
          {items.map((item) => (
            <li key={item} className="flex items-center gap-2">
              <CheckCircle2 size={15} className="text-moss" aria-hidden />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="whitespace-pre-line text-sm leading-7 text-ink/78">{block.body}</p>
      )}
    </section>
  );
}
