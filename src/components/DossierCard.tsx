import { useEffect, useState } from "react";

import type {
  AIDossierResponse,
  CaseParticipant,
  Dossier,
  EvidenceCreatePayload,
  EventCreatePayload,
  RelationCreatePayload,
} from "../types";
import { DestinyMatrixPanel } from "./DestinyMatrixPanel";
import { PhotoUploadField } from "./PhotoUploadField";
import { StatusPill, statusTone } from "./StatusPill";

type TabId = "profile" | "materials" | "links" | "esoteric";

function blankEvidence(): EvidenceCreatePayload {
  return { title: "", category: "", status: "", details: "" };
}

function blankEvent(): EventCreatePayload {
  return { eventDate: "", title: "", details: "" };
}

function blankRelation(): RelationCreatePayload {
  return { targetType: "", targetLabel: "", relationType: "", confidence: 50 };
}

function ageFromBirthDate(value: string | null): number | null {
  if (!value) return null;
  const birth = new Date(value);
  if (Number.isNaN(birth.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) age -= 1;
  return age >= 0 ? age : null;
}

export function DossierCard({
  dossier,
  draft,
  onChange,
  onSave,
  onPin,
  onGeneratePdf,
  onGenerateBoardPdf,
  onUploadPhoto,
  onPersistPhoto,
  onAddEvidence,
  onDeleteEvidence,
  onAddEvent,
  onDeleteEvent,
  onAddRelation,
  onDeleteRelation,
  photoUploading,
  onGenerateAIDossier,
  aiBusy,
}: {
  dossier: Dossier | null;
  draft: CaseParticipant | null;
  onChange: (patch: Partial<CaseParticipant>) => void;
  onSave: () => void;
  onPin: (pinned: boolean) => void;
  onGeneratePdf: () => void;
  onGenerateBoardPdf: () => void;
  onUploadPhoto: (file: File) => Promise<string>;
  onPersistPhoto: (path: string | null) => Promise<void>;
  onAddEvidence: (payload: EvidenceCreatePayload) => void | Promise<void>;
  onDeleteEvidence: (id: string) => void | Promise<void>;
  onAddEvent: (payload: EventCreatePayload) => void | Promise<void>;
  onDeleteEvent: (id: string) => void | Promise<void>;
  onAddRelation: (payload: RelationCreatePayload) => void | Promise<void>;
  onDeleteRelation: (id: string) => void | Promise<void>;
  photoUploading: boolean;
  onGenerateAIDossier: () => Promise<AIDossierResponse>;
  aiBusy: boolean;
}) {
  const [activeTab, setActiveTab] = useState<TabId>("profile");
  const [evidenceDraft, setEvidenceDraft] = useState<EvidenceCreatePayload>(blankEvidence());
  const [eventDraft, setEventDraft] = useState<EventCreatePayload>(blankEvent());
  const [relationDraft, setRelationDraft] = useState<RelationCreatePayload>(blankRelation());
  const [aiDossier, setAiDossier] = useState<AIDossierResponse | null>(null);

  useEffect(() => {
    setEvidenceDraft(blankEvidence());
    setEventDraft(blankEvent());
    setRelationDraft(blankRelation());
    setAiDossier(null);
  }, [dossier?.participant.id]);

  if (!dossier || !draft) {
    return (
      <section className="panel empty-state">
        <h2>Карточка участника не выбрана</h2>
        <p>Выберите участника справа или откройте его из глобального поиска.</p>
      </section>
    );
  }

  const tabs: Array<{ id: TabId; label: string }> = [
    { id: "profile", label: "Профиль" },
    { id: "materials", label: "Материалы" },
    { id: "links", label: "Связи" },
    { id: "esoteric", label: "Эзотерика" },
  ];

  return (
    <section className="panel dossier-card">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Карточка участника</p>
          <h2>{draft.fullName}</h2>
          <p className="panel-copy">
            {dossier.case.title} · {dossier.case.classification}
          </p>
        </div>
        <div className="actions">
          <button className={`ghost ${draft.pinned ? "pin-active" : ""}`} onClick={() => onPin(!draft.pinned)}>
            {draft.pinned ? "Открепить" : "Закрепить"}
          </button>
          <button className="ghost" onClick={onSave}>
            Сохранить
          </button>
        </div>
      </div>

      <section className="print-strip">
        <div>
          <p className="eyebrow">Печать и экспорт</p>
          <h3>Готовые материалы по текущему участнику</h3>
          <p className="panel-copy">Сначала сохраните карточку, потом печатайте досье или доску расследования.</p>
        </div>
        <div className="actions">
          <button className="ghost" onClick={onGeneratePdf}>
            PDF: Досье
          </button>
          <button onClick={onGenerateBoardPdf}>PDF: Доска</button>
        </div>
      </section>

      <div className="dossier-header-grid">
        <PhotoUploadField
          compact
          label="Фото участника"
          value={draft.photoPath}
          onUpload={async (file) => {
            const path = await onUploadPhoto(file);
            onChange({ photoPath: path });
            await onPersistPhoto(path);
          }}
          onClear={() => {
            onChange({ photoPath: null });
            void onPersistPhoto(null);
          }}
          uploading={photoUploading}
        />
        <article className="summary-card summary-card--identity">
          <div className="summary-card__block">
            <span className="eyebrow">Статус</span>
            <h3>{draft.status || "Без статуса"}</h3>
            <StatusPill label={`${draft.suspicionLevel}%`} tone={statusTone(draft.status, draft.suspicionLevel)} />
          </div>
          <div className="summary-card__block">
            <span className="eyebrow">Роль</span>
            <h3>{draft.role || "Участник"}</h3>
            <p>{draft.location || "Локация не указана"}</p>
          </div>
        </article>
      </div>

      <div className="tab-row">
        {tabs.map((tab) => (
          <button key={tab.id} className={`tab-button ${activeTab === tab.id ? "tab-button--active" : "ghost"}`} onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "profile" ? (
        <div className="dossier-tab">
          <div className="compact-grid compact-grid--identity compact-grid--dossier">
            <label className="field">
              <span>ФИО</span>
              <input value={draft.fullName} onChange={(event) => onChange({ fullName: event.target.value })} />
            </label>
            <label className="field">
              <span>Псевдоним</span>
              <input value={draft.aliasName} onChange={(event) => onChange({ aliasName: event.target.value })} />
            </label>
            <label className="field">
              <span>Дата рождения</span>
              <input
                type="date"
                value={draft.birthDate ?? ""}
                onChange={(event) => {
                  const birthDate = event.target.value || null;
                  onChange({ birthDate, age: ageFromBirthDate(birthDate) });
                }}
              />
            </label>
            <label className="field field--age">
              <span>Возраст</span>
              <input type="number" min={0} max={120} value={draft.age ?? ""} onChange={(event) => onChange({ age: Number(event.target.value) || null })} />
            </label>
            <label className="field">
              <span>Роль</span>
              <input value={draft.role} onChange={(event) => onChange({ role: event.target.value })} />
            </label>
            <label className="field">
              <span>Статус</span>
              <input value={draft.status} onChange={(event) => onChange({ status: event.target.value })} />
            </label>
            <label className="field">
              <span>Локация</span>
              <input value={draft.location} onChange={(event) => onChange({ location: event.target.value })} />
            </label>
            <label className="field field--slider">
              <span>Подозрение: {draft.suspicionLevel}%</span>
              <input type="range" min={0} max={100} value={draft.suspicionLevel} onChange={(event) => onChange({ suspicionLevel: Number(event.target.value) })} />
            </label>
          </div>

          <div className="compact-grid compact-grid--content">
            <label className="field field--tall">
              <span>Биография</span>
              <textarea rows={4} value={draft.biography} onChange={(event) => onChange({ biography: event.target.value })} />
            </label>
            <label className="field field--tall">
              <span>Описание по делу</span>
              <textarea rows={4} value={draft.description} onChange={(event) => onChange({ description: event.target.value })} />
            </label>
            <label className="field field--tall">
              <span>Документы</span>
              <textarea rows={4} value={draft.documentsSummary} onChange={(event) => onChange({ documentsSummary: event.target.value })} />
            </label>
            <label className="field field--tall">
              <span>Места</span>
              <textarea rows={4} value={draft.knownPlaces} onChange={(event) => onChange({ knownPlaces: event.target.value })} />
            </label>
            <label className="field field--tall">
              <span>Повадки</span>
              <textarea rows={4} value={draft.habits} onChange={(event) => onChange({ habits: event.target.value })} />
            </label>
            <label className="field field--tall">
              <span>Оперативные заметки</span>
              <textarea rows={4} value={draft.notes} onChange={(event) => onChange({ notes: event.target.value })} />
            </label>
          </div>

          <div className="subpanel">
            <div className="panel-head">
              <div>
                <p className="eyebrow">ИИ-досье</p>
                <h3>Краткий аналитический черновик</h3>
              </div>
              <div className="actions">
                <button className="ghost" onClick={async () => setAiDossier(await onGenerateAIDossier())} disabled={aiBusy}>
                  {aiBusy ? "Генерирую..." : "Собрать досье ИИ"}
                </button>
                {aiDossier ? (
                  <button
                    onClick={() => {
                      onChange({
                        description: aiDossier.description || draft.description,
                        notes: aiDossier.notes || draft.notes,
                        status: aiDossier.status || draft.status,
                        suspicionLevel: aiDossier.suspicionLevel || draft.suspicionLevel,
                      });
                    }}
                  >
                    Применить к карточке
                  </button>
                ) : null}
              </div>
            </div>
            {aiDossier ? (
              <div className="brief-layout">
                <article className="section-card">
                  <h3>Сводка</h3>
                  <p>{aiDossier.summary}</p>
                </article>
                <article className="section-card">
                  <h3>Ключевые факты</h3>
                  <ul>{aiDossier.keyFacts.map((item) => <li key={item}>{item}</li>)}</ul>
                </article>
                <article className="section-card">
                  <h3>Красные флаги</h3>
                  <ul>{aiDossier.redFlags.map((item) => <li key={item}>{item}</li>)}</ul>
                </article>
                <article className="section-card">
                  <h3>Рекомендации</h3>
                  <ul>{aiDossier.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
                </article>
              </div>
            ) : (
              <div className="empty-inline">ИИ может быстро собрать компактное досье по текущей карточке и контексту дела.</div>
            )}
          </div>
        </div>
      ) : null}

      {activeTab === "materials" ? (
        <div className="detail-grid">
          <section className="detail-column">
            <div className="detail-column__header">
              <h3>Улики</h3>
              <span>{dossier.evidence.length}</span>
            </div>
            <div className="mini-form">
              <div className="mini-form__row">
                <input placeholder="Название" value={evidenceDraft.title} onChange={(event) => setEvidenceDraft((current) => ({ ...current, title: event.target.value }))} />
                <input placeholder="Категория" value={evidenceDraft.category} onChange={(event) => setEvidenceDraft((current) => ({ ...current, category: event.target.value }))} />
              </div>
              <div className="mini-form__row">
                <input placeholder="Статус" value={evidenceDraft.status} onChange={(event) => setEvidenceDraft((current) => ({ ...current, status: event.target.value }))} />
              </div>
              <textarea rows={3} placeholder="Описание" value={evidenceDraft.details} onChange={(event) => setEvidenceDraft((current) => ({ ...current, details: event.target.value }))} />
              <button className="ghost" onClick={() => { if (!evidenceDraft.title.trim()) return; void onAddEvidence(evidenceDraft); setEvidenceDraft(blankEvidence()); }}>
                Добавить улику
              </button>
            </div>
            {dossier.evidence.map((item) => (
              <article key={item.id} className="detail-card">
                <div className="detail-card__actions">
                  <strong>{item.title}</strong>
                  <button className="ghost danger detail-card__delete" onClick={() => void onDeleteEvidence(item.id)}>
                    Удалить
                  </button>
                </div>
                <p>{item.category} · {item.status}</p>
                <small>{item.details}</small>
              </article>
            ))}
          </section>

          <section className="detail-column">
            <div className="detail-column__header">
              <h3>События</h3>
              <span>{dossier.events.length}</span>
            </div>
            <div className="mini-form">
              <div className="mini-form__row">
                <input placeholder="Дата" value={eventDraft.eventDate} onChange={(event) => setEventDraft((current) => ({ ...current, eventDate: event.target.value }))} />
                <input placeholder="Название" value={eventDraft.title} onChange={(event) => setEventDraft((current) => ({ ...current, title: event.target.value }))} />
              </div>
              <textarea rows={3} placeholder="Что произошло" value={eventDraft.details} onChange={(event) => setEventDraft((current) => ({ ...current, details: event.target.value }))} />
              <button className="ghost" onClick={() => { if (!eventDraft.title.trim()) return; void onAddEvent(eventDraft); setEventDraft(blankEvent()); }}>
                Добавить событие
              </button>
            </div>
            {dossier.events.map((item) => (
              <article key={item.id} className="detail-card">
                <div className="detail-card__actions">
                  <strong>{item.title}</strong>
                  <button className="ghost danger detail-card__delete" onClick={() => void onDeleteEvent(item.id)}>
                    Удалить
                  </button>
                </div>
                <p>{item.eventDate}</p>
                <small>{item.details}</small>
              </article>
            ))}
          </section>
        </div>
      ) : null}

      {activeTab === "links" ? (
        <div className="detail-grid detail-grid--single">
          <section className="detail-column">
            <div className="detail-column__header">
              <h3>Связи</h3>
              <span>{dossier.relations.length}</span>
            </div>
            <div className="mini-form">
              <div className="mini-form__row">
                <input placeholder="Тип цели" value={relationDraft.targetType} onChange={(event) => setRelationDraft((current) => ({ ...current, targetType: event.target.value }))} />
                <input placeholder="Цель" value={relationDraft.targetLabel} onChange={(event) => setRelationDraft((current) => ({ ...current, targetLabel: event.target.value }))} />
              </div>
              <div className="mini-form__row">
                <input placeholder="Тип связи" value={relationDraft.relationType} onChange={(event) => setRelationDraft((current) => ({ ...current, relationType: event.target.value }))} />
                <input type="number" min={0} max={100} placeholder="Достоверность" value={relationDraft.confidence} onChange={(event) => setRelationDraft((current) => ({ ...current, confidence: Number(event.target.value) || 0 }))} />
              </div>
              <button className="ghost" onClick={() => { if (!relationDraft.targetLabel.trim()) return; void onAddRelation(relationDraft); setRelationDraft(blankRelation()); }}>
                Добавить связь
              </button>
            </div>
            {dossier.relations.map((item) => (
              <article key={item.id} className="detail-card">
                <div className="detail-card__actions">
                  <strong>{item.targetLabel}</strong>
                  <button className="ghost danger detail-card__delete" onClick={() => void onDeleteRelation(item.id)}>
                    Удалить
                  </button>
                </div>
                <p>{item.targetType} · {item.relationType}</p>
                <small>Достоверность: {item.confidence}%</small>
              </article>
            ))}
          </section>
        </div>
      ) : null}

      {activeTab === "esoteric" ? (
        <div className="dossier-tab">
          <DestinyMatrixPanel birthDate={draft.birthDate} fullName={draft.fullName} age={draft.age} />
          {dossier.matrix ? (
            <div className="brief-layout">
              <article className="section-card">
                <h3>Интерпретация</h3>
                <p>{dossier.matrix.interpretation}</p>
              </article>
              <article className="section-card">
                <h3>Сильные стороны</h3>
                <ul>{dossier.matrix.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
              </article>
              <article className="section-card">
                <h3>Риски</h3>
                <ul>{dossier.matrix.risks.map((item) => <li key={item}>{item}</li>)}</ul>
              </article>
              <article className="section-card">
                <h3>Стиль отношений</h3>
                <p>{dossier.matrix.relationshipStyle}</p>
              </article>
              <article className="section-card">
                <h3>Социальный вектор</h3>
                <p>{dossier.matrix.socialVector}</p>
              </article>
              <article className="section-card">
                <h3>Теневая сторона</h3>
                <p>{dossier.matrix.shadowPattern}</p>
              </article>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
