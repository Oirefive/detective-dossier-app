import { useState } from "react";

import type { CaseCreatePayload, CaseSummary } from "../types";
import { StatusPill, statusTone } from "./StatusPill";

export function Sidebar({
  view,
  onViewChange,
  cases,
  activeCaseId,
  onSelectCase,
  onCreateCase,
  onDeleteCase,
  onPinCase,
}: {
  view: "cases" | "people";
  onViewChange: (view: "cases" | "people") => void;
  cases: CaseSummary[];
  activeCaseId: string | null;
  onSelectCase: (caseId: string) => void;
  onCreateCase: (payload: CaseCreatePayload) => void | Promise<void>;
  onDeleteCase: (caseId: string) => void | Promise<void>;
  onPinCase: (caseId: string, pinned: boolean) => void | Promise<void>;
}) {
  const [draft, setDraft] = useState<CaseCreatePayload>({
    title: "",
    classification: "Закрытый контур",
    status: "В работе",
    summary: "",
    pinned: false,
  });

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <p className="eyebrow">Локальное приложение</p>
        <h2>Архив расследований</h2>
        <p className="sidebar-copy">Дела, люди, связи и живая доска без браузерной шелухи.</p>
      </div>

      <div className="nav-switch">
        <button className={view === "cases" ? "" : "ghost"} onClick={() => onViewChange("cases")}>
          Дела
        </button>
        <button className={view === "people" ? "" : "ghost"} onClick={() => onViewChange("people")}>
          Люди
        </button>
      </div>

      <div className="sidebar-panel">
        <p className="section-title">Новое дело</p>
        <div className="sidebar-form">
          <input
            placeholder="Название дела"
            value={draft.title}
            onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))}
          />
          <input
            placeholder="Класс"
            value={draft.classification}
            onChange={(event) => setDraft((current) => ({ ...current, classification: event.target.value }))}
          />
          <input
            placeholder="Статус"
            value={draft.status}
            onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value }))}
          />
          <textarea
            rows={3}
            placeholder="Краткая фабула"
            value={draft.summary}
            onChange={(event) => setDraft((current) => ({ ...current, summary: event.target.value }))}
          />
          <label className="check-row">
            <input
              type="checkbox"
              checked={draft.pinned}
              onChange={(event) => setDraft((current) => ({ ...current, pinned: event.target.checked }))}
            />
            <span>Сразу закрепить</span>
          </label>
          <button
            onClick={() => {
              if (!draft.title.trim()) return;
              void onCreateCase(draft);
              setDraft({
                title: "",
                classification: "Закрытый контур",
                status: "В работе",
                summary: "",
                pinned: false,
              });
            }}
          >
            Создать дело
          </button>
        </div>
      </div>

      <div className="sidebar-panel">
        <div className="sidebar-panel__header">
          <p className="section-title">Список дел</p>
          <span>{cases.length}</span>
        </div>
        <div className="case-list">
          {cases.map((item) => (
            <button
              key={item.id}
              className={`case-card ${activeCaseId === item.id ? "case-card--active" : ""}`}
              onClick={() => {
                onViewChange("cases");
                onSelectCase(item.id);
              }}
            >
              <div className="case-card__meta">
                <StatusPill label={item.classification} tone="neutral" />
                <StatusPill label={item.status} tone={statusTone(item.status)} />
              </div>
              <strong>{item.title}</strong>
              <div className="case-card__footer">
                <small>Участников: {item.suspectCount}</small>
                <small>{item.updatedAt}</small>
              </div>
              <div className="card-actions">
                <button
                  type="button"
                  className={`ghost icon-button ${item.pinned ? "pin-active" : ""}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    void onPinCase(item.id, !item.pinned);
                  }}
                  title={item.pinned ? "Открепить дело" : "Закрепить дело"}
                >
                  {item.pinned ? "★" : "☆"}
                </button>
                <button
                  type="button"
                  className="ghost danger icon-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    if (!window.confirm(`Удалить дело «${item.title}»?`)) return;
                    void onDeleteCase(item.id);
                  }}
                  title="Удалить дело"
                >
                  ×
                </button>
              </div>
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
