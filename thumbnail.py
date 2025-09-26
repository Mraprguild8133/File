# create_thumbnail.py
from PIL import Image, ImageDraw, ImageFont
import os

def create_default_thumbnail():
    """Create a default thumbnail if none exists"""
    if not os.path.exists("thumbnail.jpg"):
        img = Image.new('RGB', (320, 320), color='#2563eb')
        d = ImageDraw.Draw(img)
        
        # Add text (you can customize this)
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
            
        d.text((100, 140), "TURBO BOT", fill='white', font=font)
        img.save("thumbnail.jpg")
        print("Default thumbnail created!")

if __name__ == "__main__":
    create_default_thumbnail()
