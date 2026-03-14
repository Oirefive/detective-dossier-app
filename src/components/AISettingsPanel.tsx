import { useEffect, useRef, useState } from "react";

import type { AISettings } from "../types";

const PROVIDERS = {
  openai: { model: "gpt-4o-mini", baseUrl: "https://api.openai.com/v1" },
  deepseek: { model: "deepseek-chat", baseUrl: "https://api.deepseek.com/v1" },
  custom: { model: "", baseUrl: "" },
};

const DEFAULT_CARD_PROMPT =
  "Ты аналитик расследований. По сырому тексту собери аккуратную карточку человека. Верни только JSON с полями: fullName, aliasName, birthDate, biography, documentsSummary, knownPlaces, habits. Пиши по-русски. Не выдумывай факты, которых нет в тексте. Если данных нет, верни пустую строку или null для birthDate.";

const DEFAULT_DOSSIER_PROMPT =
  "Ты аналитик расследований. По карточке человека и контексту дела подготовь краткое досье. Верни только JSON с полями: summary, description, notes, status, suspicionLevel, keyFacts, redFlags, recommendations. Пиши по-русски, структурно, без воды и без выдумки.";

function normalizeSettings(settings: AISettings | null): AISettings | null {
  if (!settings) return null;
  return {
    ...settings,
    cardPrompt: settings.cardPrompt || DEFAULT_CARD_PROMPT,
    dossierPrompt: settings.dossierPrompt || DEFAULT_DOSSIER_PROMPT,
  };
}

export function AISettingsPanel({
  open,
  settings,
  saving,
  activeCaseTitle,
  onClose,
  onSave,
  onExportCase,
  onImportCase,
}: {
  open: boolean;
  settings: AISettings | null;
  saving: boolean;
  activeCaseTitle: string | null;
  onClose: () => void;
  onSave: (payload: AISettings) => void | Promise<void>;
  onExportCase: () => void | Promise<void>;
  onImportCase: (file: File) => void | Promise<void>;
}) {
  const [draft, setDraft] = useState<AISettings | null>(normalizeSettings(settings));
  const fileRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setDraft(normalizeSettings(settings));
  }, [settings]);

  if (!open || !draft) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <section className="modal-panel modal-panel--wide" onClick={(event) => event.stopPropagation()}>
        <div className="panel-head">
          <div>
            <p className="eyebrow">Настройки</p>
            <h2>ИИ и данные архива</h2>
            <p className="panel-copy">
              Здесь живут модель, ключи и сервисные действия по делу. Им не нужно торчать в шапке как продавцам страховок.
            </p>
          </div>
          <div className="actions">
            <button className="ghost" onClick={onClose}>
              Закрыть
            </button>
            <button onClick={() => void onSave(draft)} disabled={saving}>
              {saving ? "Сохраняю..." : "Сохранить"}
            </button>
          </div>
        </div>

        <div className="detail-grid">
          <section className="section-card">
            <h3>Настройки ИИ</h3>
            <div className="compact-grid compact-grid--identity compact-grid--dossier">
              <label className="field">
                <span>Провайдер</span>
                <select
                  value={draft.provider}
                  onChange={(event) => {
                    const provider = event.target.value;
                    const preset = PROVIDERS[provider as keyof typeof PROVIDERS] ?? PROVIDERS.custom;
                    setDraft((current) =>
                      current
                        ? {
                            ...current,
                            provider,
                            model: provider === "custom" ? current.model : preset.model,
                            baseUrl: provider === "custom" ? current.baseUrl : preset.baseUrl,
                          }
                        : current
                    );
                  }}
                >
                  <option value="openai">ChatGPT / OpenAI</option>
                  <option value="deepseek">DeepSeek</option>
                  <option value="custom">Совместимый API</option>
                </select>
              </label>
              <label className="field">
                <span>Модель</span>
                <input value={draft.model} onChange={(event) => setDraft((current) => (current ? { ...current, model: event.target.value } : current))} />
              </label>
              <label className="field field--wide">
                <span>Base URL</span>
                <input value={draft.baseUrl} onChange={(event) => setDraft((current) => (current ? { ...current, baseUrl: event.target.value } : current))} />
              </label>
              <label className="field field--wide">
                <span>API key</span>
                <input type="password" value={draft.apiKey} onChange={(event) => setDraft((current) => (current ? { ...current, apiKey: event.target.value } : current))} />
              </label>
            </div>

            <div className="compact-grid compact-grid--content">
              <label className="field field--tall">
                <span>Промпт: сборка карточки</span>
                <textarea rows={8} value={draft.cardPrompt} onChange={(event) => setDraft((current) => (current ? { ...current, cardPrompt: event.target.value } : current))} />
              </label>
              <label className="field field--tall">
                <span>Промпт: краткое досье</span>
                <textarea rows={8} value={draft.dossierPrompt} onChange={(event) => setDraft((current) => (current ? { ...current, dossierPrompt: event.target.value } : current))} />
              </label>
            </div>
          </section>

          <section className="section-card">
            <h3>Данные дела</h3>
            <p className="panel-copy">
              {activeCaseTitle ? `Активное дело: ${activeCaseTitle}` : "Сначала выберите дело. Без него экспортировать, как ни странно, нечего."}
            </p>
            <div className="actions">
              <button className="ghost" onClick={() => void onExportCase()} disabled={!activeCaseTitle}>
                Экспорт дела
              </button>
              <button className="ghost" onClick={() => fileRef.current?.click()}>
                Импорт дела
              </button>
              <input
                ref={fileRef}
                type="file"
                accept=".json,application/json"
                hidden
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void onImportCase(file);
                  event.currentTarget.value = "";
                }}
              />
            </div>
          </section>
        </div>
      </section>
    </div>
  );
}
