# Example Chat Export Files

This directory contains example JSON files demonstrating the structure of various chat service exports.

## Files

### `chatgpt_example.json`

A sample ChatGPT export file with 2 conversations demonstrating:

1. **Python Virtual Environments Tutorial**
   - 4 messages (2 user, 2 assistant)
   - Shows Q&A format with code blocks
   - Demonstrates multi-part conversation

2. **JavaScript Async/Await Explained**
   - 2 messages (1 user, 1 assistant)
   - Includes formatted JavaScript code examples
   - Shows technical documentation style

## Using the Examples

Test the converter with the example file:

```bash
cd mlstudio
python convert_chat_export.py examples/chatgpt_example.json
```

This will generate 2 Markdown files in the `outputs/` directory:
- `001_Python_Virtual_Environments_Tutorial.md`
- `002_JavaScript_Async-Await_Explained.md`

## ChatGPT Export Structure

The example demonstrates the key features of ChatGPT's export format:

```json
[
  {
    "title": "Conversation Title",
    "create_time": 1705320645.789,      // Unix timestamp
    "update_time": 1705324238.901,      // Unix timestamp
    "mapping": {
      "message-id": {
        "id": "message-id",
        "parent": "parent-id",           // null for root
        "children": ["child-id"],
        "message": {
          "id": "message-id",
          "author": {
            "role": "user"               // user, assistant, system, tool
          },
          "create_time": 1705320645.789,
          "content": {
            "content_type": "text",      // text or code
            "parts": ["Message text"]    // Array of content strings
          }
        }
      }
    }
  }
]
```

## Key Features Demonstrated

- ✅ Multiple conversations in one file
- ✅ Message threading (parent-child relationships)
- ✅ Unix timestamps for precise timing
- ✅ Different message roles (user, assistant)
- ✅ Code blocks embedded in messages
- ✅ Multi-line content
- ✅ Technical documentation format

## Creating Your Own Test Data

To create a minimal ChatGPT-format test file:

```json
[
  {
    "title": "My Test Conversation",
    "create_time": 1705320645.789,
    "update_time": 1705320645.789,
    "mapping": {
      "root": {
        "id": "root",
        "parent": null,
        "children": ["msg1"]
      },
      "msg1": {
        "id": "msg1",
        "parent": "root",
        "children": [],
        "message": {
          "id": "msg1",
          "author": {"role": "user"},
          "create_time": 1705320645.789,
          "content": {
            "content_type": "text",
            "parts": ["Hello, world!"]
          }
        }
      }
    }
  }
]
```

## Notes

- Timestamps are Unix time (seconds since epoch) as floats
- The `mapping` is a dictionary/object, not an array
- Each message node can have multiple children (branching conversations)
- The converter follows the first child to build a linear conversation
- Empty or null content is skipped during conversion
