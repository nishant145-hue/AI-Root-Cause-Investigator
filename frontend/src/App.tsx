import { useEffect, useState } from "react";
import api from "./services/api";

function App() {
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    api.get("/api/ping")
      .then((response) => {
        setMessage(response.data.message);
      })
      .catch(() => {
        setMessage("Backend connection failed");
      });
  }, []);

  return (
    <div
      style={{
        padding: "40px",
        fontSize: "24px",
        fontFamily: "Arial",
      }}
    >
      <h1>AI Root Cause Investigator</h1>

      <p>{message}</p>
    </div>
  );
}

export default App;