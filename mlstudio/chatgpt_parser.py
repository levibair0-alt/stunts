"""
ChatGPT Export Format Parser

This module handles parsing ChatGPT conversation export JSON files
into a standardized format for Markdown conversion.

ChatGPT export structure:
- conversations.json: Array of conversation objects
- Each conversation has:
  - title: string
  - create_time: float (Unix timestamp)
  - update_time: float (Unix timestamp)
  - mapping: dict of message nodes (tree structure)
- Message nodes:
  - id: string
  - message: dict with content, author, create_time
  - parent: optional string (parent message id)
- Content parts: Can be text, code, execution_output
"""

from typing import Dict, List, Optional, Any


class ChatGPTParser:
    """
    Parser for ChatGPT conversation export format.
    """
    
    def parse(self, data: List[Dict]) -> List[Dict]:
        """
        Parse ChatGPT conversations from export data.
        
        Args:
            data: List of conversation objects from conversations.json
            
        Returns:
            List of standardized conversation dictionaries
        """
        conversations = []
        
        for conv_data in data:
            conversation = self._parse_conversation(conv_data)
            if conversation and conversation.get('messages'):
                conversations.append(conversation)
        
        return conversations
    
    def _parse_conversation(self, conv_data: Dict) -> Optional[Dict]:
        """
        Parse a single conversation object.
        
        Args:
            conv_data: Conversation object from ChatGPT export
            
        Returns:
            Standardized conversation dictionary
        """
        # Extract basic metadata
        conversation = {
            'title': conv_data.get('title', 'Untitled Conversation'),
            'created_at': conv_data.get('create_time'),
            'updated_at': conv_data.get('update_time'),
            'messages': []
        }
        
        # Extract messages from the mapping structure
        mapping = conv_data.get('mapping', {})
        if not mapping:
            return conversation
        
        # Build message tree and flatten it
        messages = self._build_message_list(mapping)
        conversation['messages'] = messages
        
        return conversation
    
    def _build_message_list(self, mapping: Dict[str, Dict]) -> List[Dict]:
        """
        Build a chronological list of messages from the mapping structure.
        
        The mapping is a tree where each node can have children.
        We need to flatten it while preserving chronological order.
        
        Args:
            mapping: Dictionary of message nodes keyed by message ID
            
        Returns:
            Chronologically ordered list of messages
        """
        # Find root messages (those without parents or with null parents)
        root_ids = []
        for msg_id, node in mapping.items():
            parent_id = node.get('parent')
            if parent_id is None:
                root_ids.append(msg_id)
        
        # Build message trees from roots
        all_messages = []
        
        for root_id in root_ids:
            if root_id not in mapping:
                continue
            
            # Traverse tree and collect messages
            messages = self._traverse_message_tree(root_id, mapping)
            all_messages.extend(messages)
        
        # Sort by timestamp
        all_messages.sort(key=lambda m: m.get('timestamp', 0))
        
        return all_messages
    
    def _traverse_message_tree(self, node_id: str, mapping: Dict[str, Dict]) -> List[Dict]:
        """
        Recursively traverse message tree and collect messages.
        
        Args:
            node_id: Current message node ID
            mapping: Full mapping dictionary
            
        Returns:
            List of messages from this subtree
        """
        node = mapping.get(node_id)
        if not node:
            return []
        
        messages = []
        
        # Parse current message
        message = self._parse_message_node(node)
        if message:
            messages.append(message)
        
        # Find children (messages that have this message as parent)
        children_ids = [
            child_id for child_id, child_node in mapping.items()
            if child_node.get('parent') == node_id
        ]
        
        # Recursively process children
        for child_id in children_ids:
            child_messages = self._traverse_message_tree(child_id, mapping)
            messages.extend(child_messages)
        
        return messages
    
    def _parse_message_node(self, node: Dict) -> Optional[Dict]:
        """
        Parse a single message node.
        
        Args:
            node: Message node from mapping
            
        Returns:
            Standardized message dictionary
        """
        message_data = node.get('message')
        if not message_data:
            return None
        
        # Extract content
        content = self._extract_content(message_data)
        if not content:
            return None
        
        # Extract author role
        author = message_data.get('author', {})
        role = self._normalize_role(author.get('role', 'unknown'))
        
        # Extract timestamp
        create_time = message_data.get('create_time')
        
        return {
            'role': role,
            'content': content,
            'timestamp': create_time,
            'message_id': message_data.get('id')
        }
    
    def _extract_content(self, message_data: Dict) -> str:
        """
        Extract and format content from message data.
        
        Args:
            message_data: Message dictionary
            
        Returns:
            Formatted content string
        """
        content = message_data.get('content', {})
        
        # Handle content parts structure
        if isinstance(content, dict):
            parts = content.get('parts', [])
        elif isinstance(content, list):
            parts = content
        else:
            parts = []
        
        formatted_parts = []
        
        for part in parts:
            if not isinstance(part, dict):
                # Simple text string
                formatted_parts.append(str(part))
                continue
            
            content_type = part.get('content_type', 'text')
            
            if content_type == 'text':
                text = part.get('text', '')
                formatted_parts.append(text)
            
            elif content_type == 'code':
                code = part.get('text', '')
                language = part.get('language', '')
                # We'll format code blocks in Markdown generation
                formatted_parts.append(f'\n```{language}\n{code}\n```\n')
            
            elif content_type == 'execution_output':
                output = part.get('text', '')
                formatted_parts.append(f'\n**Execution Output:**\n```\n{output}\n```\n')
            
            elif content_type == 'tether_browsing_display':
                # Handle browsing results
                result = part.get('result', '')
                formatted_parts.append(f'\n**Browsing Result:**\n{result}\n')
            
            elif content_type == 'image':
                # Handle images (reference only)
                metadata = part.get('metadata', {})
                formatted_parts.append('[Image attached]\n')
        
        return ''.join(formatted_parts).strip()
    
    def _normalize_role(self, role: str) -> str:
        """
        Normalize role names to standard format.
        
        Args:
            role: Raw role string from export
            
        Returns:
            Normalized role string
        """
        role_lower = role.lower()
        
        if role_lower in ['user', 'assistant', 'system']:
            return role_lower
        
        # Map ChatGPT-specific roles
        role_mapping = {
            'chatgpt': 'assistant',
            'gpt': 'assistant',
            'plugin': 'assistant',
            'browser': 'assistant',
        }
        
        return role_mapping.get(role_lower, role)
    
    @staticmethod
    def get_format_description() -> str:
        """
        Get a description of the ChatGPT export format.
        
        Returns:
            Format description string
        """
        return """
ChatGPT Export Format
====================

Export Location: Settings > Data Controls > Export

Structure:
- conversations.json: Array of conversation objects
- Each conversation:
  * title: Conversation title
  * create_time: Unix timestamp
  * update_time: Unix timestamp
  * mapping: Message tree structure

Message Structure:
- Keyed by message ID
- Each message:
  * message.content.parts: Array of content parts
  * message.author.role: 'user', 'assistant', 'system', etc.
  * message.create_time: Unix timestamp
  * parent: ID of parent message (null for roots)

Content Types:
- text: Plain text content
- code: Code blocks with language
- execution_output: Code execution results
- tether_browsing_display: Web browsing results
- image: Image attachments
        """
