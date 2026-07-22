"use client";

import { useCallback, useEffect, useState } from "react";

import { getAlerts, getFiles, uploadFile } from "../api/client";
import type { AlertItem } from "../types/alert";
import type { FileItem } from "../types/file";


export function useFileDashboard() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [filesData, alertsData] = await Promise.all([getFiles(), getAlerts()]);
      setFiles(filesData);
      setAlerts(alertsData);
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  async function submitFile(title: string, file: File): Promise<boolean> {
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await uploadFile(title.trim(), file);
      await loadData();
      return true;
    } catch (error) {
      setErrorMessage(toErrorMessage(error));
      return false;
    } finally {
      setIsSubmitting(false);
    }
  }

  return {
    files,
    alerts,
    isLoading,
    isSubmitting,
    errorMessage,
    loadData,
    submitFile,
  };
}


function toErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Произошла ошибка";
}
