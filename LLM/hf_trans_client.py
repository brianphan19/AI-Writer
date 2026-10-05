import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig 
from typing import List, Dict, Optional

from config import LLMConfig
from .base_client import BaseClient


class TransformerClient(BaseClient):
    """Hugging Face Inference API Client"""
    
    def __init__(self, config: LLMConfig):
        """Initialize HF client"""
        super().__init__(config=config)

        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model['model_repo'])

        # Add Mistral chat template
        self.tokenizer.chat_template = (
            "{% for message in messages %}"
            "{% if message['role'] == 'user' %}"
            "[INST] {{ message['content'] }} [/INST]"
            "{% elif message['role'] == 'assistant' %}"
            "{{ message['content'] }}</s>"
            "{% endif %}"
            "{% endfor %}"
        )


        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model['model_repo'],
            device_map="auto",
            low_cpu_mem_usage=True,
            torch_dtype=torch.float16
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
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            input_length = inputs['input_ids'].shape[1]

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.generation['max_tokens'],
                temperature=self.config.generation['temperature'],
                top_p=0.8,
                do_sample=True,
                repetition_penalty=1.1,
            )
            
            generated_tokens = outputs[0][input_length:]
            return self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
        
        except Exception as e:
            print(f"Error generating text: {e}")
            raise
    
    