from config import LLMConfig
from .base_client import BaseClient
import openai


class OpenRouterClient(BaseClient):
    """OpenRouter API Client"""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM7 client"""
        super().__init__(config=config)
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key = config.key,
        )
    
    def generate_text(self, user_prompt, system_prompt = None, story_context = None):
        messages = [
            {
                "role": "system",
                "content": f"""
                {system_prompt}
                Never repeat or paraphrase provided context.
                Background (do not restate): 
                {story_context}
                Do not repeat or paraphrase the background. Focus only on generating new content.
                """
            },
            {
                "role": "user",
                "content": f"""
                {user_prompt}

                Do not repeat or paraphrase the background. Focus only on generating new content.
                """
            }
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model["repo"],
                temperature=self.config.generation['temperature'] or 0.8,
                messages=messages,
                # max_completion_tokens=self.config.generation["max_tokens"]

            )
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating text: {e}")
            raise
    
    