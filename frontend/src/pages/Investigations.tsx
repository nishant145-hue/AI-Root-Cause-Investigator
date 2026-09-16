import { useParams } from "react-router-dom";

function Investigation() {
  const { investigationId } = useParams();

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Investigation</h1>
          <p>
            Investigation ID: {investigationId ?? "Unknown"}
          </p>
        </div>
      </div>

      <div className="empty-state">
        <h2>Investigation details</h2>
        <p>
          Investigation execution and AI root cause results will be
          connected in the upcoming investigation phases.
        </p>
      </div>
    </section>
  );
}

export default Investigation;