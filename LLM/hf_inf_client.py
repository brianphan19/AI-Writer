from huggingface_hub import InferenceClient
from typing import List, Dict, Optional

from config import LLMConfig
from .base_client import BaseClient


class InfClient(BaseClient):
    """Hugging Face Inference API Client"""
    
    def __init__(self, config: LLMConfig):
        """Initialize HF client"""
        super().__init__(config=config)

        if not config.key:
            raise ValueError("HUGGINGFACE_TOKEN is required")
        self.client = InferenceClient(token=config.key)
    
    def generate_text(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        story_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        messages = [
           {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"""# Story Context
                {story_context}

                # Task
                {user_prompt}"""
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model['repo'],
                messages=messages,
                max_tokens=self.config.generation['max_tokens'],
                temperature=self.config.generation['temperature'],
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating text: {e}")
            raise
    
    