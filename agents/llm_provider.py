import enum
import os
import json
from typing import Optional, Any, Union
from pydantic import BaseModel, Field
import litellm
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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
        from packages.core.config import settings
        from packages.core.exceptions import ProductionDataViolation
        if settings.APP_ENV == "PRODUCTION":
            raise ProductionDataViolation("Mock reached in production")
        # E.g. $0.001 per 1000 tokens
        return (tokens / 1000.0) * 0.001

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((litellm.RateLimitError, litellm.Timeout, litellm.APIConnectionError))
    )
    async def _execute_call(self, messages, response_model):
        kwargs = {
            "model": self.config.model_name,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
        
        if self.config.api_key:
            kwargs["api_key"] = self.config.api_key
        if self.config.base_url:
            kwargs["api_base"] = self.config.base_url
            
        if response_model:
            # LiteLLM structured outputs
            kwargs["response_format"] = response_model
            
        response = await litellm.acompletion(**kwargs)
        
        if response_model:
            content = response.choices[0].message.content
            if isinstance(content, str):
                return response_model.model_validate_json(content)
            return content
        else:
            return response.choices[0].message.content

    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = '', 
        response_model: Optional[type] = None
    ) -> Union[str, BaseModel]:
        from agents.telemetry import telemetry
        from packages.cache.manager import cache_manager
        
        app_env = os.environ.get("APP_ENV", "TEST")
        
        if app_env == "PRODUCTION":
            from packages.security.pii_scrubber import PIIScrubber
            prompt = PIIScrubber.scrub_text(prompt)
            if system_prompt:
                system_prompt = PIIScrubber.scrub_text(system_prompt)
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Cache check
        cache_key = f"llm_prompt:{system_prompt}:{prompt}:{self.config.model_name}"
        cached_response = cache_manager.get(cache_key, hash_key=True)
        if cached_response:
            if response_model:
                try:
                    return response_model.model_validate_json(cached_response)
                except Exception:
                    pass
            else:
                return cached_response

        if app_env == "TEST":
            # Bypass network, return mock data
            # Token estimation based on character length roughly
            estimated_tokens = (len(prompt) + len(system_prompt)) // 4
            estimated_cost = self._estimate_cost(estimated_tokens)
            
            # Use telemetry with prompt info for observability
            telemetry.log_llm_cost(
                provider=self.config.provider.value,
                model_name=self.config.model_name,
                tokens=estimated_tokens,
                estimated_cost=estimated_cost,
                prompt=prompt
            )
            
            if response_model:
                # Return an empty instance of the model if mock data
                # For simplicity, if possible create mock instance
                try:
                    return response_model()
                except:
                    return None
            return "MOCK_RESPONSE: " + prompt[:20]
        
        # Execute real network call for DEVELOPMENT or PRODUCTION
        result = await self._execute_call(messages, response_model)
        
        # Cache the result
        result_str = result.model_dump_json() if isinstance(result, BaseModel) else result
        cache_manager.set(cache_key, result_str, ttl=86400, hash_key=True)
        
        # We can extract actual token usage from litellm if needed, but for simplicity:
        estimated_tokens = (len(prompt) + len(system_prompt)) // 4
        estimated_cost = self._estimate_cost(estimated_tokens)
        
        telemetry.log_llm_cost(
            provider=self.config.provider.value,
            model_name=self.config.model_name,
            tokens=estimated_tokens,
            estimated_cost=estimated_cost,
            prompt=prompt
        )
        
        return result
