import asyncio
import base64
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from faster_whisper import WhisperModel
from openai import AsyncOpenAI

logger = logging.getLogger("ord.core.llm_router")


@dataclass
class LLMRouteRequest:
    prompt: str
    system_prompt: str = ""
    use_vision: bool = False
    image_path: Optional[str] = None
    prefer_offline: Optional[bool] = None
    temperature: float = 0.2
    max_tokens: int = 1024


class LLMRouter:
    """
    Hybrid router:
    - Offline: Ollama (default first hop when enabled)
    - Online: OpenAI GPT-4o / user-specified online model
    - Optional Grok-compatible endpoint via OpenAI-compatible base URL
    - Voice transcription: faster-whisper
    """

    def __init__(self) -> None:
        self.use_offline_default = os.getenv("USE_OFFLINE", "true").lower() == "true"
        self.offline_model = os.getenv("OFFLINE_MODEL", "llama3.1:8b")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        self.online_model = os.getenv("ONLINE_MODEL", "gpt-4o")
        self.vision_model = os.getenv("VISION_MODEL", "gpt-4o")

        # If GROK_API_KEY exists, we can use OpenAI-compatible client on xAI endpoint.
        self.grok_api_key = os.getenv("GROK_API_KEY")
        self.grok_model = os.getenv("GROK_MODEL", "grok-2-latest")
        self.grok_base_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")

        self.openai_client: Optional[AsyncOpenAI] = None
        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        self.grok_client: Optional[AsyncOpenAI] = None
        if self.grok_api_key:
            self.grok_client = AsyncOpenAI(api_key=self.grok_api_key, base_url=self.grok_base_url)

        whisper_model_name = os.getenv("WHISPER_MODEL", "base")
        self.whisper = WhisperModel(whisper_model_name, device="cpu", compute_type="int8")
        self.http = httpx.AsyncClient(timeout=90)

        logger.info("LLMRouter ready: offline=%s offline_model=%s online_model=%s", self.use_offline_default, self.offline_model, self.online_model)

    async def transcribe_voice(self, audio_path: str, language: Optional[str] = None) -> str:
        """Transcribe audio file via faster-whisper."""
        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        def _tx() -> str:
            segments, _info = self.whisper.transcribe(str(audio_file), language=language)
            return " ".join(seg.text.strip() for seg in segments if seg.text.strip())

        try:
            return await asyncio.to_thread(_tx)
        except Exception as exc:
            logger.exception("Voice transcription failed: %s", exc)
            raise

    async def route(self, prompt: str, system_prompt: str = "", use_vision: bool = False, image_path: Optional[str] = None, prefer_offline: Optional[bool] = None, provider: Optional[str] = None) -> str:
        request = LLMRouteRequest(
            prompt=prompt,
            system_prompt=system_prompt,
            use_vision=use_vision,
            image_path=image_path,
            prefer_offline=prefer_offline,
        )
        return await self.route_request(request, provider=provider)

    async def route_request(self, request: LLMRouteRequest, provider: Optional[str] = None) -> str:
        full_prompt = f"{request.system_prompt}\n\n{request.prompt}".strip() if request.system_prompt else request.prompt
        use_offline = self.use_offline_default if request.prefer_offline is None else request.prefer_offline

        # 1) Forced provider path
        if provider:
            return await self._route_by_provider(provider, request, full_prompt)

        # 2) Hybrid preference
        if use_offline and not request.use_vision:
            try:
                return await self._ollama_generate(full_prompt)
            except Exception as exc:
                logger.warning("Offline route failed; falling back online. error=%s", exc)

        # 3) online fallback
        if self.openai_client:
            return await self._openai_generate(request, full_prompt)
        if self.grok_client:
            return await self._grok_generate(full_prompt, request)

        raise RuntimeError("No viable LLM provider configured. Set OPENAI_API_KEY or GROK_API_KEY, or run Ollama.")

    async def _route_by_provider(self, provider: str, request: LLMRouteRequest, full_prompt: str) -> str:
        provider = provider.lower()
        if provider == "ollama":
            return await self._ollama_generate(full_prompt)
        if provider in {"openai", "gpt-4o", "gpt"}:
            if not self.openai_client:
                raise RuntimeError("OPENAI_API_KEY missing")
            return await self._openai_generate(request, full_prompt)
        if provider in {"grok", "xai"}:
            if not self.grok_client:
                raise RuntimeError("GROK_API_KEY missing")
            return await self._grok_generate(full_prompt, request)
        raise ValueError(f"Unsupported provider: {provider}")

    async def _ollama_generate(self, full_prompt: str) -> str:
        payload = {"model": self.offline_model, "prompt": full_prompt, "stream": False}
        response = await self.http.post(f"{self.ollama_base_url}/api/generate", json=payload)
        response.raise_for_status()
        return response.json().get("response", "")

    async def _openai_generate(self, request: LLMRouteRequest, full_prompt: str) -> str:
        assert self.openai_client is not None
        if request.use_vision and request.image_path:
            image_b64 = base64.b64encode(Path(request.image_path).read_bytes()).decode("utf-8")
            messages: List[Dict[str, Any]] = [
                {"role": "system", "content": "You are Ord: warm, loving, and highly competent."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                    ],
                },
            ]
            resp = await self.openai_client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            return resp.choices[0].message.content or ""

        resp = await self.openai_client.chat.completions.create(
            model=self.online_model,
            messages=[
                {"role": "system", "content": "You are Ord: warm, loving, and highly competent."},
                {"role": "user", "content": full_prompt},
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def _grok_generate(self, full_prompt: str, request: LLMRouteRequest) -> str:
        assert self.grok_client is not None
        # Grok endpoint is treated as OpenAI-compatible chat completions.
        resp = await self.grok_client.chat.completions.create(
            model=self.grok_model,
            messages=[
                {"role": "system", "content": "You are Ord: warm, loving, and highly competent."},
                {"role": "user", "content": full_prompt},
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        return resp.choices[0].message.content or ""


llm_router = LLMRouter()
