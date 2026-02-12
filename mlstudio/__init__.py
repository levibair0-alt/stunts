"""
MLStudio - Chat Export Converter

A toolkit for converting chat export JSON files from various AI chat services
into clean, readable Markdown documents.

Supported formats:
- ChatGPT (conversations.json)

Usage:
    from mlstudio.chatgpt_parser import ChatGPTParser
    from mlstudio.convert_chat_export import ChatExportConverter
    
    # Convert a file
    converter = ChatExportConverter('conversations.json')
    converter.convert()
"""

__version__ = '1.0.0'
__author__ = 'MLStudio Team'

# Make key classes available at package level
from .chatgpt_parser import ChatGPTParser, ChatGPTConversation, ChatGPTMessage

__all__ = [
    'ChatGPTParser',
    'ChatGPTConversation', 
    'ChatGPTMessage',
]
