import os
import logging
import asyncio
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class FaceMemoryStorage:
    def __init__(self, base_dir: str = "data/faces"):
        self.base_dir = base_dir
        self._ensure_directory()
        
    def _ensure_directory(self):
        """Ensure the faces directory exists"""
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)
            
    async def save_face(self, name: str, image_data: bytes, extension: str = "jpg") -> str:
        """Save a face image with the given name"""
        # Sanitize filename
        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).strip()
        if not safe_name:
            raise ValueError("Invalid name")
            
        filename = f"{safe_name}.{extension}"
        filepath = os.path.join(self.base_dir, filename)
        
        def _write():
            with open(filepath, 'wb') as f:
                f.write(image_data)
                
        try:
            await asyncio.to_thread(_write)
            logger.info(f"Saved face for {safe_name} at {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Failed to save face image: {e}")
            raise

    def get_known_faces(self) -> Dict[str, str]:
        """Get a dictionary of {name: filepath} for all known faces"""
        faces = {}
        if not os.path.exists(self.base_dir):
            return faces
            
        for filename in os.listdir(self.base_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.base_dir, filename)
                faces[name] = filepath
        return faces

    def delete_face(self, name: str) -> bool:
        """Delete a face by name"""
        faces = self.get_known_faces()
        if name in faces:
            try:
                os.remove(faces[name])
                return True
            except Exception as e:
                logger.error(f"Failed to delete face {name}: {e}")
                return False
        return False
