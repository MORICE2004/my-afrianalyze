import enum
from typing import Optional, Any, Union
from pydantic import BaseModel, Field

class LLMProvider(enum.Enum):
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OPENAI = "openai"
    LOCAL = "local"

class LLMConfig(BaseModel):
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    temperature: float = Field(default=0.1, description="Low temperature for financial analysis")
    max_tokens: int = 4096
    base_url: Optional[str] = None

class LLMClient:
    """
    The financial engine works independently of this LLM. The AI is replaceable.
    This abstraction ensures no vendor lock-in.
    """
    def __init__(self, config: LLMConfig):
        self.config = config

    def _estimate_cost(self, tokens: int) -> float:
        # Dummy cost calculation for observability demo
        # E.g. $0.001 per 1000 tokens
        return (tokens / 1000.0) * 0.001

    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = '', 
        response_model: Optional[type] = None
    ) -> Union[str, BaseModel]:
        from agents.telemetry import telemetry
        
        # Token estimation based on character length roughly
        estimated_tokens = (len(prompt) + len(system_prompt)) // 4
        estimated_cost = self._estimate_cost(estimated_tokens)
        
        telemetry.log_llm_cost(
            provider=self.config.provider.value,
            model_name=self.config.model_name,
            tokens=estimated_tokens,
            estimated_cost=estimated_cost
        )
        
        raise NotImplementedError(
            f"LLM Client not implemented for provider: {self.config.provider}. "
            "Please configure a valid provider implementation."
        )
