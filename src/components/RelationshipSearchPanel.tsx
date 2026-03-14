import type { RelationshipHit } from "../types";

function confidenceLabel(value: string) {
  const normalized = value.toLowerCase();
  if (normalized.includes("высок")) return "Уверенная связь";
  if (normalized.includes("сред")) return "Нужно проверить";
  return "Предварительно";
}

export function RelationshipSearchPanel({
  query,
  loading,
  results,
  onQueryChange,
  onSubmit,
  onPickParticipant,
}: {
  query: string;
  loading: boolean;
  results: RelationshipHit[];
  onQueryChange: (value: string) => void;
  onSubmit: (value: string) => void;
  onPickParticipant: (id: string) => void;
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Поиск взаимосвязей</p>
          <h2>Аналитика по делу</h2>
          <p className="panel-copy">
            Сопоставляет людей по документам, местам, повадкам, уликам, событиям и прямым связям.
          </p>
        </div>
      </div>

      <div className="search-bar">
        <input
          className="search-input"
          placeholder="Например: архив, пропуск, терминал, Орлова"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") onSubmit(query);
          }}
        />
        <button onClick={() => onSubmit(query)}>{loading ? "Поиск..." : "Найти"}</button>
      </div>

      <div className="search-results">
        {results.map((hit) => (
          <article key={hit.participant.id} className="result-card">
            <div className="result-card__header">
              <div>
                <strong>{hit.participant.fullName}</strong>
                <p>{hit.participant.aliasName || "Без псевдонима"}</p>
              </div>
              <div className="result-card__score">
                <span>{hit.score}</span>
                <small>{confidenceLabel(hit.confidence)}</small>
              </div>
            </div>

            <p className="result-card__summary">{hit.summary}</p>

            <div className="tag-row">
              {hit.matchedOn.map((item) => (
                <span key={item} className="tag">
                  {item}
                </span>
              ))}
            </div>

            <div className="result-columns">
              <div>
                <h4>Подсветка</h4>
                <ul>
                  {hit.highlights.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4>Опорные связи</h4>
                <ul>
                  {hit.topLinks.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            <button className="ghost" onClick={() => onPickParticipant(hit.participant.id)}>
              Открыть карточку
            </button>
          </article>
        ))}
        {!results.length && !loading && (
          <div className="empty-inline">Введите запрос, и система покажет совпадения по делу.</div>
        )}
      </div>
    </section>
  );
}
