import os
import base64
import logging
import asyncio
from typing import Optional
import httpx
from openai import AsyncOpenAI
from faster_whisper import WhisperModel

logger = logging.getLogger("ord.llm_router")


class LLMRouter:
    def __init__(self):
        self.use_offline = os.getenv("USE_OFFLINE", "false").lower() == "true"
        self.offline_model = os.getenv("OFFLINE_MODEL", "llama3.1:8b")
        self.online_model = os.getenv("ONLINE_MODEL", "gpt-4o-mini")
        
        # Clients
        api_key = os.getenv("OPENAI_API_KEY")
        self.openai = AsyncOpenAI(api_key=api_key) if api_key else None
        self.http = httpx.AsyncClient(timeout=60)
        
        # Voice
        self.whisper = WhisperModel(os.getenv("WHISPER_MODEL", "small"), device="cpu", compute_type="int8")
        logger.info("✅ LLM Router initialized (Hybrid + Voice + Vision)")

    async def transcribe_voice(self, ogg_path: str) -> str:
        """Transcribe voice with faster-whisper."""
        try:
            segments, _ = await asyncio.to_thread(self.whisper.transcribe, ogg_path)
            return " ".join(seg.text for seg in segments)
        except Exception as e:
            logger.error(f"Voice transcription failed: {e}")
            return "[Transcription failed]"

    async def route(self, prompt: str, system_prompt: str = "", use_vision: bool = False, image_path: Optional[str] = None) -> str:
        """Hybrid routing with fallback."""
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        # Try offline first if enabled
        if self.use_offline:
            try:
                resp = await self.http.post("http://localhost:11434/api/generate", json={"model": self.offline_model, "prompt": full_prompt, "stream": False})
                return resp.json().get("response", "")
            except Exception as e:
                logger.warning(f"Offline fallback failed: {e}. Switching to online...")
        
        # Online fallback
        return await self._online_route(full_prompt, use_vision, image_path)

    async def _online_route(self, prompt: str, use_vision: bool, image_path: Optional[str]) -> str:
        if not self.openai:
            raise RuntimeError("No OpenAI API key configured")
        
        messages = [{"role": "system", "content": "You are Ord: sweet, loving, professional. Maintain warm expertise."}]
        
        if use_vision and image_path:
            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            messages.append({"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]})
            resp = await self.openai.chat.completions.create(model="gpt-4o", messages=messages, max_tokens=2048)
        else:
            messages.append({"role": "user", "content": prompt})
            resp = await self.openai.chat.completions.create(model=self.online_model, messages=messages, max_tokens=2048)
        
        return resp.choices[0].message.content or ""


llm_router = LLMRouter()