"use client";

import { useEffect, useState } from "react";
import type { JobDocument } from "./documents.model";
import * as documentsService from "./documents.service";

export function useDocuments(jobId: number) {
  const [documents, setDocuments] = useState<JobDocument[]>([]);
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    documentsService.listDocuments(jobId).then(setDocuments);
  }, [jobId]);

  async function upload(files: File[]) {
    setUploading(true);
    const created: JobDocument[] = [];
    for (const file of files) created.push(await documentsService.uploadDocument(jobId, file));
    setDocuments((current) => [...current, ...created]);
    setUploading(false);
  }

  async function remove(document: JobDocument) {
    await documentsService.deleteDocument(document.id);
    setDocuments(documents.filter((item) => item.id !== document.id));
  }

  return { documents, uploading, upload, remove, download: documentsService.downloadDocument };
}
