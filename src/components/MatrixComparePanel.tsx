import type { CaseCompatibilityResponse, MatrixComparisonResponse, Person } from "../types";
import { StatusPill } from "./StatusPill";

export function MatrixComparePanel({
  people,
  activePersonId,
  comparePersonId,
  onComparePersonIdChange,
  comparison,
  compatibility,
}: {
  people: Person[];
  activePersonId: string | null;
  comparePersonId: string | null;
  onComparePersonIdChange: (value: string) => void;
  comparison: MatrixComparisonResponse | null;
  compatibility: CaseCompatibilityResponse | null;
}) {
  const options = people.filter((item) => item.id !== activePersonId);

  return (
    <section className="panel panel--compact">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Эзотерический слой</p>
          <h2>Сравнение и совместимость</h2>
        </div>
      </div>
      <label className="field">
        <span>Сравнить с другим человеком</span>
        <select value={comparePersonId ?? ""} onChange={(event) => onComparePersonIdChange(event.target.value)}>
          <option value="">Выберите второго человека</option>
          {options.map((item) => (
            <option key={item.id} value={item.id}>
              {item.fullName}
            </option>
          ))}
        </select>
      </label>

      {comparison ? (
        <div className="brief-layout">
          <article className="section-card">
            <h3>
              {comparison.leftPerson.fullName} × {comparison.rightPerson.fullName}
            </h3>
            <p>{comparison.summary}</p>
            <StatusPill label={`${comparison.compatibilityScore}% · ${comparison.resonance}`} tone="warn" />
          </article>
          <article className="section-card">
            <h3>Общие опоры</h3>
            <ul>{comparison.sharedStrengths.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
          <article className="section-card">
            <h3>Точки напряжения</h3>
            <ul>{comparison.tensionPoints.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
        </div>
      ) : null}

      {compatibility ? (
        <div className="brief-layout">
          <article className="section-card">
            <h3>Совместимость с делом</h3>
            <p>{compatibility.summary}</p>
            <StatusPill label={`${compatibility.compatibilityScore}%`} tone="success" />
          </article>
          <article className="section-card">
            <h3>Почему совпадает</h3>
            <ul>{compatibility.matchReasons.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
          <article className="section-card">
            <h3>Риски</h3>
            <ul>{compatibility.riskFactors.map((item) => <li key={item}>{item}</li>)}</ul>
          </article>
        </div>
      ) : null}
    </section>
  );
}
