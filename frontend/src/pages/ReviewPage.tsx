import { CalendarDays, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client";
import { EmptyState } from "../components/EmptyState";
import type { ReviewItem } from "../types";

export function ReviewPage() {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .reviewsDue()
      .then(setReviews)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load reviews."));
  }, []);

  if (error) {
    return <div className="mx-auto max-w-6xl px-4 py-10 text-berry">{error}</div>;
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div>
        <p className="text-sm font-medium text-teal">Review queue</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">Due reviews</h1>
      </div>
      <div className="mt-6 grid gap-4">
        {reviews.length ? (
          reviews.map((review) => (
            <article key={review.id} className="panel p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <RotateCcw size={18} className="text-berry" aria-hidden />
                  <h2 className="font-semibold text-ink">
                    {review.concept ?? review.lesson_title ?? "Review item"}
                  </h2>
                </div>
                <span className="inline-flex items-center gap-2 rounded-md border border-line bg-paper px-2 py-1 text-xs text-ink/65">
                  <CalendarDays size={14} aria-hidden />
                  {new Date(review.due_for_review).toLocaleDateString()}
                </span>
              </div>
              <p className="mt-3 text-sm leading-6 text-ink/70">{review.reason}</p>
              {review.question_prompt ? (
                <p className="mt-3 rounded-md bg-paper p-3 text-sm text-ink/75">{review.question_prompt}</p>
              ) : null}
            </article>
          ))
        ) : (
          <EmptyState title="No reviews due" body="Weak concepts appear here when they reach their review date." />
        )}
      </div>
    </div>
  );
}
