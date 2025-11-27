"""
Autonomous Feature Development System
ユーザーリクエストに基づいて機能を自律的に生成・実装するシステム
"""

import logging
import json
import os
import re
import asyncio
import google.generativeai as genai
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class FeatureRequestAnalyzer:
    """機能リクエストの分析"""
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
            
    async def analyze_request(self, request_text: str) -> Dict[str, Any]:
        """ユーザーのリクエストを分析して機能要件を抽出"""
        if not self.model:
            return {"error": "Gemini API not available"}
            
        prompt = f"""
        以下のユーザーリクエストを分析し、Discord Botの新機能としての要件をJSON形式で抽出してください。
        
        リクエスト: "{request_text}"
        
        必要な出力形式:
        {{
            "feature_name": "機能名（英語、スネークケース）",
            "description": "機能の概要",
            "commands": [
                {{
                    "name": "コマンド名",
                    "usage": "使用法",
                    "description": "コマンドの説明"
                }}
            ],
            "data_requirements": ["必要なデータ保存（例: jsonファイル）"],
            "complexity": "low/medium/high",
            "is_feasible": true/false
        }}
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text
            # JSONブロックを抽出
            match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                json_str = match.group(1)
            else:
                json_str = text
                
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error analyzing feature request: {e}")
            return {"error": str(e)}

class CodeGenerator:
    """コード自動生成"""
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        else:
            self.model = None
            
    async def generate_cog_code(self, feature_spec: Dict) -> str:
        """機能仕様に基づいてCogのコードを生成"""
        if not self.model:
            return ""
            
        prompt = f"""
        以下の機能仕様に基づいて、Discord.py (Py-cord) のCogクラスのPythonコードを生成してください。
        
        仕様:
        {json.dumps(feature_spec, ensure_ascii=False, indent=2)}
        
        要件:
        1. `commands.Cog` を継承したクラスを作成
        2. 必要なインポートを含める
        3. エラーハンドリングを実装
        4. データの保存/読み込みが必要な場合は `data/` ディレクトリを使用
        5. コードのみを出力（マークダウンのコードブロック内）
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text
            match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1)
            return text
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return ""

    async def modify_code(self, original_code: str, instructions: str) -> str:
        """既存のコードを指示に基づいて修正"""
        if not self.model:
            return ""
            
        prompt = f"""
        以下のPythonコードを、指示に従って修正してください。
        
        指示:
        {instructions}
        
        元のコード:
        ```python
        {original_code}
        ```
        
        要件:
        1. 修正後の完全なコードを出力してください
        2. コードのみを出力（マークダウンのコードブロック内）
        3. 既存の機能は維持しつつ、指示された変更のみを適用してください
        """
        
        try:
            response = await self.model.generate_content_async(prompt)
            text = response.text
            match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
            if match:
                return match.group(1)
            return text
        except Exception as e:
            logger.error(f"Error modifying code: {e}")
            return ""

class FeatureValidator:
    """生成された機能の検証"""
    
    async def validate_code(self, code: str) -> Tuple[bool, str]:
        """コードの構文チェック"""
        try:
            compile(code, '<string>', 'exec')
            return True, "Syntax OK"
        except SyntaxError as e:
            return False, f"Syntax Error: {e}"
        except Exception as e:
            return False, f"Validation Error: {e}"

class FeatureIntegrator:
    """機能の統合と管理"""
    
    def __init__(self, bot_root: str = "."):
        self.bot_root = bot_root
        self.cogs_dir = os.path.join(bot_root, "cogs")
        self.generated_cogs_dir = os.path.join(self.cogs_dir, "generated")
        os.makedirs(self.generated_cogs_dir, exist_ok=True)
        
    async def save_feature(self, feature_name: str, code: str) -> str:
        """生成されたコードをファイルに保存"""
        filename = f"{feature_name}_cog.py"
        filepath = os.path.join(self.generated_cogs_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
            
        return filepath

class AutonomousFeatureManager:
    """自律機能開発の全体管理"""
    
    def __init__(self):
        self.analyzer = FeatureRequestAnalyzer()
        self.generator = CodeGenerator()
        self.validator = FeatureValidator()
        self.integrator = FeatureIntegrator()
        
    async def process_feature_request(self, request_text: str) -> Dict[str, Any]:
        """リクエストから機能生成までのプロセスを実行"""
        # 1. 分析
        analysis = await self.analyzer.analyze_request(request_text)
        if "error" in analysis:
            return {"status": "error", "message": analysis["error"]}
            
        if not analysis.get("is_feasible", False):
            return {"status": "rejected", "message": "Feature deemed not feasible"}
            
        # 2. コード生成
        code = await self.generator.generate_cog_code(analysis)
        if not code:
            return {"status": "error", "message": "Failed to generate code"}
            
        # 3. 検証
        is_valid, validation_msg = await self.validator.validate_code(code)
        if not is_valid:
            return {"status": "error", "message": validation_msg}
            
        # 4. 保存（統合はまだ行わない、ユーザー承認待ち）
        feature_name = analysis.get("feature_name", "unknown_feature")
        filepath = await self.integrator.save_feature(feature_name, code)
        
        return {
            "status": "success",
            "feature_name": feature_name,
            "filepath": filepath,
            "analysis": analysis,
            "code": code
        }
