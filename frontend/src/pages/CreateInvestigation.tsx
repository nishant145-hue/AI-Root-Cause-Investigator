import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createInvestigation } from "../services/investigationApi";

function CreateInvestigation() {
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    setError(null);

    const trimmedTitle = title.trim();
    const trimmedDescription = description.trim();

    if (trimmedTitle.length < 3) {
      setError("Investigation title must be at least 3 characters.");
      return;
    }

    if (trimmedTitle.length > 255) {
      setError("Investigation title cannot exceed 255 characters.");
      return;
    }

    if (trimmedDescription.length > 5000) {
      setError("Description cannot exceed 5000 characters.");
      return;
    }

    setIsSubmitting(true);

    try {
      const investigation = await createInvestigation({
        title: trimmedTitle,
        description: trimmedDescription || null,
      });

      navigate(`/investigations/${investigation.id}`);
    } catch (requestError: unknown) {
      console.error(
        "Failed to create investigation:",
        requestError,
      );

      setError(
        "Unable to create the investigation. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Create Investigation</h1>
          <p>
            Analyze an incident and identify its likely root cause.
          </p>
        </div>
      </div>

      <div className="dashboard-card create-investigation-card">
        <form
          className="investigation-form"
          onSubmit={handleSubmit}
        >
          <div className="form-field">
            <label htmlFor="investigation-title">
              Investigation Title
            </label>

            <input
              id="investigation-title"
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="e.g. Database connection failure"
              maxLength={255}
              disabled={isSubmitting}
              required
            />

            <span className="form-help">
              3–255 characters.
            </span>
          </div>

          <div className="form-field">
            <label htmlFor="investigation-description">
              Description
            </label>

            <textarea
              id="investigation-description"
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              placeholder="Describe the incident, symptoms, errors, affected services, or other useful context..."
              maxLength={5000}
              rows={8}
              disabled={isSubmitting}
            />

            <span className="form-help">
              Optional. Maximum 5000 characters.
            </span>
          </div>

          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}

          <div className="form-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={() => navigate("/investigations")}
              disabled={isSubmitting}
            >
              Cancel
            </button>

            <button
              type="submit"
              className="primary-button"
              disabled={isSubmitting}
            >
              {isSubmitting
                ? "Creating..."
                : "Create Investigation"}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}

export default CreateInvestigation;