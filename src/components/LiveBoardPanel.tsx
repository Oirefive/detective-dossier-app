import type { AutoBriefResponse, CaseGraphResponse, CaseParticipant } from "../types";
import { StatusPill, statusTone } from "./StatusPill";

export function LiveBoardPanel({
  active,
  graph,
  brief,
  participants,
}: {
  active: boolean;
  graph: CaseGraphResponse | null;
  brief: AutoBriefResponse | null;
  participants: CaseParticipant[];
}) {
  if (!active) return null;

  return (
    <section className="panel live-board">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Живая доска</p>
          <h2>Оперативная раскладка</h2>
        </div>
      </div>
      <div className="live-board__grid">
        <article className="board-note">
          <h3>Ядро фигурантов</h3>
          {participants.slice(0, 4).map((item) => (
            <div key={item.id} className="board-note__row">
              <strong>{item.fullName}</strong>
              <StatusPill label={`${item.suspicionLevel}%`} tone={statusTone(item.status, item.suspicionLevel)} />
            </div>
          ))}
        </article>
        <article className="board-note">
          <h3>Короткая сводка</h3>
          <p>{brief?.summary ?? "Сводка появится после выбора дела."}</p>
        </article>
        <article className="board-note">
          <h3>Узлы графа</h3>
          <ul>{graph?.nodes.slice(0, 6).map((item) => <li key={item.id}>{item.label}</li>) ?? <li>Нет данных</li>}</ul>
        </article>
        <article className="board-note">
          <h3>Связи</h3>
          <ul>
            {graph?.edges.slice(0, 6).map((item, index) => <li key={`${item.source}-${item.target}-${index}`}>{item.label}</li>) ?? (
              <li>Нет данных</li>
            )}
          </ul>
        </article>
      </div>
    </section>
  );
}
