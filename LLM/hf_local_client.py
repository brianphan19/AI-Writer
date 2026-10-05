from typing import List, Dict, Optional
from llama_cpp import Llama
from config import LLMConfig
from .base_client import BaseClient


class LocalClient(BaseClient):
    """Hugging Face Inference API Client"""
    
    def __init__(self, config: LLMConfig):
        """Initialize HF client"""
        super().__init__(config=config)
        self.client = Llama.from_pretrained(
            repo_id=config.model["repo"],
            filename=config.model["quant"],
            n_gpu_layers= config.runtime["gpu_layers"] or -1,
            n_threads= config.runtime["threads"] or 12,
            n_ctx=config.model["context"] or 16384,  
            chat_format="chatml",
            verbose=True,
        )

    def generate_text(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        story_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
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
            response = self.client.create_chat_completion(
                temperature=self.config.generation['temperature'] or 0.8,
                max_tokens=self.config.generation['max_tokens'] or 3000,
                messages=messages,
                repeat_penalty=self.config.generation['repeat_penalty'] or 1.1,
                top_p=self.config.generation['top_p'] or 0.85,
                presence_penalty=self.config.generation['presence_penalty']
                # stop=[ "###", "</s>"],
            )
            return response["choices"][0]["message"]["content"]
        
        except Exception as e:
            print(f"Error generating text: {e}")
            raise
    
    