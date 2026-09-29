import {
  useState,
  type FormEvent,
} from "react";
import {
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getApiErrorMessage } from "../services/api";
import {
  register,
  type RegisterRequest,
} from "../services/authApi";

function Register() {
  const {
    isAuthenticated,
    isLoading,
  } = useAuth();

  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  if (isLoading) {
    return (
      <div className="page-center">
        <div className="auth-card">
          <div className="app-brand-icon auth-icon">
            AI
          </div>

          <h1>AI Root Cause Investigator</h1>

          <p className="muted">
            Checking your session...
          </p>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");

    const trimmedFullName = fullName.trim();
    const trimmedUsername = username.trim();
    const trimmedEmail = email.trim();

    if (
      trimmedUsername.length < 3 ||
      trimmedUsername.length > 50
    ) {
      setError(
        "Username must be between 3 and 50 characters.",
      );
      return;
    }

    if (
      !/^[a-zA-Z0-9_.-]+$/.test(trimmedUsername)
    ) {
      setError(
        "Username can contain only letters, numbers, underscores, dots, and hyphens.",
      );
      return;
    }

    if (!trimmedEmail) {
      setError("Please enter your email address.");
      return;
    }

    if (password.length < 8 || password.length > 128) {
      setError(
        "Password must be between 8 and 128 characters.",
      );
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    const data: RegisterRequest = {
      username: trimmedUsername,
      email: trimmedEmail,
      password,
      full_name: trimmedFullName || null,
    };

    setIsSubmitting(true);

    try {
      await register(data);

      navigate("/login", {
        replace: true,
        state: {
          registrationSuccess:
            "Account created successfully. Please sign in.",
        },
      });
    } catch (err: unknown) {
      setError(
        getApiErrorMessage(
          err,
          "Unable to create your account. Please check your information and try again.",
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="page-center">
      <div className="auth-card">
        <div className="app-brand-icon auth-icon">
          AI
        </div>

        <h1>Create your account</h1>

        <p className="muted">
          Create an AI Root Cause Investigator account
          to investigate incidents and identify root
          causes.
        </p>

        <form
          onSubmit={handleSubmit}
          className="auth-form"
        >
          <label>
            Full name
            <input
              type="text"
              value={fullName}
              onChange={(event) =>
                setFullName(event.target.value)
              }
              placeholder="Your full name"
              autoComplete="name"
              maxLength={255}
              disabled={isSubmitting}
            />
          </label>

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
              minLength={3}
              maxLength={50}
              required
              disabled={isSubmitting}
            />
          </label>

          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="you@example.com"
              autoComplete="email"
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
              placeholder="At least 8 characters"
              autoComplete="new-password"
              minLength={8}
              maxLength={128}
              required
              disabled={isSubmitting}
            />
          </label>

          <label>
            Confirm password
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(event.target.value)
              }
              placeholder="Enter your password again"
              autoComplete="new-password"
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
            {isSubmitting
              ? "Creating account..."
              : "Create account"}
          </button>
        </form>

        <p className="auth-note">
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
