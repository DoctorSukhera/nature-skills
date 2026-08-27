from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import base64
import json
import time
import requests
from io import BytesIO

try:
    from PIL import Image
except Exception:
    Image = None


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
        self.images_generate_url = "https://api.openai.com/v1/images/generations"

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

    def _base_payload(self, *, instructions: str, schema_name: str, schema: dict[str, Any], max_output_tokens: int, web_search: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "instructions": instructions,
            "reasoning": {"effort": self.reasoning_effort},
            "text": {"format": {"type": "json_schema", "name": schema_name, "schema": schema, "strict": True}},
            "max_output_tokens": max_output_tokens,
            "store": False,
            "prompt_cache_key": "nanomax-nature-editor-v9",
        }
        if web_search:
            payload["tools"] = [{"type": "web_search_preview"}]
            payload["tool_choice"] = "auto"
            payload["include"] = ["web_search_call.action.sources"]
        return payload

    def structured(self, *, instructions: str, input_text: str, schema_name: str, schema: dict[str, Any], max_output_tokens: int = 64000, web_search: bool = False) -> ApiResult:
        payload = self._base_payload(instructions=instructions, schema_name=schema_name, schema=schema, max_output_tokens=max_output_tokens, web_search=web_search)
        payload["input"] = input_text
        result = self._post_json(payload)
        if result.parsed is None:
            raise RuntimeError("Structured response was not valid JSON.")
        return result

    @staticmethod
    def _vision_ready(blob: bytes, max_dim: int = 1800) -> tuple[bytes, str]:
        if Image is None:
            return blob, "image/png"
        try:
            im = Image.open(BytesIO(blob)).convert("RGB")
            if max(im.size) > max_dim:
                scale = max_dim / max(im.size)
                im = im.resize((max(1, int(im.width*scale)), max(1, int(im.height*scale))))
            out = BytesIO(); im.save(out, format="JPEG", quality=88, optimize=True)
            return out.getvalue(), "image/jpeg"
        except Exception:
            return blob, "image/png"

    def structured_with_images(self, *, instructions: str, input_text: str, images: list[dict[str, Any]], schema_name: str, schema: dict[str, Any], max_output_tokens: int = 32000, web_search: bool = False) -> ApiResult:
        payload = self._base_payload(instructions=instructions, schema_name=schema_name, schema=schema, max_output_tokens=max_output_tokens, web_search=web_search)
        content: list[dict[str, Any]] = [{"type":"input_text", "text":input_text}]
        for i, img in enumerate(images, 1):
            blob, mime = self._vision_ready(img["bytes"])
            data_url = f"data:{mime};base64," + base64.b64encode(blob).decode("ascii")
            content.append({"type":"input_text", "text":f"IMAGE ASSET {i}: {img.get('name','image')}"})
            content.append({"type":"input_image", "image_url":data_url, "detail":"high"})
        payload["input"] = [{"role":"user", "content":content}]
        result = self._post_json(payload)
        if result.parsed is None:
            raise RuntimeError("Multimodal structured response was not valid JSON.")
        return result

    def edit_image(self, *, image_bytes: bytes, filename: str, prompt: str, image_model: str = "gpt-image-2", size: str = "1536x1024") -> bytes:
        files = {"image": (filename, image_bytes)}
        data = {"model": image_model, "prompt": prompt, "size": size}
        response = requests.post(self.images_edit_url, headers=self.headers, files=files, data=data, timeout=self.timeout)
        return self._decode_image_response(response)

    def generate_image(self, *, prompt: str, image_model: str = "gpt-image-2", size: str = "1536x1024") -> bytes:
        headers = {**self.headers, "Content-Type":"application/json"}
        response = requests.post(self.images_generate_url, headers=headers, json={"model":image_model,"prompt":prompt,"size":size}, timeout=self.timeout)
        return self._decode_image_response(response)

    def _decode_image_response(self, response) -> bytes:
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
            r = requests.get(url, timeout=self.timeout); r.raise_for_status(); return r.content
        raise RuntimeError("Image request returned no image data.")
