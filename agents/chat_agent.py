from typing import Optional

class LLMClient:
    """
    Mock LLM client to handle communications with external LLM APIs.
    """
    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        # In a real environment, this invokes the LLM API
        return "Simulated LLM response bound by the system prompt."

class PortfolioChatAgent:
    """
    AI Chat Engine for Portfolio interactions, strictly utilizing injected context.
    """
    SYSTEM_PROMPT = (
        "You are an Advanced AI Financial Assistant for My AfriAnalyze. "
        "CRITICAL RULES: "
        "1. You must STRICTLY use the provided portfolio context to answer the user's queries. "
        "2. You are FORBIDDEN from hallucinating financial data, generating unsupported calculations, or providing financial advice. "
        "3. Every claim you make about the user's portfolio must be backed by the injected Context Evidence Records. "
        "4. If an answer cannot be determined from the provided context, explicitly state that you do not have the required information."
    )

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()

    def chat(self, query: str, portfolio_context: str) -> str:
        """
        Executes a chat request given the user query and the injected portfolio context.
        """
        user_prompt = (
            f"=== PORTFOLIO CONTEXT ===\n"
            f"{portfolio_context}\n"
            f"=========================\n\n"
            f"User Query: {query}"
        )
        
        return self.llm_client.generate_response(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt
        )
