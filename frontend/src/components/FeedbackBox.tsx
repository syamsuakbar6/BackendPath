import { CheckCircle2, RotateCcw, XCircle } from "lucide-react";
import type { Feedback } from "../types";

export function FeedbackBox({ feedback }: { feedback: Feedback }) {
  return (
    <div
      className={`mt-4 rounded-md border p-4 ${
        feedback.is_correct ? "border-moss/30 bg-moss/10" : "border-berry/30 bg-berry/10"
      }`}
    >
      <div className="flex items-center gap-2">
        {feedback.is_correct ? (
          <CheckCircle2 size={18} className="text-moss" aria-hidden />
        ) : (
          <XCircle size={18} className="text-berry" aria-hidden />
        )}
        <p className="font-medium text-ink">
          {feedback.is_correct ? "Correct" : "Needs repair"} · score {Math.round(feedback.score * 100)}%
        </p>
      </div>
      <div className="mt-3 grid gap-3 text-sm leading-6 text-ink/76">
        {feedback.what_part_is_wrong ? <p>{feedback.what_part_is_wrong}</p> : null}
        {feedback.why_it_is_wrong ? <p>{feedback.why_it_is_wrong}</p> : null}
        <p>
          <span className="font-medium text-ink">Correct concept:</span>{" "}
          {feedback.correct_concept}
        </p>
        <p>
          <span className="font-medium text-ink">Example:</span> {feedback.simple_example}
        </p>
        <div className="flex items-start gap-2 rounded-md bg-white/70 p-3">
          <RotateCcw size={16} className="mt-1 text-teal" aria-hidden />
          <p>{feedback.remedial_question}</p>
        </div>
      </div>
    </div>
  );
}
