import { BookOpen, LayoutDashboard, LogOut, Map, Search, Settings } from "lucide-react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/skill-map", label: "Skill Map", icon: Map },
  { to: "/reviews", label: "Reviews", icon: BookOpen },
  { to: "/search", label: "Search", icon: Search }
];

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-paper/92 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <Link to={user ? "/dashboard" : "/"} className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-md bg-ink text-sm font-semibold text-white">
              BM
            </div>
            <div>
              <p className="text-base font-semibold text-ink">Backend Mastery System</p>
              <p className="text-xs text-ink/60">Skill-based backend learning</p>
            </div>
          </Link>
          {user ? (
            <div className="flex flex-wrap items-center gap-2">
              <nav className="flex flex-wrap items-center gap-1">
                {navItems.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    className={({ isActive }) =>
                      `focus-ring inline-flex h-10 items-center gap-2 rounded-md px-3 text-sm ${
                        isActive
                          ? "bg-teal text-white"
                          : "text-ink/70 hover:bg-white hover:text-ink"
                      }`
                    }
                  >
                    <item.icon size={16} aria-hidden />
                    {item.label}
                  </NavLink>
                ))}
                {user.role === "admin" ? (
                  <NavLink
                    to="/admin"
                    className={({ isActive }) =>
                      `focus-ring inline-flex h-10 items-center gap-2 rounded-md px-3 text-sm ${
                        isActive
                          ? "bg-teal text-white"
                          : "text-ink/70 hover:bg-white hover:text-ink"
                      }`
                    }
                  >
                    <Settings size={16} aria-hidden />
                    Admin
                  </NavLink>
                ) : null}
              </nav>
              <button
                className="focus-ring inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm text-ink hover:border-ink/30"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
                title="Log out"
              >
                <LogOut size={16} aria-hidden />
                <span>Log out</span>
              </button>
            </div>
          ) : null}
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
