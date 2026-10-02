import requests
import io
from openai import OpenAI
import google.generativeai as genai
import anthropic
from config import settings

class AIService:
    """Сервис для работы с AI провайдерами"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        if settings.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        
        if settings.GEMINI_API_KEY:
            genai.configure(api_key=settings.GEMINI_API_KEY)
    
    # =============== TEXT GENERATION ===============
    
    def text_openai(self, prompt, model="gpt-4o-mini"):
        """Генерировать текст через OpenAI"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ты полезный помощник. Отвечай кратко и по существу."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def text_claude(self, prompt, model="claude-3-5-sonnet-20241022"):
        """Генерировать текст через Claude"""
        if not self.anthropic_client:
            raise ValueError("Claude API key not configured")
        
        message = self.anthropic_client.messages.create(
            model=model,
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text
    
    def text_gemini(self, prompt, model="gemini-2.0-flash"):
        """Генерировать текст через Gemini"""
        if not settings.GEMINI_API_KEY:
            raise ValueError("Gemini API key not configured")
        
        model_obj = genai.GenerativeModel(model)
        response = model_obj.generate_content(prompt)
        return response.text
    
    def text(self, prompt, model="gpt"):
        """Генерировать текст"""
        if model == "gpt":
            return self.text_openai(prompt)
        elif model == "claude":
            return self.text_claude(prompt)
        elif model == "gemini":
            return self.text_gemini(prompt)
        else:
            raise ValueError(f"Unknown model: {model}")
    
    # =============== IMAGE GENERATION ===============
    
    def image_openai(self, prompt, size="1024x1024"):
        """Генерировать изображение через OpenAI"""
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")
        
        response = self.openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",
            n=1
        )
        
        return response.data[0].url
    
    def image_stability(self, prompt):
        """Генерировать изображение через Stability AI"""
        if not settings.STABILITY_API_KEY:
            raise ValueError("Stability AI API key not configured")
        
        url = "https://api.stability.ai/v1/generate"
        headers = {
            "authorization": f"Bearer {settings.STABILITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        body = {
            "steps": 40,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "cfg_scale": 7.0,
            "samples": 1,
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=body, timeout=60)
        if response.status_code != 200:
            raise ValueError(f"Stability API error: {response.text}")
        
        data = response.json()
        if data['artifacts']:
            return f"data:image/png;base64,{data['artifacts'][0]['base64']}"
        
        raise ValueError("No image generated")
    
    def image(self, prompt, model="openai"):
        """Генерировать изображение"""
        if model == "openai":
            return self.image_openai(prompt)
        elif model == "stability":
            return self.image_stability(prompt)
        else:
            raise ValueError(f"Unknown model: {model}")
    
    # =============== VIDEO GENERATION ===============
    
    def video_replicate(self, prompt):
        """Генерировать видео через Replicate"""
        if not settings.REPLICATE_API_TOKEN:
            raise ValueError("Replicate API token not configured")
        
        import replicate
        
        try:
            output = replicate.run(
                "genmo/mochi-1:1d0f2ff8be63c20b7b2a9c1b4c1c1c1c1c1c1c1c",
                input={
                    "prompt": prompt,
                    "seed": 0
                }
            )
            return output[0] if isinstance(output, list) else output
        except Exception as e:
            raise ValueError(f"Replicate error: {str(e)}")
    
    def video_fal(self, prompt):
        """Генерировать видео через FAL"""
        if not settings.FAL_KEY:
            raise ValueError("FAL API key not configured")
        
        url = "https://queue.fal.run/fal-ai/fast-video-generation"
        headers = {
            "Authorization": f"Key {settings.FAL_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {"prompt": prompt}
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code != 200:
            raise ValueError(f"FAL API error: {response.text}")
        
        data = response.json()
        return data.get('video')
    
    def video(self, prompt, model="replicate"):
        """Генерировать видео"""
        if model == "replicate":
            return self.video_replicate(prompt)
        elif model == "fal":
            return self.video_fal(prompt)
        else:
            raise ValueError(f"Unknown model: {model}")

ai_service = AIService()
