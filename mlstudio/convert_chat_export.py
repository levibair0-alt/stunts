#!/usr/bin/env python3
"""
Chat Export to Markdown Converter

This script converts chat export JSON files from various AI services (ChatGPT, Claude, etc.)
into readable Markdown documents.

Usage:
    python convert_chat_export.py <path_to_json_file>
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from chatgpt_parser import ChatGPTParser


def sanitize_filename(title: str) -> str:
    """
    Sanitize a conversation title for use as a filename.
    
    Args:
        title: The conversation title to sanitize
        
    Returns:
        A safe filename string
    """
    # Remove or replace unsafe characters
    unsafe_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in unsafe_chars:
        title = title.replace(char, '_')
    
    # Limit length
    if len(title) > 100:
        title = title[:97] + '...'
    
    return title.strip()


def detect_format(data: Dict) -> Optional[str]:
    """
    Detect the chat service format from the JSON data structure.
    
    Args:
        data: The loaded JSON data
        
    Returns:
        The format identifier ('chatgpt', 'claude', etc.) or None if unknown
    """
    # Check for ChatGPT format
    if isinstance(data, list) and len(data) > 0:
        first_item = data[0]
        if 'title' in first_item and 'mapping' in first_item:
            return 'chatgpt'
    
    return None


def parse_conversations(file_path: str, format_type: str) -> List[Dict]:
    """
    Parse conversations from the export file based on format type.
    
    Args:
        file_path: Path to the JSON export file
        format_type: The format identifier
        
    Returns:
        List of parsed conversation dictionaries
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if format_type == 'chatgpt':
        parser = ChatGPTParser()
        return parser.parse(data)
    else:
        raise ValueError(f"Unsupported format: {format_type}")


def format_timestamp(timestamp: Optional[float]) -> str:
    """
    Format a Unix timestamp into a readable date string.
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
        
    Returns:
        Formatted date string or empty string if timestamp is None
    """
    if timestamp is None:
        return ''
    
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def format_message_content(content_parts: List[Dict]) -> str:
    """
    Format message content parts into Markdown.
    
    Args:
        content_parts: List of content part dictionaries
        
    Returns:
        Formatted Markdown string
    """
    if not content_parts:
        return ''
    
    formatted_parts = []
    for part in content_parts:
        content_type = part.get('content_type', 'text')
        
        if content_type == 'text':
            text = part.get('text', '')
            formatted_parts.append(text)
        elif content_type == 'code':
            code = part.get('text', '')
            language = part.get('language', '')
            formatted_parts.append(f'\n```{language}\n{code}\n```\n')
        elif content_type == 'execution_output':
            output = part.get('text', '')
            formatted_parts.append(f'\n**Execution Output:**\n```\n{output}\n```\n')
    
    return ''.join(formatted_parts)


def messages_to_mapping(messages: List[Dict]) -> str:
    """
    Convert a flat list of messages into Markdown format.
    
    Args:
        messages: List of message dictionaries with role, content, timestamp
        
    Returns:
        Formatted Markdown string
    """
    markdown_lines = []
    
    for msg in messages:
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        timestamp = msg.get('timestamp')
        
        # Format timestamp
        ts_str = format_timestamp(timestamp)
        if ts_str:
            ts_line = f'*{ts_str}*\n'
        else:
            ts_line = ''
        
        # Role-based formatting
        if role == 'user':
            markdown_lines.append(f'\n### 👤 User\n\n{ts_str}')
        elif role == 'assistant':
            markdown_lines.append(f'\n### 🤖 Assistant\n\n{ts_str}')
        elif role == 'system':
            markdown_lines.append(f'\n### ⚙️ System\n\n{ts_str}')
        else:
            markdown_lines.append(f'\n### {role.title()}\n\n{ts_str}')
        
        # Content
        if content:
            markdown_lines.append(f'{content}\n')
    
    return '\n'.join(markdown_lines)


def generate_markdown(conversation: Dict) -> str:
    """
    Generate Markdown content for a conversation.
    
    Args:
        conversation: Parsed conversation dictionary
        
    Returns:
        Complete Markdown document as string
    """
    title = conversation.get('title', 'Untitled Conversation')
    created_at = conversation.get('created_at')
    updated_at = conversation.get('updated_at')
    messages = conversation.get('messages', [])
    
    # Header
    markdown_lines = [f'# {title}\n']
    
    # Metadata
    markdown_lines.append('---\n')
    if created_at:
        markdown_lines.append(f'**Created:** {format_timestamp(created_at)}\n')
    if updated_at:
        markdown_lines.append(f'**Last Updated:** {format_timestamp(updated_at)}\n')
    markdown_lines.append('---\n')
    
    # Messages
    markdown_lines.append(messages_to_mapping(messages))
    
    return '\n'.join(markdown_lines)


def save_markdown(content: str, output_dir: str, filename: str) -> str:
    """
    Save Markdown content to a file.
    
    Args:
        content: The Markdown content to save
        output_dir: Directory to save the file in
        filename: The filename (without extension)
        
    Returns:
        Full path to the saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f'{filename}.md')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def main():
    """Main entry point for the converter."""
    parser = argparse.ArgumentParser(
        description='Convert chat export JSON files to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python convert_chat_export.py conversations.json
  python convert_chat_export.py ~/Downloads/conversations.json
        '''
    )
    
    parser.add_argument(
        'json_file',
        help='Path to the chat export JSON file'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='outputs',
        help='Output directory for Markdown files (default: outputs/)'
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.isfile(args.json_file):
        print(f"Error: File not found: {args.json_file}", file=sys.stderr)
        sys.exit(1)
    
    # Load and detect format
    print(f"Loading: {args.json_file}")
    with open(args.json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    format_type = detect_format(data)
    if not format_type:
        print("Error: Could not detect chat service format.", file=sys.stderr)
        print("Supported formats: ChatGPT", file=sys.stderr)
        sys.exit(1)
    
    print(f"Detected format: {format_type}")
    
    # Parse conversations
    print("Parsing conversations...")
    conversations = parse_conversations(args.json_file, format_type)
    print(f"Found {len(conversations)} conversations")
    
    # Convert to Markdown
    output_dir = os.path.join(os.path.dirname(__file__), args.output_dir)
    converted_count = 0
    
    for conv in conversations:
        title = conv.get('title', 'untitled')
        filename = sanitize_filename(title)
        
        markdown_content = generate_markdown(conv)
        saved_path = save_markdown(markdown_content, output_dir, filename)
        
        converted_count += 1
        print(f"  [{converted_count}/{len(conversations)}] {title} -> {os.path.basename(saved_path)}")
    
    print(f"\n✅ Successfully converted {converted_count} conversations to Markdown")
    print(f"📁 Output directory: {output_dir}")


if __name__ == '__main__':
    main()
