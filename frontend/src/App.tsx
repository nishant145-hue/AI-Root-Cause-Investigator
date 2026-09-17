import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import Investigation from "./pages/Investigation";
import Investigations from "./pages/Investigations";
import Login from "./pages/Login";
import Notifications from "./pages/Notifications";
import NotFound from "./pages/NotFound";
import Observability from "./pages/Observability";
import Settings from "./pages/Settings";
import Upload from "./pages/Upload";
import ProtectedRoute from "./components/auth/ProtectedRoute";
import CreateInvestigation from "./pages/CreateInvestigation";
import Reports from "./pages/Reports";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route
              path="/"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route path="/dashboard" element={<Dashboard />} />

            <Route
              path="/investigations"
              element={<Investigations />}
            />

            <Route
              path="/investigations/new"
              element={<CreateInvestigation />}
            />

            <Route
              path="/investigations/:investigationId"
              element={<Investigation />}
            />

            <Route
              path="/observability"
              element={<Observability />}
            />

            <Route
              path="/reports"
              element={<Reports />}
            />

            <Route path="/uploads" element={<Upload />} />

            <Route
              path="/notifications"
              element={<Notifications />}
            />

            <Route path="/settings" element={<Settings />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
