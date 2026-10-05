from abc import abstractmethod, ABC
from typing import Dict, List, Optional

from config import LLMConfig

class BaseClient(ABC):
    def __init__(self, config: LLMConfig):
        """Base client"""
        if not config:
            raise ValueError("No config")
        if not config.model["repo"]:
            raise ValueError("Model Repo is required")
        self.config = config


    @abstractmethod
    def generate_text(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None,
        story_context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        pass