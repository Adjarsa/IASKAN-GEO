"""
LLM Abstraction Layer for Railway Deployment
Uses emergentintegrations when available, falls back to native OpenAI SDK
"""
import os
import logging

logger = logging.getLogger(__name__)

# Try to import emergentintegrations, fall back to native SDK
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    USING_EMERGENT = True
    logger.info("Using emergentintegrations for LLM")
except ImportError:
    USING_EMERGENT = False
    logger.info("emergentintegrations not available, using native OpenAI SDK")
    
    # Native OpenAI implementation
    import openai
    
    class UserMessage:
        """Compatible UserMessage class"""
        def __init__(self, text: str):
            self.text = text
            self.role = "user"
            self.content = text
    
    class LlmChat:
        """Compatible LlmChat class using native OpenAI SDK"""
        def __init__(self, api_key: str, model: str = "gpt-4o"):
            self.api_key = api_key
            self.model = model
            self.client = openai.OpenAI(api_key=api_key)
            self.messages = []
        
        def send_message(self, message: UserMessage) -> str:
            """Send a message and get response"""
            self.messages.append({
                "role": "user",
                "content": message.text if hasattr(message, 'text') else str(message)
            })
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages
            )
            
            assistant_message = response.choices[0].message.content
            self.messages.append({
                "role": "assistant", 
                "content": assistant_message
            })
            
            return assistant_message
        
        def clear_history(self):
            """Clear conversation history"""
            self.messages = []


def get_llm_chat(api_key: str, model: str = "gpt-4o") -> LlmChat:
    """Factory function to get LLM chat instance"""
    return LlmChat(api_key=api_key, model=model)


def get_user_message(text: str) -> UserMessage:
    """Factory function to create user message"""
    return UserMessage(text=text)
