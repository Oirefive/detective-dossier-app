from __future__ import annotations

import json
from typing import Any

import httpx

from .models import AIDossierRequest, AIDossierResponse, AIPersonCardResponse, AISettings


class AIService:
    def __init__(self, settings: AISettings) -> None:
        self.settings = settings

    def generate_person_card(self, source_text: str) -> AIPersonCardResponse:
        payload = self._chat_json(
            system_prompt=self.settings.card_prompt,
            user_prompt=(
                "Собери карточку человека из этого текста.\n\n"
                f"{source_text.strip()}\n\n"
                "Верни только JSON."
            ),
        )
        return AIPersonCardResponse(
            full_name=self._as_str(payload.get("fullName") or payload.get("full_name")),
            alias_name=self._as_str(payload.get("aliasName") or payload.get("alias_name")),
            birth_date=self._as_date_or_none(payload.get("birthDate") or payload.get("birth_date")),
            biography=self._as_str(payload.get("biography")),
            documents_summary=self._as_str(payload.get("documentsSummary") or payload.get("documents_summary")),
            known_places=self._as_str(payload.get("knownPlaces") or payload.get("known_places")),
            habits=self._as_str(payload.get("habits")),
        )

    def generate_dossier(self, request: AIDossierRequest) -> AIDossierResponse:
        source = {
            "case": request.case.model_dump(by_alias=True) if request.case else None,
            "participant": request.participant.model_dump(by_alias=True) if request.participant else None,
            "person": request.person.model_dump(by_alias=True) if request.person else None,
        }
        payload = self._chat_json(
            system_prompt=self.settings.dossier_prompt,
            user_prompt=(
                "Подготовь краткое досье по этой карточке. Можно уточнить статус и уровень подозрения, "
                "если это следует из данных.\n\n"
                f"{json.dumps(source, ensure_ascii=False, indent=2)}\n\n"
                "Верни только JSON."
            ),
        )
        return AIDossierResponse(
            summary=self._as_str(payload.get("summary")),
            description=self._as_str(payload.get("description")),
            notes=self._as_str(payload.get("notes")),
            status=self._as_str(payload.get("status")),
            suspicion_level=self._clamp_int(payload.get("suspicionLevel") or payload.get("suspicion_level")),
            key_facts=self._as_list(payload.get("keyFacts") or payload.get("key_facts")),
            red_flags=self._as_list(payload.get("redFlags") or payload.get("red_flags")),
            recommendations=self._as_list(payload.get("recommendations")),
        )

    def _chat_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        base_url = self.settings.base_url.rstrip("/")
        if not self.settings.api_key.strip():
            raise ValueError("API key не задан")

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.settings.model,
                    "temperature": 0.3,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )

        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if not isinstance(content, str):
            raise ValueError("Модель вернула неожиданный ответ")
        return self._extract_json(content)

    @staticmethod
    def _extract_json(content: str) -> dict[str, Any]:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]).strip()
        return json.loads(text)

    @staticmethod
    def _as_str(value: Any) -> str:
        return str(value).strip() if value is not None else ""

    @staticmethod
    def _as_date_or_none(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _as_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value is None:
            return []
        text = str(value).strip()
        return [text] if text else []

    @staticmethod
    def _clamp_int(value: Any) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, min(100, number))
