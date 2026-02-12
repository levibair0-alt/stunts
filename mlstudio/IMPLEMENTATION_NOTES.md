# ML Studio - Chat Export Converter

## Implementation Summary

This Python tool converts AI chat export JSON files (currently ChatGPT) into readable Markdown documents.

## Files Created

### Core Files
1. **`convert_chat_export.py`** (8299 bytes)
   - Main entry point script
   - Command-line argument parsing
   - Format detection
   - Markdown generation
   - File I/O handling

2. **`chatgpt_parser.py`** (9234 bytes)
   - ChatGPT-specific parser module
   - Handles conversation tree structure
   - Extracts messages with roles, content, and timestamps
   - Handles multiple content types (text, code, execution_output, etc.)

3. **`__init__.py`** (303 bytes)
   - Package initialization
   - Exports main functions and classes

### Documentation
4. **`README.md`** (5856 bytes)
   - Complete usage instructions
   - Feature overview
   - Examples and troubleshooting
   - Extensibility guide

### Sample Data
5. **`sample_data/chatgpt_sample.json`** (5036 bytes)
   - Sample ChatGPT export JSON
   - 2 conversations with code blocks
   - Demonstrates various content types

6. **`sample_data/sample_output.md`** (1674 bytes)
   - Example Markdown output
   - Shows formatted result

### Output Directory
7. **`outputs/.gitkeep`** (106 bytes)
   - Ensures directory is tracked by git
   - Generated Markdown files go here

## Features Implemented

✅ Format Detection
- Automatically detects ChatGPT export format
- Extensible architecture for adding other formats

✅ ChatGPT Parser
- Parses conversation tree structure
- Handles message hierarchies
- Extracts all content types:
  - Text
  - Code blocks with language tags
  - Execution output
  - Web browsing results
  - Image attachments

✅ Markdown Generation
- Conversation titles as H1 headers
- Timestamps preserved and formatted
- Role-based message separation (👤 User, 🤖 Assistant, ⚙️ System)
- Code blocks with syntax highlighting
- Clean, readable formatting

✅ File Handling
- Sanitized filenames
- Custom output directory support
- Error handling for missing files
- Batch processing of multiple conversations

✅ CLI Interface
- Command-line arguments
- Help documentation
- Custom output directory option

## Usage Example

```bash
# Basic usage
python convert_chat_export.py conversations.json

# Custom output directory
python convert_chat_export.py conversations.json -o my_chats

# Help
python convert_chat_export.py --help
```

## Testing Results

✅ Sample data conversion successful
✅ 2 conversations converted
✅ Markdown files generated correctly
✅ Code blocks properly formatted
✅ Timestamps preserved
✅ Error handling works (tested with non-existent file)

## Extensibility

To add support for another chat service:

1. Create a new parser module (e.g., `claude_parser.py`)
2. Implement a parser class with `parse()` method
3. Add format detection in `detect_format()`
4. Register the parser in the main script

Example structure:
```python
class ClaudeParser:
    def parse(self, data):
        # Parse Claude export format
        conversations = []
        # ... parsing logic ...
        return conversations
```

## Requirements

- Python 3.7+
- No external dependencies (uses standard library only)

## Notes

- Uses UTF-8 encoding for file I/O
- Handles large exports efficiently
- Preserves conversation metadata
- Generates clean, human-readable Markdown
