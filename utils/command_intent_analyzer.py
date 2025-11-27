"""
Command Intent Analyzer
ユーザーの自然言語メッセージからBotコマンドの意図を抽出し、実行可能なコマンドに変換する
"""

import logging
import json
import os
import google.generativeai as genai
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class CommandIntentAnalyzer:
    def __init__(self, bot_commands: List[Dict]):
        """
        Args:
            bot_commands: 利用可能なコマンドのリスト
            [{"name": "play", "description": "音楽を再生", "args": ["query"]}, ...]
        """
        self.bot_commands = bot_commands
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None

    async def analyze_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """メッセージからコマンド意図を分析"""
        if not self.model:
            return None

        # コマンドリストをプロンプト用に整形
        commands_desc = json.dumps(self.bot_commands, ensure_ascii=False, indent=2)

        prompt = f"""
        以下のユーザーメッセージが、Botの特定のコマンドを実行する意図を含んでいるか判断してください。
        
        利用可能なコマンド:
        {commands_desc}
        
        ユーザーメッセージ: "{message}"
        
        もしコマンド実行の意図が明確な場合、以下のJSON形式で出力してください。
        意図がない、または単なる会話の場合は null を出力してください。
        
        出力形式:
        {{
            "command": "コマンド名（プレフィックスなし）",
            "args": ["引数1", "引数2", ...],
            "confidence": 0.0〜1.0
        }}
        """

        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text.strip()
            
            if text == "null":
                return None
                
            # JSON抽出
            import re
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            json_str = match.group(1) if match else text
            
            result = json.loads(json_str)
            
            if result and result.get("confidence", 0) > 0.8:
                return result
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing command intent: {e}")
            return None
