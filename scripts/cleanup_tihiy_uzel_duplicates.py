from pathlib import Path

from backend.database import Database
from backend.models import EvidenceCreatePayload, RelationCreatePayload

V_PARTICIPANT_ID = "d04dfcb3-f6ab-4ebc-860d-92d763463f53"
S_PARTICIPANT_ID = "0479c50e-c250-4d71-b2ce-49f11fca4a53"


def main() -> None:
    db = Database(Path("app_data"))

    with db.connect() as conn:
        conn.execute("DELETE FROM evidence WHERE participant_id=?", (V_PARTICIPANT_ID,))
        conn.execute("DELETE FROM relations WHERE participant_id=?", (V_PARTICIPANT_ID,))
        conn.execute("DELETE FROM relations WHERE participant_id=?", (S_PARTICIPANT_ID,))

    for payload in [
        EvidenceCreatePayload(
            title="Пропуск на склад",
            category="Документ",
            status="Изъято",
            details="Пропуск на склад с частично стертым номером.",
        ),
        EvidenceCreatePayload(
            title="Записка с адресом",
            category="Бумажный след",
            status="Зафиксировано",
            details="Записка с адресом в Белгороде и временем встречи.",
        ),
        EvidenceCreatePayload(
            title="Скриншот переписки",
            category="Цифровой след",
            status="Проверяется",
            details="Скриншот переписки с упоминанием «тихой доставки».",
        ),
        EvidenceCreatePayload(
            title="Описание автомобиля",
            category="Свидетельское показание",
            status="Подтверждено",
            details="Свидетельское описание автомобиля, совпадающее с машиной Вячеслава.",
        ),
    ]:
        db.create_evidence(V_PARTICIPANT_ID, payload)

    for payload in [
        RelationCreatePayload(
            target_type="person",
            target_label="Софья Игоревна Лебедева",
            relation_type="Близкая личная связь",
            confidence=91,
        ),
        RelationCreatePayload(
            target_type="place",
            target_label="Гаражный бокс №17",
            relation_type="Место хранения",
            confidence=78,
        ),
        RelationCreatePayload(
            target_type="place",
            target_label="Складской район",
            relation_type="Регулярное появление",
            confidence=83,
        ),
        RelationCreatePayload(
            target_type="person",
            target_label="Неустановленный посредник",
            relation_type="Связь через третьих лиц",
            confidence=64,
        ),
    ]:
        db.create_relation(V_PARTICIPANT_ID, payload)

    for payload in [
        RelationCreatePayload(
            target_type="person",
            target_label="Вячеслав Алексеевич Морозов",
            relation_type="Личная связь",
            confidence=90,
        ),
        RelationCreatePayload(
            target_type="place",
            target_label="Кофейня рядом с вокзалом",
            relation_type="Точка контакта",
            confidence=62,
        ),
    ]:
        db.create_relation(S_PARTICIPANT_ID, payload)

    print("ok")


if __name__ == "__main__":
    main()
