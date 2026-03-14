import type { CaseGraphResponse } from "../types";
import { StatusPill, statusTone } from "./StatusPill";

export function CaseGraphPanel({ graph }: { graph: CaseGraphResponse | null }) {
  if (!graph) {
    return (
      <section className="panel panel--compact">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Граф связей</p>
            <h2>Контур дела</h2>
          </div>
        </div>
        <div className="empty-inline">Сначала выберите дело. Граф сам из воздуха связи не родит.</div>
      </section>
    );
  }

  const labelMap = new Map(graph.nodes.map((node) => [node.id, node.label]));

  return (
    <section className="panel panel--compact">
      <div className="panel-head">
        <div>
          <p className="eyebrow">Граф связей</p>
          <h2>Живая карта</h2>
        </div>
        <span className="badge">{graph.nodes.length} узлов</span>
      </div>
      <div className="graph-board">
        {graph.nodes.slice(0, 12).map((node) => (
          <article key={node.id} className={`graph-node graph-node--${node.nodeType}`}>
            <strong>{node.label}</strong>
            <div className="tag-row">
              <StatusPill label={node.nodeType} tone="neutral" />
              {node.status ? <StatusPill label={node.status} tone={statusTone(node.status)} /> : null}
            </div>
          </article>
        ))}
      </div>
      <div className="relation-list">
        {graph.edges.slice(0, 10).map((edge, index) => (
          <div key={`${edge.source}-${edge.target}-${index}`} className="relation-list__item">
            <span>{edge.label}</span>
            <small>
              {labelMap.get(edge.source) ?? edge.source} → {labelMap.get(edge.target) ?? edge.target}
            </small>
          </div>
        ))}
      </div>
    </section>
  );
}
