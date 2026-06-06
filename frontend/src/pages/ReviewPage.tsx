import { CalendarDays, CheckCircle2, RotateCcw, Send, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import type { ReviewItem, ReviewSubmissionResponse } from "../types";

interface ReviewDraft {
  answer_text: string;
  code_text: string;
}

export function ReviewPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [drafts, setDrafts] = useState<Record<number, ReviewDraft>>({});
  const [results, setResults] = useState<Record<number, ReviewSubmissionResponse>>({});
  const [submitting, setSubmitting] = useState<Record<number, boolean>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .reviewsDue()
      .then(setReviews)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load reviews."));
  }, []);

  const updateDraft = (reviewId: number, patch: Partial<ReviewDraft>) => {
    setDrafts((current) => ({
      ...current,
      [reviewId]: {
        ...(current[reviewId] ?? { answer_text: "", code_text: "" }),
        ...patch
      }
    }));
  };

  const submitReview = async (review: ReviewItem) => {
    const draft = drafts[review.id] ?? { answer_text: "", code_text: "" };
    setSubmitting((current) => ({ ...current, [review.id]: true }));
    setError(null);
    try {
      const result = await api.submitReview(review.id, {
        answer_text: draft.answer_text,
        code_text: draft.code_text || null
      });
      setResults((current) => ({ ...current, [review.id]: result }));
      setReviews((current) => current.map((item) => (item.id === review.id ? result.review : item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not submit review.");
    } finally {
      setSubmitting((current) => ({ ...current, [review.id]: false }));
    }
  };

  if (error && !reviews.length) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-berry">{error}</div>;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div>
        <p className="text-sm font-medium text-teal">Review queue</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">Due reviews</h1>
      </div>
      {error ? (
        <div className="mt-4 rounded-md border border-berry/25 bg-berry/5 p-3 text-sm text-berry">{error}</div>
      ) : null}
      <div className="mt-6 grid gap-4">
        {reviews.length ? (
          reviews.map((review) => (
            <article key={review.id} className="panel p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <RotateCcw size={18} className="text-berry" aria-hidden />
                  <h2 className="font-semibold text-ink">
                    {review.concept ??
                      review.debug_task_title ??
                      review.mini_task_title ??
                      review.lesson_title ??
                      "Review item"}
                  </h2>
                </div>
                <span className="inline-flex items-center gap-2 rounded-md border border-line bg-paper px-2 py-1 text-xs text-ink/65">
                  <CalendarDays size={14} aria-hidden />
                  {new Date(review.due_for_review).toLocaleDateString()}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-ink/70">{review.reason}</p>
              {review.lesson_title ? (
                <p className="mt-3 text-sm text-ink/60">Lesson: {review.lesson_title}</p>
              ) : null}
              {review.proof_type ? (
                <p className="mt-3 rounded-md bg-paper p-3 text-sm text-ink/75">
                  Proof type: {review.proof_type.replace("_", " ")}
                </p>
              ) : null}
              {review.original_answer_text ? (
                <div className="mt-3 rounded-md border border-line bg-paper p-3">
                  <p className="text-xs font-medium uppercase text-ink/45">Previous weak answer</p>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-ink/75">{review.original_answer_text}</p>
                </div>
              ) : null}
              {review.original_code_text ? (
                <pre className="mt-3 overflow-auto rounded-md bg-ink p-3 text-sm text-white">
                  <code>{review.original_code_text}</code>
                </pre>
              ) : null}
              {review.missing_points.length ? (
                <div className="mt-3 rounded-md border border-berry/25 bg-berry/5 p-3">
                  <p className="text-sm font-medium text-berry">Missing points</p>
                  <ul className="mt-2 grid gap-1 text-sm text-ink/75">
                    {review.missing_points.map((point) => (
                      <li key={point}>{point}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {review.question_prompt ? (
                <p className="mt-3 rounded-md bg-paper p-3 text-sm text-ink/75">{review.question_prompt}</p>
              ) : null}
              {review.debug_task_title || review.mini_task_title ? (
                <p className="mt-3 rounded-md bg-paper p-3 text-sm text-ink/75">
                  Task: {review.debug_task_title ?? review.mini_task_title}
                </p>
              ) : null}
              {review.remedial_question ? (
                <p className="mt-3 rounded-md border border-teal/25 bg-teal/5 p-3 text-sm text-ink/75">
                  {review.remedial_question}
                </p>
              ) : null}

              <div className="mt-4 grid gap-3">
                <textarea
                  className="min-h-28 rounded-md border border-line bg-white p-3 text-sm text-ink outline-none focus:border-teal"
                  value={drafts[review.id]?.answer_text ?? ""}
                  onChange={(event) => updateDraft(review.id, { answer_text: event.target.value })}
                  placeholder="Explain the corrected concept, bug fix, or mini task repair."
                />
                {review.proof_type === "debug_task" || review.proof_type === "mini_task" ? (
                  <textarea
                    className="min-h-24 rounded-md border border-line bg-white p-3 font-mono text-sm text-ink outline-none focus:border-teal"
                    value={drafts[review.id]?.code_text ?? ""}
                    onChange={(event) => updateDraft(review.id, { code_text: event.target.value })}
                    placeholder="Optional code or corrected snippet"
                  />
                ) : null}
                <button
                  type="button"
                  className="focus-ring inline-flex h-10 w-fit items-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                  onClick={() => void submitReview(review)}
                  disabled={Boolean(submitting[review.id])}
                >
                  <Send size={16} aria-hidden />
                  {submitting[review.id] ? "Submitting..." : "Submit review"}
                </button>
              </div>

              {results[review.id] ? <ReviewResult result={results[review.id]} /> : null}
            </article>
          ))
        ) : (
          <EmptyState title="No reviews due" body="Weak concepts appear here when they reach their review date." />
        )}
      </div>
    </div>
  );
}

function ReviewResult({ result }: { result: ReviewSubmissionResponse }) {
  const Icon = result.passed ? CheckCircle2 : XCircle;
  const tone = result.passed ? "border-moss/25 bg-moss/5 text-moss" : "border-berry/25 bg-berry/5 text-berry";
  return (
    <div className={`mt-4 rounded-md border p-4 ${tone}`}>
      <div className="flex items-center gap-2">
        <Icon size={18} aria-hidden />
        <p className="font-semibold">
          {result.passed ? "Review repaired" : "Still needs repair"} - {Math.round(result.score_numeric * 100)}%
        </p>
      </div>
      <p className="mt-2 text-sm leading-6 text-ink/75">{result.feedback_json.feedback}</p>
      {result.feedback_json.correct_points.length ? (
        <p className="mt-3 text-sm text-ink/75">
          Correct: {result.feedback_json.correct_points.join(", ")}
        </p>
      ) : null}
      {result.feedback_json.missing_points.length ? (
        <p className="mt-3 text-sm text-ink/75">
          Missing: {result.feedback_json.missing_points.join(", ")}
        </p>
      ) : null}
      <p className="mt-3 rounded-md bg-white/70 p-3 text-sm text-ink/75">{result.feedback_json.remedial_question}</p>
      {result.next_due_for_review ? (
        <p className="mt-3 text-sm text-ink/65">
          Next reinforcement: {new Date(result.next_due_for_review).toLocaleDateString()}
        </p>
      ) : result.passed ? (
        <p className="mt-3 text-sm text-ink/65">No immediate review required.</p>
      ) : null}
    </div>
  );
}
