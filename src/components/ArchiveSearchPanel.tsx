import type { ArchiveSearchResult } from "../types";
import { StatusPill, statusTone } from "./StatusPill";

export function ArchiveSearchPanel({
  query,
  results,
  onQueryChange,
  onPickResult,
}: {
  query: string;
  results: ArchiveSearchResult[];
  onQueryChange: (value: string) => void;
  onPickResult: (item: ArchiveSearchResult) => void;
}) {
  return (
    <section className="panel panel--compact">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Глобальный поиск</p>
          <h2>Весь архив сразу</h2>
        </div>
      </div>
      <input
        className="search-input"
        placeholder="Дело, человек, место, событие, улика"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
      />
      {query.trim() ? (
        <div className="archive-result-list">
          {results.length ? (
            results.map((item) => (
              <button key={`${item.entityType}:${item.entityId}`} className="archive-result" onClick={() => onPickResult(item)}>
                <div className="archive-result__head">
                  <strong>{item.title}</strong>
                  <div className="tag-row">
                    <StatusPill label={item.entityType} tone="neutral" />
                    {item.status ? <StatusPill label={item.status} tone={statusTone(item.status)} /> : null}
                    {item.pinned ? <StatusPill label="Закреплено" tone="success" /> : null}
                  </div>
                </div>
                <p>{item.subtitle}</p>
                <small>{item.highlights.join(" · ") || "Совпадение по архиву"}</small>
              </button>
            ))
          ) : (
            <div className="empty-inline">Ничего не найдено. Архив пока держит лицо.</div>
          )}
        </div>
      ) : (
        <div className="empty-inline">Введите запрос и ищите сразу по людям, делам и участникам.</div>
      )}
    </section>
  );
}
