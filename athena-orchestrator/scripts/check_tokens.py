#!/usr/bin/env python3
"""
Check and validate API tokens for Athena Orchestrator.
"""

import os
import sys
from pathlib import Path


def load_env_file(env_path: Path) -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    return env_vars


def check_token(name: str, env_var: str, expected_prefix: str = None, env_vars: dict = None) -> bool:
    """Check if a token is configured."""
    value = env_vars.get(env_var) or os.environ.get(env_var, '')
    
    if not value:
        print(f"  ❌ {name}: Not set ({env_var})")
        return False
    
    if expected_prefix and not value.startswith(expected_prefix):
        print(f"  ⚠️  {name}: Unexpected format ({env_var})")
        return False
    
    if 'your-' in value.lower() or 'placeholder' in value.lower():
        print(f"  ❌ {name}: Using placeholder value ({env_var})")
        return False
    
    masked = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
    print(f"  ✅ {name}: Configured ({masked})")
    return True


def main():
    """Main validation function."""
    project_dir = Path(__file__).parent.parent
    env_path = project_dir / '.env'
    
    print("🔍 Checking Athena Orchestrator API Tokens")
    print("=" * 50)
    print()
    
    # Load environment file
    env_vars = load_env_file(env_path)
    
    if env_vars:
        print(f"📄 Loaded {len(env_vars)} variables from .env")
        print()
    
    # Check LLM providers
    print("🤖 LLM Providers:")
    llm_ok = True
    llm_ok &= check_token("OpenAI", "OPENAI_API_KEY", "sk-", env_vars)
    llm_ok &= check_token("Anthropic", "ANTHROPIC_API_KEY", "sk-ant", env_vars)
    llm_ok &= check_token("Gemini", "GEMINI_API_KEY", None, env_vars)
    llm_ok &= check_token("xAI/Grok", "XAI_API_KEY", "xai-", env_vars)
    print()
    
    # Check integrations
    print("🔗 Integrations:")
    integrations_ok = True
    integrations_ok &= check_token("GitHub", "GITHUB_TOKEN", "ghp_", env_vars)
    integrations_ok &= check_token("Notion", "NOTION_API_KEY", "secret_", env_vars)
    integrations_ok &= check_token("CTO.new", "CTO_API_KEY", None, env_vars)
    print()
    
    # Check optional services
    print("📊 Optional Services:")
    check_token("Sentry", "SENTRY_DSN", "https://", env_vars)
    print()
    
    # Summary
    print("=" * 50)
    if llm_ok and integrations_ok:
        print("✅ All required tokens are configured!")
        print()
        print("🚀 You can now run the orchestrator:")
        print("   python runner/main_loop.py")
        return 0
    else:
        print("⚠️  Some tokens are missing or using placeholder values.")
        print()
        print("📝 To set up your environment:")
        print("   1. Edit .env file with your API keys")
        print("   2. Or run: export $(cat .env | xargs)")
        print()
        print("🔗 Quick Links:")
        print("   OpenAI: https://platform.openai.com/api-keys")
        print("   Anthropic: https://console.anthropic.com/")
        print("   GitHub: https://github.com/settings/tokens")
        print("   Notion: https://www.notion.so/my-integrations")
        return 1


if __name__ == "__main__":
    sys.exit(main())
