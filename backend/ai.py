import json
import os
from dataclasses import dataclass

from openai import OpenAI

SYSTEM_PROMPT = """\
You are an AI assistant that helps manage a Kanban board.

The board uses this JSON format:
{
  "columns": [{"id": "string", "title": "string", "cardIds": ["string"]}],
  "cards": {"<card-id>": {"id": "string", "title": "string", "details": "string"}}
}

Column ids are fixed: col-backlog, col-discovery, col-progress, col-review, col-done.
Card ids are generated strings (e.g. "card-1", "card-abc123ef").

When the user asks you to make changes, respond with this JSON:
{"message": "your response", "board_update": <full updated board JSON or null>}

Rules:
- Always return valid JSON with no markdown or code fences.
- Set board_update to null when no board changes are needed.
- When making changes, return the complete board (not just the changed parts).
- New card ids must be unique; use a short random string like "card-<6 chars>".
"""


@dataclass
class AIResponse:
    message: str
    board_update: dict | None


def chat(user_message: str, history: list[dict], board: dict) -> AIResponse:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + f"\n\nCurrent board:\n{json.dumps(board)}",
        },
        *history,
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
        return AIResponse(
            message=parsed.get("message", ""),
            board_update=parsed.get("board_update") or None,
        )
    except (json.JSONDecodeError, AttributeError):
        return AIResponse(message=content or "Sorry, I could not process that.", board_update=None)
