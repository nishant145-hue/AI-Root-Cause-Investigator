import {
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../services/api";

interface LoginLocationState {
  from?: {
    pathname?: string;
  };
  registrationSuccess?: string;
}

function Login() {
  const {
    login,
    isAuthenticated,
    isLoading,
  } = useAuth();

  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const locationState =
    location.state as LoginLocationState | null;

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (isLoading) {
    return (
      <div className="page-center">
        <div className="auth-card">
          <div className="app-brand-icon auth-icon">AI</div>
          <h1>AI Root Cause Investigator</h1>
          <p className="muted">
            Restoring your session...
          </p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const redirectPath =
    locationState?.from?.pathname || "/dashboard";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setIsSubmitting(true);

    try {
      await login({
        username,
        password,
      });

      navigate(redirectPath, { replace: true });
    } catch (err: unknown) {
      setError(
        getApiErrorMessage(
          err,
          "Unable to sign in. Please check your credentials.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-center">
      <div className="auth-card">
        <div className="app-brand-icon auth-icon">AI</div>

        <h1>AI Root Cause Investigator</h1>

        <p className="muted">
          Sign in to investigate incidents and identify
          root causes.
        </p>

        {locationState?.registrationSuccess && (
          <div className="auth-success" role="status">
            {locationState.registrationSuccess}
          </div>
        )}

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >
          <label>
            Username
            <input
              type="text"
              value={username}
              onChange={(event) =>
                setUsername(event.target.value)
              }
              placeholder="your username"
              autoComplete="username"
              required
              disabled={isSubmitting}
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="••••••••"
              autoComplete="current-password"
              required
              disabled={isSubmitting}
            />
          </label>

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="primary-button"
            disabled={isSubmitting}
          >
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="auth-note">
          Use your AI Root Cause Investigator account
          credentials.
        </p>

        <div className="auth-signup">
          <span>New to AI Root Cause Investigator?</span>
          <Link to="/register">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  );
}

export default Login;
