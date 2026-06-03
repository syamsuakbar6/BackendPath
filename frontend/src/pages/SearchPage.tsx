import { Search } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { SearchResponse, SearchResultItem } from "../types";

const groups: Array<[keyof SearchResponse, string]> = [
  ["lessons", "Lessons"],
  ["questions", "Questions"],
  ["debug_tasks", "Debug tasks"],
  ["mini_tasks", "Mini tasks"],
  ["modules", "Modules"],
  ["tracks", "Tracks"]
];

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      setResults(await api.search(query));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed.");
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div>
        <p className="text-sm font-medium text-teal">Search</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">Find concepts and practice</h1>
      </div>
      <form className="panel mt-6 flex gap-2 p-3" onSubmit={submit}>
        <input
          className="focus-ring h-11 flex-1 rounded-md border border-line bg-white px-3 text-sm"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Try return, auth, 401"
        />
        <button className="focus-ring inline-flex h-11 items-center gap-2 rounded-md bg-ink px-4 text-sm font-medium text-white">
          <Search size={16} aria-hidden />
          Search
        </button>
      </form>
      {error ? <p className="mt-4 text-sm text-berry">{error}</p> : null}
      {results ? (
        <div className="mt-6 grid gap-6">
          {groups.map(([key, title]) => (
            <ResultGroup key={key} title={title} items={results[key] as SearchResultItem[]} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function ResultGroup({ title, items }: { title: string; items: SearchResultItem[] }) {
  if (!items.length) return null;

  return (
    <section>
      <h2 className="text-lg font-semibold text-ink">{title}</h2>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {items.map((item) => {
          const target =
            item.type === "lesson"
              ? `/lessons/${item.id}`
              : item.type === "module"
                ? `/modules/${item.id}`
                : "/search";
          return (
            <Link key={`${item.type}-${item.id}`} className="panel p-4 hover:border-teal/40" to={target}>
              <p className="font-medium text-ink">{item.title}</p>
              {item.description ? <p className="mt-1 line-clamp-2 text-sm text-ink/65">{item.description}</p> : null}
              {item.parent ? <p className="mt-3 text-xs font-medium text-teal">{item.parent}</p> : null}
            </Link>
          );
        })}
      </div>
    </section>
  );
}
