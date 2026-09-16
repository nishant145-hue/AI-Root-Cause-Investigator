import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { getUploads, uploadLog } from "../services/uploadApi";

function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function getErrorMessage(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error
  ) {
    const response = (
      error as {
        response?: {
          data?: {
            detail?: string;
          };
        };
      }
    ).response;

    if (response?.data?.detail) {
      return response.data.detail;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong while uploading the file.";
}

function Upload() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState("");

  const {
    data: uploads = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["uploads"],
    queryFn: getUploads,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadLog(file),

    onSuccess: () => {
      setSelectedFile(null);
      setUploadError("");

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      queryClient.invalidateQueries({
        queryKey: ["uploads"],
      });
    },

    onError: (error: unknown) => {
      setUploadError(getErrorMessage(error));
    },
  });

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = event.target.files?.[0] ?? null;

    setSelectedFile(file);
    setUploadError("");
  };

  const handleUpload = () => {
    if (!selectedFile || uploadMutation.isPending) {
      return;
    }

    setUploadError("");
    uploadMutation.mutate(selectedFile);
  };

  return (
    <section className="page">
      <div className="page-heading">
        <div>
          <h1>Uploads</h1>
          <p>
            Upload logs and evidence for root cause investigation.
          </p>
        </div>
      </div>

      <div className="upload-card">
        <div className="upload-card-heading">
          <div>
            <h2>Upload log file</h2>
            <p>
              Select a log file to parse and make available for AI
              investigation.
            </p>
          </div>
        </div>

        <div className="upload-controls">
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
          />

          <button
            type="button"
            className="primary-button"
            onClick={handleUpload}
            disabled={!selectedFile || uploadMutation.isPending}
          >
            {uploadMutation.isPending
              ? "Uploading..."
              : "Upload Log"}
          </button>
        </div>

        {selectedFile && (
          <div className="selected-file">
            <strong>{selectedFile.name}</strong>
            <span>{formatFileSize(selectedFile.size)}</span>
          </div>
        )}

        {uploadMutation.isSuccess && (
          <div className="success-message">
            File uploaded and parsed successfully.
          </div>
        )}

        {uploadError && (
          <div className="error-message">
            {uploadError}
          </div>
        )}
      </div>

      <div className="upload-card">
        <div className="upload-card-heading">
          <div>
            <h2>Uploaded logs</h2>
            <p>
              These logs are available to use in investigations.
            </p>
          </div>

          <button
            type="button"
            className="secondary-button"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            Refresh
          </button>
        </div>

        {isLoading && (
          <div className="upload-message">
            Loading uploaded logs...
          </div>
        )}

        {isError && (
          <div className="error-message">
            {getErrorMessage(error)}
          </div>
        )}

        {!isLoading && !isError && uploads.length === 0 && (
          <div className="upload-empty-state">
            <h3>No uploaded logs</h3>
            <p>
              Upload a log file above to make it available for an
              investigation.
            </p>
          </div>
        )}

        {!isLoading && !isError && uploads.length > 0 && (
          <div className="upload-list">
            {uploads.map((upload) => (
              <div className="upload-item" key={upload.id}>
                <div className="upload-item-main">
                  <div className="upload-item-title">
                    {upload.filename}
                  </div>

                  <div className="upload-item-meta">
                    <span>ID: {upload.id}</span>
                    <span>
                      {upload.parsed_logs} parsed logs
                    </span>
                    <span>
                      {formatFileSize(upload.size)}
                    </span>
                    <span>{upload.status}</span>
                  </div>
                </div>

                <div className="upload-item-date">
                  {formatDate(upload.uploaded_at)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default Upload;