import api from "./api";

export interface Upload {
  id: number;
  filename: string;
  content_type: string;
  size: number;
  parsed_logs: number;
  status: string;
  uploaded_at: string;
}

export interface UploadResponse extends Upload {
  saved_as: string;
  file_path: string;
  message: string;
}

export const getUploads = async (): Promise<Upload[]> => {
  const response = await api.get<Upload[]>("/api/v1/uploads");

  return response.data;
};

export const uploadLog = async (
  file: File,
): Promise<UploadResponse> => {
  const formData = new FormData();

  formData.append("file", file);

  const response = await api.post<UploadResponse>(
    "/api/v1/uploads",
    formData,
  );

  return response.data;
};