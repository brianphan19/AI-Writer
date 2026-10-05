from dataclasses import dataclass
from dotenv import load_dotenv
import os, yaml

load_dotenv()
SETTING_PATH="settings.yaml"

@dataclass(frozen=True)
class NotionConfig:
    notion_token: str
    chapters_page_id: str

    @classmethod
    def load(cls) -> 'NotionConfig':
        return cls(
            notion_token = os.getenv("NOTION_TOKEN"),
            chapters_page_id=os.getenv("PAGE_ID"),
        )

@dataclass(frozen=True)
class LLMConfig:
    key: str

    provider: str
    model: dict
    runtime: dict
    generation: dict

    @classmethod
    def load(cls, path) -> 'LLMConfig':

        with open(path) as f:
            raw = yaml.safe_load(f)

        llm = raw["llm"]

        # Resolve active model if catalog exists
        if "catalog" in llm:
            llm = llm["catalog"][llm["active"]]

        provider=llm["provider"]
        match provider:
            case 'llm7':
                api_key = os.getenv("LLM7_API_KEY")
            case  'glm':
                api_key = os.getenv("GLM_API_KEY")
            case 'inf':
                api_key = os.getenv("HF_TOKEN")
            case 'openrouter':
                api_key = os.getenv("VENICE_KEY")
            case _ :
                api_key = None

        return cls(
            key = api_key,
            provider=llm["provider"],
            model=llm.get("model", {}),
            runtime=llm.get("runtime", {}),
            generation=raw["llm"].get("generation", {}),
        )

    @staticmethod
    def _safe_float(value: str) -> float:
        """Safely convert string to float"""
        try:
            return max(0.0, min(2.0, float(value)))
        except (ValueError, TypeError):
            return 0.3

@dataclass(frozen=True)
class Config:
    notion: NotionConfig
    llm: LLMConfig

    @classmethod
    def from_env(cls) -> 'Config':
        
        return cls(
            notion=NotionConfig.load(),
            llm=LLMConfig.load(path=SETTING_PATH)
        )
