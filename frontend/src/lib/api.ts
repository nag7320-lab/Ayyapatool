import axios, {
  AxiosError,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from "axios";
import { useAuthStore } from "@/store/auth";
import type { AuthTokens } from "@/types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
});

// Track whether a token refresh is in progress to prevent concurrent refreshes
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
}> = [];

const processQueue = (error: AxiosError | null, token: string | null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// Request interceptor: attach JWT access token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const tokens = useAuthStore.getState().tokens;
    if (tokens?.access_token) {
      config.headers.Authorization = `Bearer ${tokens.access_token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor: handle 401 and refresh tokens
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // If the error is not 401, or the request has already been retried, reject
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // If a refresh is already in progress, queue this request
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${token}`;
          }
          return api(originalRequest);
        })
        .catch((err) => {
          return Promise.reject(err);
        });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const tokens = useAuthStore.getState().tokens;

    if (!tokens?.refresh_token) {
      useAuthStore.getState().logout();
      isRefreshing = false;
      return Promise.reject(error);
    }

    try {
      const response = await axios.post<AuthTokens>(
        `${API_BASE_URL}/auth/refresh`,
        { refresh_token: tokens.refresh_token },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      const newTokens: AuthTokens = response.data;
      useAuthStore.getState().setTokens(newTokens);

      processQueue(null, newTokens.access_token);

      if (originalRequest.headers) {
        originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
      }

      return api(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError as AxiosError, null);
      useAuthStore.getState().logout();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default api;

// Convenience methods for common API patterns
export const apiGet = <T>(url: string, params?: Record<string, unknown>) =>
  api.get<T>(url, { params }).then((res) => res.data);

export const apiPost = <T>(url: string, data?: unknown) =>
  api.post<T>(url, data).then((res) => res.data);

export const apiPut = <T>(url: string, data?: unknown) =>
  api.put<T>(url, data).then((res) => res.data);

export const apiPatch = <T>(url: string, data?: unknown) =>
  api.patch<T>(url, data).then((res) => res.data);

export const apiDelete = <T>(url: string) =>
  api.delete<T>(url).then((res) => res.data);
