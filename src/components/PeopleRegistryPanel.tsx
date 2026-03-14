import { useEffect, useMemo, useState } from "react";

import type { AIPersonCardResponse, CaseAssignmentCreatePayload, CaseSummary, Person, PersonCreatePayload } from "../types";
import { PhotoUploadField } from "./PhotoUploadField";
import { StatusPill } from "./StatusPill";

function blankPerson(): PersonCreatePayload {
  return {
    fullName: "",
    aliasName: "",
    birthDate: null,
    age: null,
    biography: "",
    documentsSummary: "",
    knownPlaces: "",
    habits: "",
    photoPath: null,
    pinned: false,
  };
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

export function PeopleRegistryPanel({
  people,
  activePersonId,
  activePerson,
  cases,
  activeCaseId,
  onSelectPerson,
  onStartCreate,
  onCreatePerson,
  onSavePerson,
  onDeletePerson,
  onPinPerson,
  onAssignToCase,
  onUploadPhoto,
  onPersistPhoto,
  photoUploading,
  onGenerateWithAI,
  aiBusy,
}: {
  people: Person[];
  activePersonId: string | null;
  activePerson: Person | null;
  cases: CaseSummary[];
  activeCaseId: string | null;
  onSelectPerson: (id: string) => void;
  onStartCreate: () => void;
  onCreatePerson: (payload: PersonCreatePayload) => void | Promise<void>;
  onSavePerson: (personId: string, payload: PersonCreatePayload) => void | Promise<void>;
  onDeletePerson: (personId: string) => void | Promise<void>;
  onPinPerson: (personId: string, pinned: boolean) => void | Promise<void>;
  onAssignToCase: (payload: CaseAssignmentCreatePayload) => void | Promise<void>;
  onUploadPhoto: (file: File) => Promise<string>;
  onPersistPhoto: (path: string | null) => Promise<void>;
  photoUploading: boolean;
  onGenerateWithAI: (sourceText: string) => Promise<AIPersonCardResponse>;
  aiBusy: boolean;
}) {
  const [filter, setFilter] = useState("");
  const [draft, setDraft] = useState<PersonCreatePayload>(blankPerson());
  const [assignment, setAssignment] = useState<CaseAssignmentCreatePayload>({
    personId: "",
    role: "",
    suspicionLevel: 35,
    status: "Новый участник",
    location: "",
    description: "",
    notes: "",
    pinned: false,
  });
  const [aiSourceText, setAiSourceText] = useState("");
  const [aiOpen, setAiOpen] = useState(false);
  const [assignmentOpen, setAssignmentOpen] = useState(false);

  useEffect(() => {
    if (!activePerson) {
      setDraft(blankPerson());
      setAssignment((current) => ({
        ...current,
        personId: "",
        role: "",
        status: "Новый участник",
        location: "",
        description: "",
        notes: "",
        suspicionLevel: 35,
        pinned: false,
      }));
      setAssignmentOpen(false);
      return;
    }

    setDraft({
      fullName: activePerson.fullName,
      aliasName: activePerson.aliasName,
      birthDate: activePerson.birthDate,
      age: activePerson.age,
      biography: activePerson.biography,
      documentsSummary: activePerson.documentsSummary,
      knownPlaces: activePerson.knownPlaces,
      habits: activePerson.habits,
      photoPath: activePerson.photoPath,
      pinned: activePerson.pinned,
    });
    setAssignment((current) => ({ ...current, personId: activePerson.id }));
  }, [activePerson]);

  const filtered = useMemo(() => {
    const query = filter.trim().toLowerCase();
    if (!query) return people;
    return people.filter((item) =>
      [item.fullName, item.aliasName, item.knownPlaces, item.documentsSummary].join(" ").toLowerCase().includes(query)
    );
  }, [filter, people]);

  return (
    <section className="people-layout">
      <section className="panel panel--compact">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Реестр людей</p>
            <h2>Все карточки</h2>
          </div>
        </div>
        <input className="search-input" placeholder="Поиск по людям" value={filter} onChange={(event) => setFilter(event.target.value)} />
        <div className="participant-list">
          {filtered.map((item) => (
            <button
              key={item.id}
              className={`participant-card ${activePersonId === item.id ? "participant-card--active" : ""}`}
              onClick={() => onSelectPerson(item.id)}
            >
              <div className="participant-card__header">
                <strong>{item.fullName}</strong>
                <div className="tag-row">{item.pinned ? <StatusPill label="Важный" tone="success" /> : null}</div>
              </div>
              <p>{item.aliasName || "Без псевдонима"}</p>
              <small>{item.birthDate || "Дата рождения не указана"}</small>
            </button>
          ))}
        </div>
      </section>

      <section className="panel panel--form">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Карточка человека</p>
            <h2>{activePerson ? activePerson.fullName : "Новый человек"}</h2>
          </div>
          <div className="actions">
            <button className="ghost" onClick={onStartCreate}>
              Новый человек
            </button>
            {activePerson ? (
              <>
                <button
                  className={`ghost ${activePerson.pinned ? "pin-active" : ""}`}
                  onClick={() => void onPinPerson(activePerson.id, !activePerson.pinned)}
                >
                  {activePerson.pinned ? "Открепить" : "Закрепить"}
                </button>
                <button
                  className="ghost danger"
                  onClick={() => {
                    if (window.confirm(`Удалить человека «${activePerson.fullName}»?`)) {
                      void onDeletePerson(activePerson.id);
                    }
                  }}
                >
                  Удалить
                </button>
              </>
            ) : null}
            <button
              onClick={() => {
                if (!draft.fullName.trim()) return;
                if (activePerson) void onSavePerson(activePerson.id, draft);
                else void onCreatePerson(draft);
              }}
            >
              {activePerson ? "Сохранить" : "Создать"}
            </button>
          </div>
        </div>

        <div className="identity-grid identity-grid--compact">
          <div className="identity-grid__photo">
            <PhotoUploadField
              compact
              label="Фото человека"
              value={draft.photoPath}
              onUpload={async (file) => {
                const path = await onUploadPhoto(file);
                setDraft((current) => ({ ...current, photoPath: path }));
                if (activePerson) await onPersistPhoto(path);
              }}
              onClear={() => {
                setDraft((current) => ({ ...current, photoPath: null }));
                if (activePerson) void onPersistPhoto(null);
              }}
              uploading={photoUploading}
            />
          </div>

          <div className="compact-grid compact-grid--identity compact-grid--people">
            <label className="field field--wide">
              <span>ФИО</span>
              <input value={draft.fullName} onChange={(event) => setDraft((current) => ({ ...current, fullName: event.target.value }))} />
            </label>
            <label className="field">
              <span>Псевдоним</span>
              <input value={draft.aliasName} onChange={(event) => setDraft((current) => ({ ...current, aliasName: event.target.value }))} />
            </label>
            <label className="field">
              <span>Дата рождения</span>
              <input
                type="date"
                value={draft.birthDate ?? ""}
                onChange={(event) => {
                  const birthDate = event.target.value || null;
                  setDraft((current) => ({ ...current, birthDate, age: ageFromBirthDate(birthDate) }));
                }}
              />
            </label>
            <label className="field field--age">
              <span>Возраст</span>
              <input type="number" min={0} max={120} value={draft.age ?? ""} onChange={(event) => setDraft((current) => ({ ...current, age: Number(event.target.value) || null }))} />
            </label>
          </div>
        </div>

        <div className="compact-grid compact-grid--content">
          <label className="field field--tall">
            <span>Биография</span>
            <textarea rows={4} value={draft.biography} onChange={(event) => setDraft((current) => ({ ...current, biography: event.target.value }))} />
          </label>
          <label className="field field--tall">
            <span>Документы</span>
            <textarea rows={4} value={draft.documentsSummary} onChange={(event) => setDraft((current) => ({ ...current, documentsSummary: event.target.value }))} />
          </label>
          <label className="field field--tall">
            <span>Места</span>
            <textarea rows={4} value={draft.knownPlaces} onChange={(event) => setDraft((current) => ({ ...current, knownPlaces: event.target.value }))} />
          </label>
          <label className="field field--tall">
            <span>Повадки</span>
            <textarea rows={4} value={draft.habits} onChange={(event) => setDraft((current) => ({ ...current, habits: event.target.value }))} />
          </label>
        </div>

        <section className="accordion">
          <button className="accordion__header" onClick={() => setAiOpen((current) => !current)} type="button">
            <div>
              <p className="eyebrow">ИИ-сборка карточки</p>
              <h3>Из сырого текста в профиль</h3>
            </div>
            <span>{aiOpen ? "Свернуть" : "Развернуть"}</span>
          </button>
          {aiOpen ? (
            <div className="accordion__body">
              <label className="field field--tall">
                <span>Черновой текст</span>
                <textarea
                  rows={6}
                  placeholder="Вставьте заметки, описание, переписку, выдержку из протокола или просто грубый текст. ИИ попробует собрать аккуратную карточку."
                  value={aiSourceText}
                  onChange={(event) => setAiSourceText(event.target.value)}
                />
              </label>
              <div className="actions">
                <button
                  className="ghost"
                  disabled={!aiSourceText.trim() || aiBusy}
                  onClick={async () => {
                    const generated = await onGenerateWithAI(aiSourceText);
                    setDraft((current) => ({
                      ...current,
                      fullName: generated.fullName || current.fullName,
                      aliasName: generated.aliasName || current.aliasName,
                      birthDate: generated.birthDate ?? current.birthDate,
                      age: ageFromBirthDate(generated.birthDate ?? current.birthDate),
                      biography: generated.biography || current.biography,
                      documentsSummary: generated.documentsSummary || current.documentsSummary,
                      knownPlaces: generated.knownPlaces || current.knownPlaces,
                      habits: generated.habits || current.habits,
                    }));
                  }}
                >
                  {aiBusy ? "Собираю..." : "Собрать карточку ИИ"}
                </button>
              </div>
            </div>
          ) : null}
        </section>

        {activePerson ? (
          <section className="accordion">
            <button className="accordion__header" onClick={() => setAssignmentOpen((current) => !current)} type="button">
              <div>
                <p className="eyebrow">Привязка к делу</p>
                <h3>Добавить человека в выбранное дело</h3>
              </div>
              <span>{assignmentOpen ? "Свернуть" : "Развернуть"}</span>
            </button>
            {assignmentOpen ? (
              <div className="accordion__body">
                <div className="compact-grid compact-grid--identity compact-grid--assign">
                  <label className="field field--wide">
                    <span>Выбранное дело</span>
                    <select value={activeCaseId ?? ""} disabled>
                      <option value="">{cases.length ? "Выберите дело слева" : "Нет доступных дел"}</option>
                      {cases.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.title}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="field">
                    <span>Роль</span>
                    <input value={assignment.role} onChange={(event) => setAssignment((current) => ({ ...current, role: event.target.value }))} />
                  </label>
                  <label className="field">
                    <span>Статус</span>
                    <input value={assignment.status} onChange={(event) => setAssignment((current) => ({ ...current, status: event.target.value }))} />
                  </label>
                  <label className="field">
                    <span>Локация</span>
                    <input value={assignment.location} onChange={(event) => setAssignment((current) => ({ ...current, location: event.target.value }))} />
                  </label>
                  <label className="field field--slider">
                    <span>Подозрение ({assignment.suspicionLevel}%)</span>
                    <input type="range" min={0} max={100} value={assignment.suspicionLevel} onChange={(event) => setAssignment((current) => ({ ...current, suspicionLevel: Number(event.target.value) }))} />
                  </label>
                </div>
                <div className="compact-grid compact-grid--content">
                  <label className="field field--tall">
                    <span>Описание по делу</span>
                    <textarea rows={4} value={assignment.description} onChange={(event) => setAssignment((current) => ({ ...current, description: event.target.value }))} />
                  </label>
                  <label className="field field--tall">
                    <span>Заметки</span>
                    <textarea rows={4} value={assignment.notes} onChange={(event) => setAssignment((current) => ({ ...current, notes: event.target.value }))} />
                  </label>
                </div>
                <div className="actions">
                  <button
                    disabled={!activeCaseId}
                    onClick={() => {
                      if (!activeCaseId || !activePerson) return;
                      void onAssignToCase({ ...assignment, personId: activePerson.id });
                    }}
                  >
                    Добавить в выбранное дело
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        ) : null}
      </section>
    </section>
  );
}
