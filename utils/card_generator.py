import discord
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import io
import random
import os
import aiohttp
import logging

logger = logging.getLogger(__name__)

# Constants
CARD_WIDTH = 400
CARD_HEIGHT = 600
FONT_PATH = "C:\\Windows\\Fonts\\meiryo.ttc" # Windows Japanese Font
if not os.path.exists(FONT_PATH):
    FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf" # Fallback

RARITY_CONFIG = {
    "N": {"color": (200, 200, 200), "stars": 1, "border": (150, 150, 150)},
    "R": {"color": (0, 150, 255), "stars": 2, "border": (0, 100, 200)},
    "SR": {"color": (255, 215, 0), "stars": 3, "border": (218, 165, 32)},
    "UR": {"color": (255, 50, 50), "stars": 4, "border": (200, 0, 0)},
    "LE": {"color": (200, 0, 255), "stars": 5, "border": (150, 0, 200)}
}

class CardGenerator:
    def __init__(self):
        self.font_path = FONT_PATH
        self.font_cache = {}
        self.base_card_cache = {}

    def get_font(self, size):
        if size in self.font_cache:
            return self.font_cache[size]
            
        try:
            font = ImageFont.truetype(self.font_path, size)
            self.font_cache[size] = font
            return font
        except:
            return ImageFont.load_default()

    async def _download_image(self, url):
        """Download image asynchronously"""
        if not url:
            return None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
        return None

    async def generate_card(self, title, name, rarity, image_url=None, item_type="member", stats=None, image_path=None):
        """Generate a single card image with TCG style (Async wrapper)"""
        logger.info(f"generate_card called for {name} ({rarity})")
        image_bytes = None
        if image_url:
            logger.info(f"Downloading image from {image_url}")
            image_bytes = await self._download_image(image_url)
            logger.info(f"Download complete: {len(image_bytes) if image_bytes else 0} bytes")
            
        logger.info("Offloading sync generation to thread")
        return await asyncio.to_thread(
            self._generate_card_sync, title, name, rarity, image_bytes, item_type, stats, image_path
        )

    def _generate_card_sync(self, title, name, rarity, image_bytes=None, item_type="member", stats=None, image_path=None, skip_holo=False):
        """Generate a single card image with TCG style (Synchronous implementation)"""
        logger.info(f"_generate_card_sync started for {name}")
        config = RARITY_CONFIG.get(rarity, RARITY_CONFIG["N"])
        
        # Check cache for base image
        if rarity in self.base_card_cache:
            img = self.base_card_cache[rarity].copy()
            draw = ImageDraw.Draw(img)
        else:
            # Create base
            img = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (20, 20, 30, 255))
            draw = ImageDraw.Draw(img)
            
            # 1. Outer Border (Metallic effect simulation)
            border_color = config["border"]
            draw.rectangle([0, 0, CARD_WIDTH-1, CARD_HEIGHT-1], outline=border_color, width=15)
            draw.rectangle([5, 5, CARD_WIDTH-6, CARD_HEIGHT-6], outline=(255, 255, 255), width=2) # Inner highlight

            # 2. Inner Background
            draw.rectangle([15, 15, CARD_WIDTH-16, CARD_HEIGHT-16], fill=(30, 30, 40, 255))

            # 3. Main Image Area
            image_y_start = 80
            image_height = 300
            draw.rectangle([25, image_y_start, CARD_WIDTH-26, image_y_start+image_height], fill=(10, 10, 20), outline=border_color, width=3)
            
            # 4. Header (Title & Rarity)
            # Title Bar
            draw.rectangle([20, 20, CARD_WIDTH-21, 70], fill=(40, 40, 50), outline=border_color, width=2)
            
            # Rarity Stars (Top Right) - Static part
            star_font = self.get_font(24)
            stars = "★" * config["stars"]
            draw.text((CARD_WIDTH-30, 45), stars, font=star_font, fill=config["color"], anchor="rm", stroke_width=1, stroke_fill="black")

            # 5. Name Bar (Below Image)
            name_y = image_y_start + image_height + 10
            draw.rectangle([20, name_y, CARD_WIDTH-21, name_y+50], fill=(50, 50, 60), outline=border_color, width=2)
            
            # 6. Stats Area Labels (Static)
            stats_y = name_y + 60
            draw.text((60, stats_y), "ATK", font=self.get_font(18), fill=(255, 100, 100))
            draw.text((CARD_WIDTH-100, stats_y), "DEF", font=self.get_font(18), fill=(100, 100, 255))
            
            # Flavor Text / Description (Center Bottom)
            desc_font = self.get_font(14)
            desc = "STELLA TCG COLLECTION"
            draw.text((CARD_WIDTH//2, CARD_HEIGHT-30), desc, font=desc_font, fill=(100, 100, 100), anchor="mm")
            
            # Save to cache
            self.base_card_cache[rarity] = img.copy()
        
        # --- Dynamic Content Drawing ---
        
        # Load Image
        image_y_start = 80
        image_height = 300
        avatar = None
        try:
            if image_path and os.path.exists(image_path):
                avatar = Image.open(image_path).convert("RGBA")
            elif image_bytes:
                avatar = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        except Exception as e:
            logger.error(f"Failed to load image: {e}")

        # Paste Image
        if avatar:
            try:
                # Resize to fit
                target_size = image_height - 10
                avatar = avatar.resize((target_size, target_size), Image.Resampling.LANCZOS)
                
                x = (CARD_WIDTH - target_size) // 2
                y = image_y_start + 5
                
                if item_type == "member":
                    # Circular mask for members? Or keep square for TCG feel?
                    # Let's keep square for TCG feel, maybe rounded corners
                    mask = Image.new("L", (target_size, target_size), 0)
                    draw_mask = ImageDraw.Draw(mask)
                    draw_mask.rounded_rectangle((0, 0, target_size, target_size), radius=20, fill=255)
                    img.paste(avatar, (x, y), mask)
                else:
                    img.paste(avatar, (x, y))
            except Exception as e:
                logger.error(f"Failed to paste image: {e}")
        else:
             # Text Placeholder
             try:
                 icon_font = self.get_font(80)
                 draw.text((CARD_WIDTH//2, image_y_start + image_height//2), "🎁", font=icon_font, fill="white", anchor="mm")
             except:
                 pass

        # 4. Header (Title & Rarity) - Dynamic Text
        # Title Text
        title_font = self.get_font(20)
        draw.text((30, 45), title[:20], font=title_font, fill=(220, 220, 220), anchor="lm")
        
        # 5. Name Bar (Below Image) - Dynamic Text
        name_y = image_y_start + image_height + 10
        name_font = self.get_font(28)
        draw.text((CARD_WIDTH//2, name_y+25), name, font=name_font, fill="white", anchor="mm", stroke_width=1, stroke_fill="black")

        # 6. Stats Area (Bottom) - Dynamic Values
        if stats:
            stats_y = name_y + 60
            # ATK Value
            draw.text((60, stats_y+30), str(stats.get('attack', 0)), font=self.get_font(32), fill="white", stroke_width=1, stroke_fill="black")
            
            # DEF Value
            draw.text((CARD_WIDTH-100, stats_y+30), str(stats.get('defense', 0)), font=self.get_font(32), fill="white", stroke_width=1, stroke_fill="black")

        # 7. Holo Effect (Overlay)
        if not skip_holo and rarity in ["SR", "UR", "LE"]:
            overlay = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)
            
            # Diagonal shine
            for i in range(-CARD_HEIGHT, CARD_WIDTH + CARD_HEIGHT, 60):
                draw_overlay.line([(i, CARD_HEIGHT), (i+CARD_HEIGHT, 0)], fill=(255, 255, 255, 20), width=10)
            
            img = Image.alpha_composite(img, overlay)

        return img

    async def generate_result_image(self, cards_data):
        """Generate a summary image for multiple pulls (Async wrapper)"""
        logger.info(f"generate_result_image called for {len(cards_data)} cards")
        # Download all images concurrently
        tasks = []
        for card in cards_data:
            if card.get('image_url'):
                tasks.append(self._download_image(card['image_url']))
            else:
                # Return None for no URL
                tasks.append(asyncio.sleep(0, result=None))
        
        # Execute all downloads
        logger.info("Starting concurrent image downloads")
        results = await asyncio.gather(*tasks)
        logger.info("All image downloads completed")
        
        # Inject bytes into card data for sync method
        cards_data_with_bytes = []
        for i, card in enumerate(cards_data):
            c = card.copy()
            c['image_bytes'] = results[i]
            cards_data_with_bytes.append(c)

        return await asyncio.to_thread(self._generate_result_image_sync, cards_data_with_bytes)

    def _generate_result_image_sync(self, cards_data):
        """Generate a summary image for multiple pulls (Synchronous implementation)"""
        logger.info(f"_generate_result_image_sync started for {len(cards_data)} cards")
        cols = 5
        rows = (len(cards_data) + cols - 1) // cols
        
        thumb_w = 200
        thumb_h = 300
        padding = 20
        
        bg_w = cols * (thumb_w + padding) + padding
        bg_h = rows * (thumb_h + padding) + padding
        
        bg = Image.new('RGBA', (bg_w, bg_h), (20, 20, 30, 255))
        
        for i, card_data in enumerate(cards_data):
            # We need to call the sync version here since we are already in a thread
            card_img = self._generate_card_sync(
                card_data['title'], 
                card_data['name'], 
                card_data['rarity'], 
                card_data.get('image_bytes'), # Use bytes we downloaded
                card_data.get('type', 'member'),
                card_data.get('stats'),
                card_data.get('image_path'),
                skip_holo=True # Optimization: Skip holo effect for thumbnails
            )
            
            card_thumb = card_img.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            
            col = i % cols
            row = i // cols
            
            x = padding + col * (thumb_w + padding)
            y = padding + row * (thumb_h + padding)
            
            bg.paste(card_thumb, (x, y))
            
        return bg

    def get_bytes(self, img):
        b = io.BytesIO()
        img.save(b, format='PNG')
        b.seek(0)
        return b
