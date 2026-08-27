from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import base64
import json
import time
import requests


@dataclass
class ApiResult:
    text: str
    parsed: dict[str, Any] | None
    response_id: str | None
    usage: dict[str, Any]
    raw: dict[str, Any]


class OpenAIResponsesClient:
    def __init__(self, api_key: str, model: str, reasoning_effort: str = "high", timeout: int = 900):
        self.api_key = api_key
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout = timeout
        self.responses_url = "https://api.openai.com/v1/responses"
        self.images_edit_url = "https://api.openai.com/v1/images/edits"

    @property
    def headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    @staticmethod
    def _extract_output_text(data: dict[str, Any]) -> str:
        chunks: list[str] = []
        for item in data.get("output", []) or []:
            if item.get("type") != "message":
                continue
            for content in item.get("content", []) or []:
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()

    def _post_json(self, payload: dict[str, Any]) -> ApiResult:
        headers = {**self.headers, "Content-Type": "application/json"}
        response = None
        for attempt in range(3):
            response = requests.post(self.responses_url, headers=headers, json=payload, timeout=self.timeout)
            if response.status_code in {408,409,429,500,502,503,504} and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            break
        if response is None:
            raise RuntimeError("OpenAI request failed before a response was received.")
        if response.status_code >= 400:
            try:
                msg = response.json().get("error", {}).get("message", response.text)
            except Exception:
                msg = response.text
            raise RuntimeError(f"OpenAI API error {response.status_code}: {msg}")
        data = response.json()
        if data.get("error"):
            raise RuntimeError(str(data["error"]))
        text = self._extract_output_text(data)
        parsed = None
        if text:
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                pass
        return ApiResult(text, parsed, data.get("id"), data.get("usage") or {}, data)

    def structured(self, *, instructions: str, input_text: str, schema_name: str, schema: dict[str, Any], max_output_tokens: int = 64000, web_search: bool = False) -> ApiResult:
        payload: dict[str, Any] = {
            "model": self.model,
            "instructions": instructions,
            "input": input_text,
            "reasoning": {"effort": self.reasoning_effort},
            "text": {"format": {"type": "json_schema", "name": schema_name, "schema": schema, "strict": True}},
            "max_output_tokens": max_output_tokens,
            "store": False,
            "prompt_cache_key": "nanomax-nature-editor-v6",
        }
        if web_search:
            payload["tools"] = [{"type": "web_search_preview"}]
            payload["tool_choice"] = "auto"
            payload["include"] = ["web_search_call.action.sources"]
        result = self._post_json(payload)
        if result.parsed is None:
            raise RuntimeError("Structured response was not valid JSON.")
        return result

    def edit_image(self, *, image_bytes: bytes, filename: str, prompt: str, image_model: str = "gpt-image-2", size: str = "1536x1024") -> bytes:
        files = {"image": (filename, image_bytes)}
        data = {"model": image_model, "prompt": prompt, "size": size}
        response = requests.post(self.images_edit_url, headers=self.headers, files=files, data=data, timeout=self.timeout)
        if response.status_code >= 400:
            try:
                msg = response.json().get("error", {}).get("message", response.text)
            except Exception:
                msg = response.text
            raise RuntimeError(f"Image API error {response.status_code}: {msg}")
        payload = response.json()
        item = (payload.get("data") or [{}])[0]
        b64 = item.get("b64_json")
        if b64:
            return base64.b64decode(b64)
        url = item.get("url")
        if url:
            r = requests.get(url, timeout=self.timeout)
            r.raise_for_status()
            return r.content
        raise RuntimeError("Image edit returned no image data.")
