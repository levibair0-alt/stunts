# MLStudio - Chat Export Converter

A Python tool for converting chat export JSON files from various AI chat services into clean, readable Markdown documents.

## 🎯 Features

- **Multi-format Support**: Currently supports ChatGPT, extensible for Claude and other services
- **Clean Markdown Output**: Well-formatted conversations with proper headers, timestamps, and code blocks
- **Smart Content Detection**: Automatically detects and preserves code blocks and formatting
- **Sanitized Filenames**: Converts conversation titles into valid filenames
- **Organized Output**: All Markdown files saved to dedicated `outputs/` directory
- **Conversation Metadata**: Preserves creation/update times and message counts

## 📦 Installation

No external dependencies required! This tool uses only Python standard library.

```bash
cd mlstudio
python convert_chat_export.py <path_to_json_file>
```

**Requirements:**
- Python 3.7 or higher

## 🚀 Quick Start

### 1. Export Your Chats from ChatGPT

To export your ChatGPT conversations:

1. Go to [ChatGPT Settings](https://chat.openai.com/)
2. Click on your profile (bottom-left corner)
3. Navigate to **Settings** → **Data controls**
4. Click **Export data**
5. Confirm the export
6. Wait for the email notification (usually within a few minutes to 24 hours)
7. Download the export archive
8. Extract the `conversations.json` file

### 2. Convert to Markdown

```bash
python convert_chat_export.py conversations.json
```

The script will:
- Detect the format automatically (ChatGPT)
- Parse all conversations
- Generate individual Markdown files in `outputs/`

### 3. View Your Markdown Files

Check the `outputs/` directory for your converted conversations:

```bash
ls outputs/
# Example output:
# 001_Python_Best_Practices.md
# 002_Machine_Learning_Tutorial.md
# 003_API_Design_Discussion.md
```

## 📖 Usage

### Basic Usage

```bash
python convert_chat_export.py <json_file>
```

### Custom Output Directory

```bash
python convert_chat_export.py conversations.json -o my_conversations
```

### Get Help

```bash
python convert_chat_export.py --help
```

## 📄 Output Format

Generated Markdown files include:

### Header Section
- **Conversation title** as H1 heading
- **Metadata section** with:
  - Creation timestamp
  - Last update timestamp
  - Total message count

### Messages
Each message includes:
- **Role indicator** (👤 User, 🤖 Assistant, ⚙️ System, 🔧 Tool)
- **Timestamp** in readable format
- **Content** with preserved formatting
- Code blocks automatically detected and formatted

### Example Output

```markdown
# How to Use Python Virtual Environments

## Conversation Metadata

- **Created:** 2024-01-15 10:30:45
- **Updated:** 2024-01-15 11:22:18
- **Messages:** 12

---

## Conversation

### 👤 User

*2024-01-15 10:30:45*

How do I create a Python virtual environment?

---

### 🤖 Assistant

*2024-01-15 10:30:52*

To create a Python virtual environment, you can use the following command:

```bash
python -m venv myenv
```

This creates a new virtual environment in a directory called `myenv`.

---
```

## 🏗️ Architecture

### Project Structure

```
mlstudio/
├── convert_chat_export.py    # Main conversion script
├── chatgpt_parser.py          # ChatGPT format parser
├── outputs/                   # Generated Markdown files
├── README.md                  # This file
└── examples/                  # Example JSON structures
    └── chatgpt_example.json   # Sample ChatGPT export structure
```

### Core Components

1. **`convert_chat_export.py`** - Main script
   - Format detection
   - CLI argument parsing
   - Conversion orchestration
   - File I/O management

2. **`chatgpt_parser.py`** - ChatGPT parser module
   - JSON parsing
   - Message tree traversal
   - Conversation extraction
   - Timestamp handling

3. **`MarkdownGenerator`** - Markdown generation
   - Content formatting
   - Code block detection
   - Filename sanitization
   - File writing

## 🔧 Extending for Other Services

The tool is designed to be extensible. To add support for a new chat service:

### 1. Create a New Parser Module

```python
# claude_parser.py
class ClaudeParser:
    @staticmethod
    def is_claude_format(json_data):
        # Detection logic
        pass
    
    def parse_conversations(self):
        # Parsing logic
        pass
```

### 2. Update Format Detection

In `convert_chat_export.py`, add to the `detect_format()` method:

```python
def detect_format(self) -> Optional[str]:
    if ChatGPTParser.is_chatgpt_format(self.json_data):
        return 'chatgpt'
    
    if ClaudeParser.is_claude_format(self.json_data):
        return 'claude'
    
    return None
```

### 3. Add Conversion Handler

Add a new method like `_convert_claude()` following the pattern of `_convert_chatgpt()`.

## 📋 ChatGPT Export Format Reference

ChatGPT exports use the following JSON structure:

```json
[
  {
    "title": "Conversation Title",
    "create_time": 1674123456.789,
    "update_time": 1674125678.901,
    "mapping": {
      "message-id-1": {
        "id": "message-id-1",
        "parent": null,
        "children": ["message-id-2"],
        "message": {
          "id": "message-id-1",
          "author": {
            "role": "user"
          },
          "create_time": 1674123456.789,
          "content": {
            "content_type": "text",
            "parts": ["Hello, how are you?"]
          }
        }
      },
      "message-id-2": {
        "id": "message-id-2",
        "parent": "message-id-1",
        "children": [],
        "message": {
          "id": "message-id-2",
          "author": {
            "role": "assistant"
          },
          "create_time": 1674123460.123,
          "content": {
            "content_type": "text",
            "parts": ["I'm doing well, thank you!"]
          }
        }
      }
    }
  }
]
```

### Key Fields

- **`title`**: Conversation title string
- **`create_time`**: Unix timestamp (float)
- **`update_time`**: Unix timestamp (float)
- **`mapping`**: Dictionary of message nodes
  - **`id`**: Unique message identifier
  - **`parent`**: Parent message ID (null for root)
  - **`children`**: Array of child message IDs
  - **`message.author.role`**: 'user', 'assistant', 'system', or 'tool'
  - **`message.content.parts`**: Array of content strings
  - **`message.create_time`**: Message timestamp

## 🐛 Troubleshooting

### "Unknown chat export format"
- Verify you're using a supported format (currently ChatGPT)
- Check that the JSON file is valid and properly formatted
- Ensure the file contains the expected structure (has 'mapping' field for ChatGPT)

### "No conversations found"
- The JSON file may be empty or malformed
- Check if the export contains any actual conversations

### Permission errors
- Ensure you have write permissions in the `outputs/` directory
- Try running with appropriate permissions

### Import errors
- Make sure you're running the script from the `mlstudio/` directory
- Or ensure `chatgpt_parser.py` is in the same directory as `convert_chat_export.py`

## 🤝 Contributing

To extend this tool:

1. Add new parser modules for different chat services
2. Enhance Markdown formatting options
3. Add filtering capabilities (date ranges, specific conversations)
4. Implement batch processing for multiple files
5. Add export to other formats (HTML, PDF, etc.)

## 📝 License

This tool is part of the stunts repository. See the repository's main LICENSE file for details.

## 🙏 Acknowledgments

Created as part of the MLStudio toolkit for AI chat management and analysis.

---

**Happy Converting! 🚀**
