from .base_client import BaseClient
from .hf_inf_client import InfClient
from .hf_local_client import LocalClient
from .hf_trans_client import TransformerClient
from .llm7_client import LLM7Client
from .glm_client import GLMClient
from .openrouter_client import OpenRouterClient
from config import LLMConfig


def llm_factory(cfg: LLMConfig) -> BaseClient:
    match  cfg.provider:
        case "inference":
            client = InfClient(cfg)
        case"llama_cpp":
            client = LocalClient(cfg)
        case"transformer":
            client = TransformerClient(cfg)
        case"llm7":
            client = LLM7Client(cfg)
        case"glm":
            client = GLMClient(cfg)
        case "openrouter":
            client = OpenRouterClient(cfg)
        case _ :
            raise ValueError(f"Unknown provider: { cfg.provider}")

    return client
