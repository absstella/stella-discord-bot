"""
VOICEVOX Client
Integrates with VOICEVOX API for high-quality Japanese TTS
"""

import logging
import aiohttp
import json
import os
from typing import Optional

logger = logging.getLogger(__name__)

class VOICEVOXClient:
    """Client for VOICEVOX API"""
    
    def __init__(self, host: str = None, port: int = None):
        # Use environment variables if not provided
        self.host = host or os.environ.get("VOICEVOX_HOST", "127.0.0.1")
        self.port = port or int(os.environ.get("VOICEVOX_PORT", "50021"))
        self.base_url = f"http://{self.host}:{self.port}"
        self.available = False
        logger.info(f"VOICEVOX Client initialized: {self.base_url}")
        
    async def check_availability(self) -> bool:
        """Check if VOICEVOX server is running"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/version", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status == 200:
                        self.available = True
                        version = await response.text()
                        logger.info(f"VOICEVOX server found: {version}")
                        return True
        except Exception as e:
            logger.debug(f"VOICEVOX not available: {e}")
            self.available = False
        return False
    
    async def get_speakers(self) -> list:
        """Get available speakers"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/speakers") as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Failed to get speakers: {e}")
        return []
    
    async def synthesize(self, text: str, speaker_id: int = 3, output_file: str = "output.wav") -> bool:
        """
        Synthesize speech using VOICEVOX
        
        Args:
            text: Text to synthesize
            speaker_id: Speaker ID (default: 3 = ずんだもん)
            output_file: Output file path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Step 1: Create audio query
                params = {"text": text, "speaker": speaker_id}
                async with session.post(f"{self.base_url}/audio_query", params=params) as response:
                    if response.status != 200:
                        logger.error(f"Audio query failed: {response.status}")
                        return False
                    query = await response.json()
                
                # Step 2: Synthesize
                params = {"speaker": speaker_id}
                headers = {"Content-Type": "application/json"}
                async with session.post(
                    f"{self.base_url}/synthesis",
                    params=params,
                    json=query,
                    headers=headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Synthesis failed: {response.status}")
                        return False
                    
                    # Save audio
                    audio_data = await response.read()
                    with open(output_file, "wb") as f:
                        f.write(audio_data)
                    
                    logger.info(f"Synthesized audio saved to {output_file}")
                    return True
                    
        except Exception as e:
            logger.error(f"VOICEVOX synthesis error: {e}")
            return False
