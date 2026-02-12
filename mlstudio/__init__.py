"""
ML Studio - Chat Export Converter

A Python tool for converting AI chat export JSON files into readable Markdown documents.
"""

__version__ = "1.0.0"
__author__ = "Stunts Project"

from .convert_chat_export import main
from .chatgpt_parser import ChatGPTParser

__all__ = ['main', 'ChatGPTParser']
