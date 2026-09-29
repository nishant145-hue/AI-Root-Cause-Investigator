import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import {
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";

import "./index.css";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { ApiError } from "./services/api";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (
        failureCount,
        error,
      ) => {
        if (failureCount >= 1) {
          return false;
        }

        if (error instanceof ApiError) {
          if (
            error.status === 400 ||
            error.status === 401 ||
            error.status === 403 ||
            error.status === 404 ||
            error.status === 409 ||
            error.status === 422
          ) {
            return false;
          }

          if (
            error.status === 0 ||
            error.status === 429 ||
            (error.status !== null &&
              error.status >= 500)
          ) {
            return true;
          }
        }

        return true;
      },
      refetchOnWindowFocus: false,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
