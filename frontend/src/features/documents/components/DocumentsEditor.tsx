"use client";

import { useRef, type ChangeEvent } from "react";
import { useI18n } from "@/shared/lib/i18n";
import { UploadIcon } from "@/shared/components/icons";
import { useDocuments } from "../documents.controller";

export function DocumentsEditor({ jobId }: { jobId: number }) {
  const { t } = useI18n();
  const { documents, uploading, upload, remove, download } = useDocuments(jobId);
  const fileInput = useRef<HTMLInputElement>(null);

  async function onFilesChosen(event: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(event.target.files ?? []);
    if (files.length > 0) await upload(files);
    event.target.value = "";
  }

  return (
    <div className="list-editor">
      {documents.length === 0 && <span className="muted">{t("documents.empty")}</span>}
      {documents.map((document) => (
        <div key={document.id} className="list-item">
          <button type="button" className="link-button list-item-name" onClick={() => download(document)}>
            {document.filename}
          </button>
          <button type="button" className="icon-button" onClick={() => remove(document)}>×</button>
        </div>
      ))}
      <input ref={fileInput} type="file" multiple hidden onChange={onFilesChosen} />
      <button
        type="button"
        className="button button-light button-small"
        disabled={uploading}
        onClick={() => fileInput.current?.click()}
      >
        <UploadIcon />
        {t("documents.upload")}
      </button>
    </div>
  );
}
