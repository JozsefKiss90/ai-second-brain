"""Create workstation-specific OpenCode config without replacing existing config."""
import json
import sys
from pathlib import Path
from second_brain.core import default_home

root = Path(__file__).resolve().parent.parent
config = {
    '$schema': 'https://opencode.ai/config.json',
    'permission': {'*': 'ask', 'read': 'allow', 'glob': 'allow', 'grep': 'allow'},
    'mcp': {'brain': {'type': 'local', 'command': [
        sys.executable, '-m', 'second_brain.cli', '--home', str(default_home()), 'mcp'
    ], 'enabled': True, 'timeout': 10000}},
}
path = root / 'opencode.json'
if path.exists() or (root / 'opencode.jsonc').exists():
    path = root / 'opencode.generated.local.json'
    print('Existing configuration retained. Merge the brain MCP block from', path)
path.write_text(json.dumps(config, indent=2), encoding='utf-8')
print('Configuration:', path)
print('Private workspace:', default_home())
