export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="panel px-5 py-6">
      <p className="font-medium text-ink">{title}</p>
      <p className="mt-1 text-sm text-ink/65">{body}</p>
    </div>
  );
}
