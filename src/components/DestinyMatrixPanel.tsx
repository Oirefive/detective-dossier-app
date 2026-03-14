import { useEffect, useState } from "react";

import type { DestinyMatrixData } from "../types";
import { api } from "../tauri";

export function DestinyMatrixPanel({
  birthDate,
  fullName,
  age,
}: {
  birthDate: string | null;
  fullName: string;
  age: number | null;
}) {
  const [matrix, setMatrix] = useState<DestinyMatrixData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadMatrix() {
      if (!birthDate) {
        setMatrix(null);
        setError(null);
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const next = await api.getDestinyMatrix(birthDate);
        if (!cancelled) {
          setMatrix(next);
        }
      } catch (loadError) {
        if (!cancelled) {
          setMatrix(null);
          setError("Не удалось загрузить эталонную матрицу. Проверьте подключение к сети.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadMatrix();
    return () => {
      cancelled = true;
    };
  }, [birthDate]);

  if (!birthDate) {
    return <div className="empty-inline">Укажите дату рождения, и матрица появится. Без даты это просто красивые кружки для самообмана.</div>;
  }

  if (loading) {
    return <div className="empty-inline">Синхронизирую матрицу с эталонным калькулятором...</div>;
  }

  if (error || !matrix) {
    return <div className="empty-inline">{error ?? "Матрицу пока получить не удалось."}</div>;
  }

  return (
    <section className="destiny-matrix">
      <div className="destiny-matrix__info">
        <div className="panel-head">
          <div>
            <p className="eyebrow">Эзотерический профиль</p>
            <h3>{fullName}</h3>
            <p className="panel-copy">
              Дата рождения: {birthDate} · Возраст: {age ?? "не указан"}
            </p>
          </div>
        </div>

        <article className="section-card">
          <h3>Карта здоровья</h3>
          <table className="chakra-table">
            <thead>
              <tr>
                <th>Чакра</th>
                <th>Физика</th>
                <th>Энергия</th>
                <th>Эмоция</th>
              </tr>
            </thead>
            <tbody>
              {matrix.chakraRows.map((row) => (
                <tr key={row.name}>
                  <td>
                    <span style={{ color: row.tone }}>{row.name}</span>
                  </td>
                  <td>{row.physics}</td>
                  <td>{row.energy}</td>
                  <td>{row.emotion}</td>
                </tr>
              ))}
              <tr className="chakra-table__total">
                <td>Итого</td>
                <td>{matrix.totals.physics}</td>
                <td>{matrix.totals.energy}</td>
                <td>{matrix.totals.emotion}</td>
              </tr>
            </tbody>
          </table>
        </article>

        <article className="section-card">
          <h3>Ключ к матрице</h3>
          <p className="panel-copy">
            Визуал и таблица синхронизированы с эталонным калькулятором матрицы судьбы. Так меньше шансов, что одна и та же дата внезапно начнёт жить двумя разными оккультными жизнями.
          </p>
        </article>
      </div>

      <div className="destiny-matrix__canvas">
        <div className="destiny-matrix__remote-svg" dangerouslySetInnerHTML={{ __html: matrix.svgHtml }} />
      </div>
    </section>
  );
}
