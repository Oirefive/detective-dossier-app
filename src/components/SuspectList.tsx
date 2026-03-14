import { useMemo, useState } from "react";

import type { CaseParticipant } from "../types";
import { StatusPill, statusTone } from "./StatusPill";

export function CaseParticipantsPanel({
  caseTitle,
  participants,
  activeParticipantId,
  onSelectParticipant,
  onPinParticipant,
}: {
  caseTitle: string;
  participants: CaseParticipant[];
  activeParticipantId: string | null;
  onSelectParticipant: (id: string) => void;
  onPinParticipant: (id: string, pinned: boolean) => void;
}) {
  const [filter, setFilter] = useState("");
  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return participants;
    return participants.filter((item) =>
      [item.fullName, item.aliasName, item.role, item.location].join(" ").toLowerCase().includes(query)
    );
  }, [filter, participants]);

  return (
    <section className="panel panel--compact">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Участники дела</p>
          <h2>{caseTitle}</h2>
        </div>
      </div>
      <input
        className="search-input"
        placeholder="Фильтр по участникам"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
      />
      <div className="participant-list">
        {filtered.map((item) => (
          <button
            key={item.id}
            className={`participant-card ${activeParticipantId === item.id ? "participant-card--active" : ""}`}
            onClick={() => onSelectParticipant(item.id)}
          >
            <div className="participant-card__header">
              <strong>{item.fullName}</strong>
              <div className="tag-row">
                <StatusPill label={`${item.suspicionLevel}%`} tone={statusTone(item.status, item.suspicionLevel)} />
                {item.pinned ? <StatusPill label="Верх" tone="success" /> : null}
              </div>
            </div>
            <p>{item.aliasName || "Без псевдонима"}</p>
            <small>{item.role || "Роль не указана"}</small>
            <small>{item.location || "Локация не указана"}</small>
            <div className="card-actions">
              <button
                type="button"
                className={`ghost icon-button ${item.pinned ? "pin-active" : ""}`}
                onClick={(event) => {
                  event.stopPropagation();
                  void onPinParticipant(item.id, !item.pinned);
                }}
              >
                {item.pinned ? "★" : "☆"}
              </button>
            </div>
          </button>
        ))}
        {!filtered.length ? <div className="empty-inline">В этом деле пока нет участников.</div> : null}
      </div>
    </section>
  );
}
