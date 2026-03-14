import type { AutoBriefResponse } from "../types";

export function AutoBriefPanel({ brief }: { brief: AutoBriefResponse | null }) {
  return (
    <section className="panel panel--compact">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Автосводка</p>
          <h2>Краткий разбор</h2>
        </div>
      </div>
      {brief ? (
        <div className="brief-layout">
          <article className="section-card">
            <h3>{brief.headline}</h3>
            <p>{brief.summary}</p>
          </article>
          <article className="section-card">
            <h3>Ключевые люди</h3>
            <ul>{brief.keyPeople.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
          <article className="section-card">
            <h3>Ключевые места</h3>
            <ul>{brief.keyPlaces.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
          <article className="section-card">
            <h3>Риски</h3>
            <ul>{brief.keyRisks.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
          <article className="section-card">
            <h3>Рекомендации</h3>
            <ul>{brief.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
        </div>
      ) : (
        <div className="empty-inline">Сводка появится после выбора дела.</div>
      )}
    </section>
  );
}
