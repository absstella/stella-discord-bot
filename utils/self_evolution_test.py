import sys, os
import asyncio, json

# Add the project root (stella_bot) to PYTHONPATH so utils can be imported
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.self_evolution import ConversationAnalyzer

async def main():
    analyzer = ConversationAnalyzer()
    result = await analyzer.analyze_conversation('明日の14時にリマンドしてほしい', user_id=123)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    asyncio.run(main())
