import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  Bell,
  LayoutDashboard,
  LogOut,
  Search,
  Settings,
  Upload,
} from "lucide-react";

import { useAuth } from "../../context/AuthContext";

const navigation = [
  {
    label: "Dashboard",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Investigations",
    path: "/investigations",
    icon: Search,
  },
  {
    label: "Observability",
    path: "/observability",
    icon: Activity,
  },
  {
    label: "Uploads",
    path: "/uploads",
    icon: Upload,
  },
  {
    label: "Notifications",
    path: "/notifications",
    icon: Bell,
  },
  {
    label: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-brand">
          <div className="app-brand-icon">AI</div>

          <div>
            <strong>Root Cause</strong>
            <span>Investigator</span>
          </div>
        </div>

        <nav className="app-navigation">
          {navigation.map(({ label, path, icon: Icon }) => (
            <NavLink
              key={path}
              to={path}
              className={({ isActive }) =>
                `app-nav-link ${isActive ? "active" : ""}`
              }
            >
              <Icon size={19} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="app-sidebar-footer">
          <span>AI RCA Platform</span>
          <small>Phase 10</small>
        </div>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <div>
            <strong>AI Root Cause Investigator</strong>

            {user && (
              <small className="app-user">
                {user.full_name || user.username}
              </small>
            )}
          </div>

          <div className="app-header-actions">
            <div className="app-header-status">
              <span className="status-dot" />
              System Online
            </div>

            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
              title="Sign out"
            >
              <LogOut size={17} />
              <span>Logout</span>
            </button>
          </div>
        </header>

        <main className="app-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default AppLayout;