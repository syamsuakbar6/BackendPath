import { Send } from "lucide-react";
import { useState } from "react";
import { api } from "../api/client";
import type { Feedback, LessonProgress, Question } from "../types";
import { FeedbackBox } from "./FeedbackBox";

export function QuestionInteraction({
  question,
  onProgress
}: {
  question: Question;
  onProgress?: (progress: LessonProgress) => void;
}) {
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isChoice = question.question_type === "multiple_choice";

  async function submit() {
    if (!answer.trim()) {
      setError("Choose or enter an answer first.");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const response = await api.answerQuestion(question.id, answer);
      setFeedback(response.feedback);
      if (response.lesson_progress) {
        onProgress?.(response.lesson_progress);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit answer.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="panel p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase text-teal">{question.question_type.replace("_", " ")}</p>
          <h3 className="mt-1 text-base font-semibold text-ink">{question.prompt}</h3>
        </div>
        <span className="rounded-md border border-line bg-paper px-2 py-1 text-xs text-ink/65">
          {question.difficulty}
        </span>
      </div>

      {isChoice ? (
        <div className="mt-4 grid gap-2">
          {question.options.map((option) => (
            <label
              key={option.id}
              className={`flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm ${
                answer === option.label
                  ? "border-teal bg-teal/10"
                  : "border-line bg-white hover:border-teal/40"
              }`}
            >
              <input
                className="mt-1"
                type="radio"
                name={`question-${question.id}`}
                value={option.label}
                checked={answer === option.label}
                onChange={(event) => setAnswer(event.target.value)}
              />
              <span>
                <span className="font-medium text-ink">{option.label}.</span> {option.text}
              </span>
            </label>
          ))}
        </div>
      ) : (
        <textarea
          className="focus-ring mt-4 min-h-28 w-full rounded-md border border-line bg-white p-3 text-sm"
          value={answer}
          onChange={(event) => setAnswer(event.target.value)}
        />
      )}

      {error ? <p className="mt-3 text-sm text-berry">{error}</p> : null}
      <button
        className="focus-ring mt-4 inline-flex h-10 items-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white disabled:opacity-60"
        onClick={submit}
        disabled={submitting}
        type="button"
      >
        <Send size={16} aria-hidden />
        {submitting ? "Submitting" : "Submit"}
      </button>
      {feedback ? <FeedbackBox feedback={feedback} /> : null}
    </div>
  );
}
