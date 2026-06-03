import { ArrowRight, CheckCircle2, Code2, GitBranch } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";

export function LandingPage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto grid min-h-[calc(100vh-73px)] max-w-6xl items-center gap-10 px-4 py-10 lg:grid-cols-[1.05fr_0.95fr]">
      <section>
        <p className="text-sm font-semibold uppercase tracking-normal text-teal">Backend Mastery System</p>
        <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-ink md:text-5xl">
          Verify backend understanding through proof, practice, and review.
        </h1>
        <p className="mt-5 max-w-2xl text-base leading-7 text-ink/70">
          A focused learning engine for backend developers where completion means demonstrating skill,
          not just reaching the end of a page.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            to={user ? "/dashboard" : "/register"}
            className="focus-ring inline-flex h-11 items-center gap-2 rounded-md bg-ink px-5 text-sm font-medium text-white"
          >
            {user ? "Open dashboard" : "Start learning"}
            <ArrowRight size={16} aria-hidden />
          </Link>
          <Link
            to="/login"
            className="focus-ring inline-flex h-11 items-center rounded-md border border-line bg-white px-5 text-sm font-medium text-ink"
          >
            Log in
          </Link>
        </div>
      </section>

      <section className="panel overflow-hidden">
        <div className="section-band px-5 py-4">
          <div className="flex items-center justify-between">
            <p className="font-semibold text-ink">Python Backend Junior Path</p>
            <span className="rounded-md bg-teal/10 px-2 py-1 text-xs font-medium text-teal">active</span>
          </div>
        </div>
        <div className="grid gap-4 p-5">
          {[
            { icon: Code2, title: "Return values", strength: "learning", color: "text-teal" },
            { icon: GitBranch, title: "Auth vs authorization", strength: "not started", color: "text-amber" },
            { icon: CheckCircle2, title: "401 vs 403", strength: "review later", color: "text-berry" }
          ].map((item) => (
            <div key={item.title} className="flex items-center justify-between rounded-md border border-line bg-paper p-4">
              <div className="flex items-center gap-3">
                <item.icon size={18} className={item.color} aria-hidden />
                <span className="font-medium text-ink">{item.title}</span>
              </div>
              <span className="rounded-md border border-line bg-white px-2 py-1 text-xs text-ink/70">
                {item.strength}
              </span>
            </div>
          ))}
          <div className="rounded-md bg-ink p-4 text-sm leading-6 text-white">
            <code>mastery = reading + quiz + explain_back + debug + mini_task</code>
          </div>
        </div>
      </section>
    </div>
  );
}
