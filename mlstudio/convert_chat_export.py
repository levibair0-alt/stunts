#!/usr/bin/env python3
"""
Chat Export to Markdown Converter

This script converts chat export JSON files from various services (ChatGPT, Claude, etc.)
into clean, readable Markdown documents.

Usage:
    python convert_chat_export.py <path_to_json_file>
    
Example:
    python convert_chat_export.py conversations.json
    
The script will:
1. Detect the chat service format
2. Parse the conversations and messages
3. Generate Markdown files in the outputs/ directory
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

from chatgpt_parser import ChatGPTParser, ChatGPTConversation, ChatGPTMessage


class MarkdownGenerator:
    """Generates Markdown documents from parsed conversations."""
    
    def __init__(self, output_dir: str = 'outputs'):
        """
        Initialize the Markdown generator.
        
        Args:
            output_dir: Directory to save generated Markdown files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """
        Sanitize a conversation title to create a valid filename.
        
        Args:
            title: Original conversation title
            max_length: Maximum filename length
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '-', title)
        sanitized = re.sub(r'\s+', '_', sanitized)
        sanitized = re.sub(r'_+', '_', sanitized)
        sanitized = sanitized.strip('_-.')
        
        # Truncate if too long
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rstrip('_-.')
        
        # Ensure we have a valid filename
        if not sanitized:
            sanitized = 'conversation'
        
        return sanitized
    
    def generate_chatgpt_markdown(self, conversation: ChatGPTConversation, 
                                  conversation_number: int = 1) -> str:
        """
        Generate Markdown content for a ChatGPT conversation.
        
        Args:
            conversation: ChatGPTConversation object
            conversation_number: Number of this conversation (for unique filenames)
            
        Returns:
            Path to the generated Markdown file
        """
        lines = []
        
        # Header with title
        lines.append(f"# {conversation.title}")
        lines.append("")
        
        # Metadata
        lines.append("## Conversation Metadata")
        lines.append("")
        lines.append(f"- **Created:** {conversation.get_formatted_create_time()}")
        lines.append(f"- **Updated:** {conversation.get_formatted_update_time()}")
        lines.append(f"- **Messages:** {len(conversation.messages)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Messages
        lines.append("## Conversation")
        lines.append("")
        
        for message in conversation.messages:
            lines.extend(self._format_message(message))
        
        # Generate filename
        base_filename = self.sanitize_filename(conversation.title)
        filename = f"{conversation_number:03d}_{base_filename}.md"
        filepath = self.output_dir / filename
        
        # Handle duplicate filenames
        counter = 1
        while filepath.exists():
            filename = f"{conversation_number:03d}_{base_filename}_{counter}.md"
            filepath = self.output_dir / filename
            counter += 1
        
        # Write to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return str(filepath)
    
    def _format_message(self, message: ChatGPTMessage) -> List[str]:
        """
        Format a single message as Markdown.
        
        Args:
            message: ChatGPTMessage object
            
        Returns:
            List of Markdown lines
        """
        lines = []
        
        # Role header with timestamp
        role_display = {
            'user': '👤 User',
            'assistant': '🤖 Assistant',
            'system': '⚙️ System',
            'tool': '🔧 Tool'
        }.get(message.role, f'❓ {message.role.capitalize()}')
        
        lines.append(f"### {role_display}")
        lines.append("")
        lines.append(f"*{message.get_formatted_timestamp()}*")
        lines.append("")
        
        # Content
        content = self._format_content(message.content)
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")
        
        return lines
    
    def _format_content(self, content: str) -> str:
        """
        Format message content, preserving code blocks and formatting.
        
        Args:
            content: Raw message content
            
        Returns:
            Formatted content
        """
        # If content already has markdown code blocks, preserve them
        if '```' in content:
            return content
        
        # Check if entire content looks like code (simple heuristic)
        lines = content.split('\n')
        if len(lines) > 1:
            # If most lines are indented or contain code-like patterns
            code_indicators = sum(1 for line in lines if 
                                 line.startswith((' ', '\t')) or 
                                 re.search(r'[{}\[\];()=]', line))
            if code_indicators > len(lines) * 0.5:
                # Wrap in generic code block
                return f"```\n{content}\n```"
        
        return content


class ChatExportConverter:
    """Main converter class that handles format detection and conversion."""
    
    def __init__(self, json_path: str, output_dir: str = 'outputs'):
        """
        Initialize the converter.
        
        Args:
            json_path: Path to the JSON export file
            output_dir: Directory to save Markdown files
        """
        self.json_path = Path(json_path)
        self.output_dir = output_dir
        self.json_data = None
        self.markdown_generator = MarkdownGenerator(output_dir)
    
    def load_json(self) -> bool:
        """
        Load and parse the JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.json_data = json.load(f)
            return True
        except FileNotFoundError:
            print(f"Error: File not found: {self.json_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON file: {e}")
            return False
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def detect_format(self) -> Optional[str]:
        """
        Detect the chat service format from the JSON structure.
        
        Returns:
            Format name ('chatgpt', 'claude', etc.) or None if unknown
        """
        if not self.json_data:
            return None
        
        # Check for ChatGPT format
        if ChatGPTParser.is_chatgpt_format(self.json_data):
            return 'chatgpt'
        
        # Add more format detectors here as we support more services
        # if ClaudeParser.is_claude_format(self.json_data):
        #     return 'claude'
        
        return None
    
    def convert(self) -> bool:
        """
        Convert the chat export to Markdown.
        
        Returns:
            True if successful, False otherwise
        """
        # Load JSON
        print(f"Loading JSON file: {self.json_path}")
        if not self.load_json():
            return False
        
        # Detect format
        print("Detecting chat service format...")
        format_name = self.detect_format()
        
        if not format_name:
            print("Error: Unknown chat export format")
            print("Currently supported formats: ChatGPT")
            return False
        
        print(f"Detected format: {format_name.upper()}")
        
        # Parse conversations based on format
        if format_name == 'chatgpt':
            return self._convert_chatgpt()
        
        # Add more format handlers here
        # elif format_name == 'claude':
        #     return self._convert_claude()
        
        return False
    
    def _convert_chatgpt(self) -> bool:
        """
        Convert ChatGPT export to Markdown.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            parser = ChatGPTParser(self.json_data)
            conversations = parser.parse_conversations()
            
            if not conversations:
                print("Warning: No conversations found in export")
                return False
            
            print(f"Found {len(conversations)} conversation(s)")
            print(f"Generating Markdown files in: {self.output_dir}")
            
            generated_files = []
            for idx, conversation in enumerate(conversations, 1):
                print(f"  [{idx}/{len(conversations)}] Converting: {conversation.title}")
                filepath = self.markdown_generator.generate_chatgpt_markdown(
                    conversation, 
                    conversation_number=idx
                )
                generated_files.append(filepath)
            
            print(f"\n✓ Successfully generated {len(generated_files)} Markdown file(s)")
            print(f"\nGenerated files:")
            for filepath in generated_files:
                print(f"  - {filepath}")
            
            return True
            
        except Exception as e:
            print(f"Error during conversion: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Convert chat export JSON files to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_chat_export.py conversations.json
  python convert_chat_export.py chatgpt_export.json
  
Supported formats:
  - ChatGPT (conversations.json from Settings > Data Controls > Export)
  
Output:
  Markdown files will be saved to the outputs/ directory with sanitized filenames.
        """
    )
    
    parser.add_argument(
        'json_file',
        help='Path to the chat export JSON file'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='outputs',
        help='Output directory for Markdown files (default: outputs)'
    )
    
    args = parser.parse_args()
    
    # Convert paths to be relative to script location
    script_dir = Path(__file__).parent
    json_path = Path(args.json_file)
    if not json_path.is_absolute():
        json_path = script_dir / json_path
    
    output_dir = Path(args.output)
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir
    
    # Create converter and run
    converter = ChatExportConverter(str(json_path), str(output_dir))
    success = converter.convert()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
