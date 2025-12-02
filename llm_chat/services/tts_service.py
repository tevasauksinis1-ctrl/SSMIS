"""TTS (Text-to-Speech) service using OpenAI-compatible API."""

import asyncio
import io
import tempfile
from pathlib import Path
from typing import Optional, List

import aiohttp

from llm_chat.utils.logger import setup_logger


logger = setup_logger(__name__)


class TTSService:
    """Text-to-Speech service using OpenAI-compatible API."""
    
    # Available voices for OpenAI-compatible TTS
    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def __init__(
        self,
        api_url: str = "http://localhost:8000/v1/audio/speech",
        model: str = "tts-1",
        voice: str = "alloy",
        speed: float = 1.0,
    ):
        """Initialize the TTS service.
        
        Args:
            api_url: TTS API endpoint URL.
            model: TTS model to use.
            voice: Voice to use.
            speed: Speech speed (0.25 to 4.0).
        """
        self.api_url = api_url
        self.model = model
        self.voice = voice
        self.speed = max(0.25, min(4.0, speed))
        self._session: Optional[aiohttp.ClientSession] = None
        self._enabled = True
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self) -> None:
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    @property
    def enabled(self) -> bool:
        """Check if TTS is enabled."""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set TTS enabled state."""
        self._enabled = value
    
    def set_voice(self, voice: str) -> None:
        """Set the voice to use.
        
        Args:
            voice: Voice name.
        """
        if voice not in self.VOICES:
            logger.warning(f"Unknown voice: {voice}, using 'alloy'")
            voice = "alloy"
        self.voice = voice
    
    def set_speed(self, speed: float) -> None:
        """Set the speech speed.
        
        Args:
            speed: Speed between 0.25 and 4.0.
        """
        self.speed = max(0.25, min(4.0, speed))
    
    async def health_check(self) -> bool:
        """Check if TTS service is available.
        
        Returns:
            True if service is reachable, False otherwise.
        """
        try:
            # Try to generate a short test audio
            audio = await self.synthesize("test")
            return audio is not None and len(audio) > 0
        except Exception as e:
            logger.debug(f"TTS health check failed: {e}")
            return False
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        response_format: str = "mp3",
    ) -> bytes:
        """Synthesize speech from text.
        
        Args:
            text: Text to synthesize.
            voice: Optional voice override.
            speed: Optional speed override.
            response_format: Audio format (mp3, opus, aac, flac).
            
        Returns:
            Audio data as bytes.
        """
        if not self._enabled:
            raise RuntimeError("TTS is disabled")
        
        session = await self._get_session()
        
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice or self.voice,
            "speed": speed or self.speed,
            "response_format": response_format,
        }
        
        async with session.post(
            self.api_url,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"TTS API error: {response.status} - {error_text}")
            
            return await response.read()
    
    async def synthesize_to_file(
        self,
        text: str,
        output_path: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        response_format: str = "mp3",
    ) -> str:
        """Synthesize speech and save to file.
        
        Args:
            text: Text to synthesize.
            output_path: Path to save audio file.
            voice: Optional voice override.
            speed: Optional speed override.
            response_format: Audio format.
            
        Returns:
            Path to saved audio file.
        """
        audio_data = await self.synthesize(
            text=text,
            voice=voice,
            speed=speed,
            response_format=response_format,
        )
        
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, "wb") as f:
            f.write(audio_data)
        
        return str(output)
    
    async def synthesize_to_temp(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        response_format: str = "mp3",
    ) -> str:
        """Synthesize speech to a temporary file.
        
        Args:
            text: Text to synthesize.
            voice: Optional voice override.
            speed: Optional speed override.
            response_format: Audio format.
            
        Returns:
            Path to temporary audio file.
        """
        audio_data = await self.synthesize(
            text=text,
            voice=voice,
            speed=speed,
            response_format=response_format,
        )
        
        # Create temp file with appropriate extension
        suffix = f".{response_format}"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_data)
            return f.name
    
    def list_voices(self) -> List[str]:
        """Get list of available voices.
        
        Returns:
            List of voice names.
        """
        return self.VOICES.copy()
