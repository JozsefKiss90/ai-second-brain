import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from second_brain.core import Brain


@unittest.skipUnless(importlib.util.find_spec('mcp'), 'Install .[mcp] for protocol integration test')
class MCPTests(unittest.TestCase):
    def test_stdio_tools_and_source_read(self):
        import anyio
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        with tempfile.TemporaryDirectory() as tmp:
            brain = Brain(tmp)
            brain.init()
            (Path(tmp) / 'inbox' / 'evidence.md').write_text('Use npm.cmd --version\n', encoding='utf-8')
            brain.ingest()
            async def run():
                params = StdioServerParameters(command=sys.executable,
                    args=['-m', 'second_brain.cli', '--home', tmp, 'mcp'], env=dict(os.environ))
                async with stdio_client(params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        names = {tool.name for tool in (await session.list_tools()).tools}
                        self.assertEqual(names, {'brain_search', 'brain_read', 'brain_status', 'brain_profile'})
                        found = await session.call_tool('brain_search', {'query': 'npm'})
                        self.assertFalse(found.isError)
                        text = '\n'.join(x.text for x in found.content if hasattr(x, 'text'))
                        self.assertIn('evidence.md', text)
                        record_id = brain.search('npm')[0]['id']
                        record = await session.call_tool('brain_read', {'record_id': record_id})
                        self.assertFalse(record.isError)
                        self.assertIn('npm.cmd --version', '\n'.join(x.text for x in record.content if hasattr(x, 'text')))
                        error = await session.call_tool('brain_read', {'record_id': 99999})
                        self.assertTrue(error.isError)
            anyio.run(run)
