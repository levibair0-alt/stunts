"""
ChatGPT Export Parser

This module handles parsing of ChatGPT export JSON files into a structured format.
ChatGPT exports come as a conversations.json file containing an array of conversation objects.

Export structure:
- Each conversation has: title, create_time, update_time, mapping (message tree)
- Messages are stored in a mapping dict with message IDs as keys
- Each message has: id, message (content, author), create_time, parent, children
- Content parts can be text or code
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any


class ChatGPTMessage:
    """Represents a single message in a ChatGPT conversation."""
    
    def __init__(self, message_id: str, role: str, content: str, timestamp: float):
        self.id = message_id
        self.role = role  # 'user', 'assistant', 'system', or 'tool'
        self.content = content
        self.timestamp = timestamp
    
    def get_formatted_timestamp(self) -> str:
        """Convert Unix timestamp to readable format."""
        if self.timestamp:
            return datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        return 'Unknown time'
    
    def __repr__(self):
        return f"ChatGPTMessage(role={self.role}, timestamp={self.get_formatted_timestamp()})"


class ChatGPTConversation:
    """Represents a complete ChatGPT conversation with all messages."""
    
    def __init__(self, title: str, create_time: float, update_time: float):
        self.title = title
        self.create_time = create_time
        self.update_time = update_time
        self.messages: List[ChatGPTMessage] = []
    
    def add_message(self, message: ChatGPTMessage):
        """Add a message to the conversation."""
        self.messages.append(message)
    
    def get_formatted_create_time(self) -> str:
        """Get formatted creation time."""
        return datetime.fromtimestamp(self.create_time).strftime('%Y-%m-%d %H:%M:%S')
    
    def get_formatted_update_time(self) -> str:
        """Get formatted update time."""
        return datetime.fromtimestamp(self.update_time).strftime('%Y-%m-%d %H:%M:%S')
    
    def __repr__(self):
        return f"ChatGPTConversation(title='{self.title}', messages={len(self.messages)})"


class ChatGPTParser:
    """Parser for ChatGPT export JSON files."""
    
    def __init__(self, json_data: Dict[str, Any]):
        """
        Initialize parser with JSON data.
        
        Args:
            json_data: Parsed JSON data from ChatGPT export
        """
        self.json_data = json_data
    
    @staticmethod
    def load_from_file(file_path: str) -> 'ChatGPTParser':
        """
        Load ChatGPT export from file.
        
        Args:
            file_path: Path to the conversations.json file
            
        Returns:
            ChatGPTParser instance
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ChatGPTParser(data)
    
    def parse_conversations(self) -> List[ChatGPTConversation]:
        """
        Parse all conversations from the export.
        
        Returns:
            List of ChatGPTConversation objects
        """
        conversations = []
        
        # ChatGPT export is an array of conversation objects
        if isinstance(self.json_data, list):
            for conv_data in self.json_data:
                conversation = self._parse_single_conversation(conv_data)
                if conversation:
                    conversations.append(conversation)
        else:
            # Single conversation object
            conversation = self._parse_single_conversation(self.json_data)
            if conversation:
                conversations.append(conversation)
        
        return conversations
    
    def _parse_single_conversation(self, conv_data: Dict[str, Any]) -> Optional[ChatGPTConversation]:
        """
        Parse a single conversation object.
        
        Args:
            conv_data: Conversation data dictionary
            
        Returns:
            ChatGPTConversation object or None if parsing fails
        """
        try:
            title = conv_data.get('title', 'Untitled Conversation')
            create_time = conv_data.get('create_time', 0)
            update_time = conv_data.get('update_time', 0)
            
            conversation = ChatGPTConversation(title, create_time, update_time)
            
            # Parse the mapping (message tree)
            mapping = conv_data.get('mapping', {})
            if not mapping:
                return conversation
            
            # Build message tree and extract linear conversation
            messages = self._extract_messages_from_mapping(mapping)
            
            for message in messages:
                conversation.add_message(message)
            
            return conversation
            
        except Exception as e:
            print(f"Error parsing conversation: {e}")
            return None
    
    def _extract_messages_from_mapping(self, mapping: Dict[str, Any]) -> List[ChatGPTMessage]:
        """
        Extract messages from the mapping tree structure.
        
        ChatGPT stores messages in a tree structure where each message has:
        - id: unique identifier
        - parent: parent message id
        - children: list of child message ids
        - message: the actual message content
        
        Args:
            mapping: Message mapping dictionary
            
        Returns:
            List of ChatGPTMessage objects in chronological order
        """
        messages = []
        
        # Find the root message (has no parent or parent is None)
        root_id = None
        for msg_id, msg_data in mapping.items():
            if msg_data.get('parent') is None or msg_data.get('parent') == '':
                root_id = msg_id
                break
        
        if not root_id:
            # If no clear root, just process all messages
            for msg_id, msg_data in mapping.items():
                message = self._parse_message_node(msg_id, msg_data)
                if message:
                    messages.append(message)
            # Sort by timestamp
            messages.sort(key=lambda m: m.timestamp)
            return messages
        
        # Traverse the tree from root
        visited = set()
        self._traverse_message_tree(root_id, mapping, messages, visited)
        
        return messages
    
    def _traverse_message_tree(self, msg_id: str, mapping: Dict[str, Any], 
                               messages: List[ChatGPTMessage], visited: set):
        """
        Recursively traverse the message tree.
        
        Args:
            msg_id: Current message ID
            mapping: Complete message mapping
            messages: List to append messages to
            visited: Set of visited message IDs
        """
        if msg_id in visited or msg_id not in mapping:
            return
        
        visited.add(msg_id)
        msg_data = mapping[msg_id]
        
        # Parse this message
        message = self._parse_message_node(msg_id, msg_data)
        if message:
            messages.append(message)
        
        # Process children in order (take the first child in the path)
        children = msg_data.get('children', [])
        if children:
            # Follow the first child (main conversation path)
            self._traverse_message_tree(children[0], mapping, messages, visited)
    
    def _parse_message_node(self, msg_id: str, msg_data: Dict[str, Any]) -> Optional[ChatGPTMessage]:
        """
        Parse a single message node.
        
        Args:
            msg_id: Message ID
            msg_data: Message data dictionary
            
        Returns:
            ChatGPTMessage object or None if not a valid message
        """
        message_obj = msg_data.get('message')
        if not message_obj:
            return None
        
        # Extract role
        author = message_obj.get('author', {})
        role = author.get('role', 'unknown')
        
        # Extract content
        content_obj = message_obj.get('content', {})
        content_type = content_obj.get('content_type', 'text')
        
        content = ''
        if content_type == 'text':
            parts = content_obj.get('parts', [])
            if parts:
                # Join all text parts
                content = '\n'.join(str(part) for part in parts if part)
        elif content_type == 'code':
            # Handle code content
            parts = content_obj.get('parts', [])
            if parts:
                content = '\n'.join(str(part) for part in parts if part)
        
        # Skip empty messages
        if not content or content.strip() == '':
            return None
        
        # Extract timestamp
        timestamp = message_obj.get('create_time', 0)
        
        return ChatGPTMessage(msg_id, role, content, timestamp)
    
    @staticmethod
    def is_chatgpt_format(json_data: Any) -> bool:
        """
        Check if the JSON data matches ChatGPT export format.
        
        Args:
            json_data: Parsed JSON data
            
        Returns:
            True if format matches ChatGPT export
        """
        # Check if it's a list of conversations or single conversation
        if isinstance(json_data, list):
            if len(json_data) == 0:
                return False
            sample = json_data[0]
        else:
            sample = json_data
        
        # Check for ChatGPT-specific structure
        if not isinstance(sample, dict):
            return False
        
        # ChatGPT exports have 'mapping' and 'create_time' fields
        has_mapping = 'mapping' in sample
        has_create_time = 'create_time' in sample
        has_title = 'title' in sample
        
        return has_mapping and (has_create_time or has_title)
