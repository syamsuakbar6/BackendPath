import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("learner@example.com");
  const [password, setPassword] = useState("learner123");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-73px)] max-w-md items-center px-4 py-10">
      <form className="panel w-full p-6" onSubmit={submit}>
        <h1 className="text-2xl font-semibold text-ink">Log in</h1>
        <div className="mt-6 grid gap-4">
          <label className="grid gap-2 text-sm font-medium text-ink">
            Email
            <input
              className="focus-ring h-11 rounded-md border border-line bg-white px-3 font-normal"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              type="email"
            />
          </label>
          <label className="grid gap-2 text-sm font-medium text-ink">
            Password
            <input
              className="focus-ring h-11 rounded-md border border-line bg-white px-3 font-normal"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              type="password"
            />
          </label>
        </div>
        {error ? <p className="mt-4 text-sm text-berry">{error}</p> : null}
        <button
          className="focus-ring mt-6 h-11 w-full rounded-md bg-ink px-4 text-sm font-medium text-white disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "Logging in" : "Log in"}
        </button>
        <p className="mt-4 text-sm text-ink/65">
          New here?{" "}
          <Link className="font-medium text-teal" to="/register">
            Create an account
          </Link>
        </p>
      </form>
    </div>
  );
}
