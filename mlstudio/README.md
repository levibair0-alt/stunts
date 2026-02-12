# ML Studio - Chat Export Converter

A Python tool for converting AI chat export JSON files into readable Markdown documents. Currently supports ChatGPT exports with extensible architecture for adding other chat services.

## Features

- 🔄 **Multiple Format Support**: ChatGPT (with extensible architecture for Claude, etc.)
- 📝 **Clean Markdown Output**: Well-formatted, readable documents
- 🕐 **Timestamp Preservation**: All conversation dates preserved
- 💻 **Code Block Formatting**: Proper syntax highlighting for code
- 👤 **Role-based Formatting**: Clear separation between user, assistant, and system messages
- 📁 **Batch Processing**: Convert entire conversation archives at once

## Quick Start

### 1. Export Your ChatGPT Conversations

1. Go to [chat.openai.com](https://chat.openai.com)
2. Click on your profile/name in the bottom left corner
3. Go to **Settings**
4. Navigate to **Data Controls** (or "Data export")
5. Click **Export** to download your conversations
6. Extract the downloaded ZIP file
7. Find `conversations.json` in the extracted folder

### 2. Run the Converter

```bash
# Basic usage
python convert_chat_export.py conversations.json

# Specify custom output directory
python convert_chat_export.py conversations.json -o my_chats

# Example with full path
python convert_chat_export.py ~/Downloads/conversations.json
```

### 3. View Your Markdown Files

The converted files will be saved in the `outputs/` directory by default:

```bash
ls outputs/
# Example output:
# How_to_write_Python_code.md
# Machine_Learning_basics.md
# Debugging_techniques.md
```

## Output Format

Each conversation is converted to a Markdown file with the following structure:

```markdown
# Conversation Title

---
**Created:** 2024-01-15 10:30:00
**Last Updated:** 2024-01-15 11:45:00
---

### 👤 User
2024-01-15 10:30:00

Can you explain how to use Python lists?

### 🤖 Assistant
2024-01-15 10:30:15

Certainly! Python lists are one of the most fundamental data structures...

```python
# Example code block
my_list = [1, 2, 3, 4, 5]
my_list.append(6)
print(my_list)  # [1, 2, 3, 4, 5, 6]
```

Lists are mutable and can contain mixed types...
```

## File Structure

```
mlstudio/
├── convert_chat_export.py    # Main converter script
├── chatgpt_parser.py          # ChatGPT format parser
├── outputs/                   # Generated Markdown files (created automatically)
├── sample_data/               # Sample JSON structures for reference
│   └── chatgpt_sample.json
└── README.md                  # This file
```

## Usage Options

```
python convert_chat_export.py <json_file> [options]

Arguments:
  json_file              Path to the chat export JSON file

Options:
  -h, --help            Show help message and exit
  -o, --output-dir DIR  Output directory for Markdown files
                        (default: outputs/)
```

## Supported Formats

### ChatGPT ✅

The parser handles ChatGPT's conversation export format including:

- **Standard conversations**: Text-based Q&A
- **Code blocks**: Properly formatted with language tags
- **Code execution**: Output from ChatGPT Code Interpreter
- **Web browsing**: Results from ChatGPT with Browsing
- **System messages**: Hidden system prompts and context

**Export Location**: Settings → Data Controls → Export

**File**: `conversations.json`

### Claude (Planned)

Architecture supports easy addition of Claude and other services. 

## Extending the Converter

To add support for another chat service:

1. Create a new parser module (e.g., `claude_parser.py`)
2. Implement a parser class with `parse()` method
3. Add format detection in `convert_chat_export.py`
4. Register the parser in the main script

Example parser structure:

```python
class ClaudeParser:
    def parse(self, data):
        # Parse Claude export format
        conversations = []
        # ... parsing logic ...
        return conversations
```

## Example ChatGPT JSON Structure

```json
[
  {
    "title": "Python programming help",
    "create_time": 1705314600.0,
    "update_time": 1705318200.0,
    "mapping": {
      "uuid-1": {
        "id": "uuid-1",
        "message": {
          "id": "uuid-1",
          "author": { "role": "user" },
          "create_time": 1705314600.0,
          "content": {
            "content_type": "text",
            "parts": ["How do I write a Python function?"]
          }
        },
        "parent": null
      },
      "uuid-2": {
        "id": "uuid-2",
        "message": {
          "id": "uuid-2",
          "author": { "role": "assistant" },
          "create_time": 1705314605.0,
          "content": {
            "content_type": "text",
            "parts": ["Here's how to write a Python function..."]
          }
        },
        "parent": "uuid-1"
      }
    }
  }
]
```

## Requirements

- Python 3.7+
- No external dependencies (uses standard library only)

## Troubleshooting

### "Could not detect chat service format"

- Ensure you're using the correct export file format
- For ChatGPT: Use `conversations.json` from the export ZIP
- Verify the JSON file is not corrupted

### "File not found" error

- Check the file path is correct
- Use absolute paths if having issues with relative paths
- Ensure the file extension is `.json`

### Empty or incomplete output

- Some conversations may have no valid messages
- Check that the export includes all conversation data
- System messages or empty conversations are skipped

## License

Part of the Stunts project. See main repository for license information.

## Contributing

Contributions welcome! Areas for enhancement:

- Add support for Claude exports
- Add support for Anthropic API logs
- Include conversation statistics
- Add search/filter functionality
- Generate conversation summaries
- Export to other formats (HTML, PDF)
