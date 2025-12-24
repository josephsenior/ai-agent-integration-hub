"""Base agent for integration hub."""

from typing import Any, Dict, Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ..utils.openrouter_client import create_llm


class BaseAgent:
    """Base agent class for integration hub."""
    
    def __init__(
        self,
        system_prompt: str = "You are a helpful AI assistant.",
        model_name: str = "gpt-4",
        temperature: float = 0.7
    ):
        """Initialize base agent."""
        self.system_prompt = system_prompt
        self.llm = create_llm(model_name=model_name, temperature=temperature)
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{input}")
        ])
        
        self.chain = self.prompt_template | self.llm | StrOutputParser()
    
    async def process(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a message and return response."""
        try:
            # Add context to input if provided
            input_text = message
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                input_text = f"Context:\n{context_str}\n\nUser: {message}"
            
            response = await self.chain.ainvoke({"input": input_text})
            return response
        except Exception as e:
            return f"Error processing message: {str(e)}"


class IntegrationAgent(BaseAgent):
    """Agent specialized for integration hub interactions."""
    
    def __init__(self):
        system_prompt = """You are an AI assistant integrated into a multi-channel communication platform.
You can receive messages from Slack, Discord, Email, Webhooks, and other channels.
Your responses should be clear, helpful, and appropriate for the communication channel.
Be concise but thorough in your responses."""
        
        super().__init__(system_prompt=system_prompt)


