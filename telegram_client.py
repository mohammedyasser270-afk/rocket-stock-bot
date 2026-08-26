from __future__ import annotations

import requests


class TelegramClient:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send(self, text: str) -> None:
        # Telegram messages are limited to 4096 characters.
        chunks = self._split_message(text, 3900)
        for chunk in chunks:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                data={
                    "chat_id": self.chat_id,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
                timeout=30,
            )
            response.raise_for_status()

    @staticmethod
    def _split_message(text: str, max_length: int) -> list[str]:
        if len(text) <= max_length:
            return [text]

        chunks: list[str] = []
        current = ""
        for line in text.splitlines(keepends=True):
            if len(current) + len(line) > max_length and current:
                chunks.append(current.rstrip())
                current = ""
            current += line
        if current:
            chunks.append(current.rstrip())
        return chunks
