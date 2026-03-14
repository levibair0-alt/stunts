#!/bin/bash
# Setup script for Athena Orchestrator environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔧 Setting up Athena Orchestrator environment..."
echo ""

# Check if .env already exists
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "⚠️  .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled. Your existing .env file is preserved."
        exit 0
    fi
    cp "$PROJECT_DIR/.env" "$PROJECT_DIR/.env.backup.$(date +%Y%m%d%H%M%S)"
    echo "📦 Existing .env backed up."
fi

# Copy .env.example to .env
cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
echo "✅ Created .env file from template"
echo ""

# Instructions
echo "📝 Next steps:"
echo ""
echo "1. Edit the .env file and add your API keys:"
echo "   - OpenAI API Key: https://platform.openai.com/api-keys"
echo "   - Anthropic API Key: https://console.anthropic.com/"
echo "   - GitHub Token: https://github.com/settings/tokens"
echo "   - Notion Integration: https://www.notion.so/my-integrations"
echo ""
echo "2. Install dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "3. Run the orchestrator:"
echo "   python runner/main_loop.py"
echo ""
echo "🔑 API Key Quick Links:"
echo ""

# Function to print status
print_status() {
    local name=$1
    local url=$2
    local key_var=$3
    
    if grep -q "^$key_var=your-" "$PROJECT_DIR/.env" 2>/dev/null || \
       grep -q "^$key_var=sk-your-" "$PROJECT_DIR/.env" 2>/dev/null || \
       grep -q "^$key_var=ghp_" "$PROJECT_DIR/.env" 2>/dev/null || \
       ! grep -q "^$key_var=" "$PROJECT_DIR/.env" 2>/dev/null; then
        echo "   ❌ $name: $url"
    else
        echo "   ✅ $name: Configured"
    fi
}

print_status "OpenAI" "https://platform.openai.com/api-keys" "OPENAI_API_KEY"
print_status "Anthropic" "https://console.anthropic.com/" "ANTHROPIC_API_KEY"
print_status "GitHub" "https://github.com/settings/tokens" "GITHUB_TOKEN"
print_status "Notion" "https://www.notion.so/my-integrations" "NOTION_API_KEY"

echo ""
echo "💡 Tip: You can use the following command to load the environment:"
echo "   export \$(cat .env | xargs)"
echo ""
echo "🚀 Setup complete! Edit .env to add your API keys."
