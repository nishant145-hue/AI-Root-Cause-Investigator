import api from "./api";

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string | null;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export const login = async (
  credentials: LoginRequest,
): Promise<TokenResponse> => {
  const body = new URLSearchParams();

  body.set("username", credentials.username);
  body.set("password", credentials.password);
  body.set("grant_type", "password");

  const response = await api.post<TokenResponse>(
    "/api/v1/auth/login",
    body,
    {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    },
  );

  return response.data;
};

export const register = async (
  data: RegisterRequest,
): Promise<User> => {
  const response = await api.post<User>(
    "/api/v1/auth/register",
    data,
  );

  return response.data;
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await api.get<User>("/api/v1/auth/me");
  return response.data;
};

export const refreshToken = async (
  data: RefreshTokenRequest,
): Promise<TokenResponse> => {
  const response = await api.post<TokenResponse>(
    "/api/v1/auth/refresh",
    data,
  );

  return response.data;
};

export const logout = async (
  refreshToken: string,
): Promise<void> => {
  await api.post("/api/v1/auth/logout", {
    refresh_token: refreshToken,
  });
};