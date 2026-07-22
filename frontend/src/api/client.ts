import type { AlertItem } from "../types/alert";
import type { FileItem } from "../types/file";


const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";


async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    cache: "no-store",
    ...init,
  });
  if (!response.ok) {
    let message = "Произошла ошибка при обращении к серверу";
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      // Keep the generic message when the server did not return JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}


export function getFiles(): Promise<FileItem[]> {
  return request<FileItem[]>("/files");
}


export function getAlerts(): Promise<AlertItem[]> {
  return request<AlertItem[]>("/alerts");
}


export function uploadFile(title: string, file: File): Promise<FileItem> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);
  return request<FileItem>("/files", { method: "POST", body: formData });
}


export function getDownloadUrl(fileId: string): string {
  return `${API_URL}/files/${fileId}/download`;
}
