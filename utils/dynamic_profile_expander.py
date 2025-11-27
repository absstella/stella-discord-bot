"""
動的プロフィール拡張エンジン - プロフィール項目を自動的に追加・拡張
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from database.models import UserProfile

logger = logging.getLogger(__name__)

class DynamicProfileExpander:
    """プロフィール項目を動的に拡張し、多様な情報を保存するエンジン"""
    
    def __init__(self):
        self.category_mappings = {
            # 基本カテゴリのマッピング
            'personal': ['名前', '年齢', '誕生日', '出身地', '住所', '家族構成', '血液型', '星座'],
            'skills': ['プログラミング', '言語', 'デザイン', '楽器', 'スポーツ', '料理', '運転'],
            'work_education': ['職業', '会社', '学校', '専攻', '資格', '経験年数', '職歴'],
            'lifestyle': ['睡眠時間', '起床時間', '運動習慣', '食事制限', '趣味時間', '休日の過ごし方'],
            'preferences': ['食べ物', '音楽', '映画', 'ゲーム', '本', '色', 'ファッション', '旅行先'],
            'social': ['友人関係', 'コミュニティ参加', 'SNS使用', '社交性', 'リーダーシップ'],
            'personality': ['性格', '価値観', 'モチベーション', 'ストレス対処', '決断スタイル'],
            'goals': ['短期目標', '長期目標', '夢', '計画', 'キャリア目標', '学習目標'],
            'opinions': ['政治観', '宗教観', '哲学的思考', '社会問題への意見', 'テクノロジー観'],
            'habits': ['日常ルーティン', '癖', '習慣', '儀式', 'こだわり'],
            'experiences': ['旅行経験', '失敗談', '成功体験', 'トラウマ', '感動体験'],
            'relationships': ['恋愛観', '結婚観', '家族関係', '友人関係', 'メンター関係'],
            'health': ['健康状態', 'アレルギー', '病歴', '運動能力', 'メンタルヘルス'],
            'technology': ['デバイス使用', 'アプリ好み', 'ゲーム傾向', 'プログラミング言語'],
            'creativity': ['創作活動', 'アート好み', '表現方法', 'インスピレーション源'],
            'time_patterns': ['活動時間', '集中時間', '休憩パターン', '季節的変化'],
            'communication': ['話し方', '聞き方', '表現スタイル', '言語使用', 'ユーモア'],
            'learning': ['学習スタイル', '記憶方法', '理解パターン', '興味分野'],
            'entertainment': ['娯楽活動', 'リラックス方法', 'ストレス解消', 'エンターテイメント'],
            'consumption': ['購買行動', 'ブランド好み', '消費パターン', '節約方法'],
            'digital': ['オンライン行動', 'デジタルフットプリント', 'プライバシー意識']
        }
        
        self.dynamic_extractors = {
            'sentiment_patterns': self._extract_sentiment_patterns,
            'language_usage': self._extract_language_usage,
            'topic_interests': self._extract_topic_interests,
            'social_behaviors': self._extract_social_behaviors,
            'temporal_patterns': self._extract_temporal_patterns,
            'emotional_responses': self._extract_emotional_responses,
            'decision_making': self._extract_decision_making,
            'problem_solving': self._extract_problem_solving,
            'learning_indicators': self._extract_learning_indicators,
            'cultural_references': self._extract_cultural_references
        }
    
    async def expand_profile_dynamically(self, profile: UserProfile, conversation_data: Dict) -> Dict[str, Any]:
        """会話データからプロフィールを動的に拡張"""
        expansion_results = {
            'new_categories': [],
            'updated_fields': [],
            'extracted_info': {},
            'confidence_scores': {}
        }
        
        try:
            user_message = conversation_data.get('user_message', '')
            ai_response = conversation_data.get('ai_response', '')
            context = conversation_data.get('context', {})
            
            # 各動的抽出器を実行
            for extractor_name, extractor_func in self.dynamic_extractors.items():
                try:
                    extracted_data = await extractor_func(user_message, ai_response, context)
                    if extracted_data:
                        expansion_results['extracted_info'][extractor_name] = extracted_data
                        
                        # プロフィールに適用
                        applied = await self._apply_extracted_data(profile, extractor_name, extracted_data)
                        if applied:
                            expansion_results['updated_fields'].extend(applied)
                
                except Exception as e:
                    logger.error(f"Error in {extractor_name}: {e}")
            
            # 新しいカテゴリの検出と追加
            new_categories = await self._detect_new_categories(user_message, ai_response)
            for category, items in new_categories.items():
                if await self._add_dynamic_category(profile, category, items):
                    expansion_results['new_categories'].append(category)
            
            # メタ情報の更新
            await self._update_meta_information(profile, expansion_results)
            
            return expansion_results
            
        except Exception as e:
            logger.error(f"Error in dynamic profile expansion: {e}")
            return expansion_results
    
    async def _extract_sentiment_patterns(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """感情パターンの抽出"""
        sentiment_data = {}
        
        # ポジティブ/ネガティブな表現を検出
        positive_patterns = ['嬉しい', '楽しい', '好き', '最高', '素晴らしい', 'いいね', 'ありがとう']
        negative_patterns = ['嫌い', 'つまらない', '悲しい', '疲れた', 'ストレス', '困った']
        
        positive_count = sum(1 for pattern in positive_patterns if pattern in user_message)
        negative_count = sum(1 for pattern in negative_patterns if pattern in user_message)
        
        if positive_count > 0 or negative_count > 0:
            sentiment_data['emotional_tendency'] = {
                'positive_expressions': positive_count,
                'negative_expressions': negative_count,
                'last_detected': datetime.now().isoformat()
            }
        
        return sentiment_data
    
    async def _extract_language_usage(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """言語使用パターンの抽出"""
        language_data = {}
        
        # 敬語使用
        formal_patterns = ['です', 'ます', 'ございます', 'でしょう', 'いらっしゃい']
        casual_patterns = ['だよ', 'だね', 'じゃん', 'かな', 'っす']
        
        formal_count = sum(1 for pattern in formal_patterns if pattern in user_message)
        casual_count = sum(1 for pattern in casual_patterns if pattern in user_message)
        
        if formal_count > 0 or casual_count > 0:
            language_data['speech_formality'] = {
                'formal_expressions': formal_count,
                'casual_expressions': casual_count,
                'ratio': formal_count / (formal_count + casual_count) if (formal_count + casual_count) > 0 else 0.5
            }
        
        # 絵文字・顔文字の使用
        emoji_count = len([c for c in user_message if ord(c) > 0x1F600])
        emoticon_patterns = [':)', ':(', ':D', ';)', 'XD', '^^', '><']
        emoticon_count = sum(1 for pattern in emoticon_patterns if pattern in user_message)
        
        if emoji_count > 0 or emoticon_count > 0:
            language_data['expressive_elements'] = {
                'emoji_usage': emoji_count,
                'emoticon_usage': emoticon_count
            }
        
        return language_data
    
    async def _extract_topic_interests(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """トピックへの興味度抽出"""
        topic_data = {}
        
        # 技術関連トピック
        tech_keywords = ['プログラミング', 'AI', '機械学習', 'データ', 'アプリ', 'ウェブ', 'システム']
        entertainment_keywords = ['ゲーム', 'アニメ', '映画', '音楽', 'マンガ', 'YouTube']
        lifestyle_keywords = ['料理', '旅行', 'ファッション', '健康', 'フィットネス', 'グルメ']
        
        topic_categories = {
            'technology': tech_keywords,
            'entertainment': entertainment_keywords,
            'lifestyle': lifestyle_keywords
        }
        
        for category, keywords in topic_categories.items():
            interest_score = sum(1 for keyword in keywords if keyword in user_message.lower())
            if interest_score > 0:
                if 'topic_engagement' not in topic_data:
                    topic_data['topic_engagement'] = {}
                topic_data['topic_engagement'][category] = {
                    'mentions': interest_score,
                    'last_mentioned': datetime.now().isoformat()
                }
        
        return topic_data
    
    async def _extract_social_behaviors(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """社会的行動パターンの抽出"""
        social_data = {}
        
        # 質問パターン
        question_patterns = ['？', '?', 'どう', '何', 'いつ', 'どこ', 'だれ', 'なぜ']
        question_count = sum(1 for pattern in question_patterns if pattern in user_message)
        
        # 提案パターン
        suggestion_patterns = ['〜したら', '〜してみて', '〜はどう', '提案', 'おすすめ']
        suggestion_count = sum(1 for pattern in suggestion_patterns if pattern in user_message)
        
        if question_count > 0 or suggestion_count > 0:
            social_data['interaction_style'] = {
                'question_frequency': question_count,
                'suggestion_frequency': suggestion_count,
                'engagement_level': (question_count + suggestion_count) / len(user_message.split()) if user_message else 0
            }
        
        return social_data
    
    async def _extract_temporal_patterns(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """時間的パターンの抽出"""
        temporal_data = {}
        
        current_hour = datetime.now().hour
        
        # 時間帯による活動パターン
        if 6 <= current_hour < 12:
            time_period = 'morning'
        elif 12 <= current_hour < 18:
            time_period = 'afternoon'
        elif 18 <= current_hour < 22:
            time_period = 'evening'
        else:
            time_period = 'night'
        
        temporal_data['activity_timing'] = {
            'current_period': time_period,
            'activity_timestamp': datetime.now().isoformat(),
            'message_length': len(user_message),
            'response_complexity': len(user_message.split())
        }
        
        return temporal_data
    
    async def _extract_emotional_responses(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """感情的反応の抽出"""
        emotional_data = {}
        
        # 感情表現の検出
        emotions = {
            'joy': ['嬉しい', '楽しい', '幸せ', 'ハッピー', '最高'],
            'surprise': ['びっくり', '驚いた', 'すごい', 'まじで', 'えー'],
            'sadness': ['悲しい', '辛い', '落ち込む', 'ショック'],
            'anger': ['腹立つ', 'むかつく', 'イライラ', '怒り'],
            'fear': ['怖い', '不安', '心配', 'ドキドキ'],
            'disgust': ['気持ち悪い', 'やだ', '嫌', 'うざい']
        }
        
        detected_emotions = {}
        for emotion, patterns in emotions.items():
            count = sum(1 for pattern in patterns if pattern in user_message)
            if count > 0:
                detected_emotions[emotion] = count
        
        if detected_emotions:
            emotional_data['emotional_expressions'] = {
                'detected_emotions': detected_emotions,
                'dominant_emotion': max(detected_emotions.items(), key=lambda x: x[1])[0],
                'emotional_intensity': sum(detected_emotions.values())
            }
        
        return emotional_data
    
    async def _extract_decision_making(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """意思決定パターンの抽出"""
        decision_data = {}
        
        # 決断関連の表現
        decisive_patterns = ['決めた', '決定', '決める', 'やる', '実行']
        hesitant_patterns = ['迷う', 'どうしよう', '悩む', '分からない', 'うーん']
        
        decisive_count = sum(1 for pattern in decisive_patterns if pattern in user_message)
        hesitant_count = sum(1 for pattern in hesitant_patterns if pattern in user_message)
        
        if decisive_count > 0 or hesitant_count > 0:
            decision_data['decision_style'] = {
                'decisive_expressions': decisive_count,
                'hesitant_expressions': hesitant_count,
                'decision_speed': decisive_count / (decisive_count + hesitant_count) if (decisive_count + hesitant_count) > 0 else 0.5
            }
        
        return decision_data
    
    async def _extract_problem_solving(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """問題解決パターンの抽出"""
        problem_data = {}
        
        # 問題解決アプローチ
        analytical_patterns = ['分析', '考える', '理由', '原因', '論理']
        creative_patterns = ['アイデア', '工夫', '創造', '発想', 'ひらめき']
        practical_patterns = ['試す', '実験', '実践', 'やってみる', '行動']
        
        approaches = {
            'analytical': analytical_patterns,
            'creative': creative_patterns,
            'practical': practical_patterns
        }
        
        approach_scores = {}
        for approach, patterns in approaches.items():
            score = sum(1 for pattern in patterns if pattern in user_message)
            if score > 0:
                approach_scores[approach] = score
        
        if approach_scores:
            problem_data['problem_solving_style'] = {
                'approach_scores': approach_scores,
                'dominant_approach': max(approach_scores.items(), key=lambda x: x[1])[0],
                'versatility': len(approach_scores)
            }
        
        return problem_data
    
    async def _extract_learning_indicators(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """学習指標の抽出"""
        learning_data = {}
        
        # 学習関連の表現
        learning_patterns = ['学ぶ', '覚える', '理解', '勉強', '習得', '知りたい']
        teaching_patterns = ['教える', '説明', '伝える', '共有', 'シェア']
        
        learning_count = sum(1 for pattern in learning_patterns if pattern in user_message)
        teaching_count = sum(1 for pattern in teaching_patterns if pattern in user_message)
        
        if learning_count > 0 or teaching_count > 0:
            learning_data['knowledge_orientation'] = {
                'learning_expressions': learning_count,
                'teaching_expressions': teaching_count,
                'knowledge_sharing_ratio': teaching_count / (learning_count + teaching_count) if (learning_count + teaching_count) > 0 else 0
            }
        
        return learning_data
    
    async def _extract_cultural_references(self, user_message: str, ai_response: str, context: Dict) -> Dict:
        """文化的参照の抽出"""
        cultural_data = {}
        
        # 文化的要素
        japanese_cultural = ['和食', '寿司', '天ぷら', '着物', '祭り', '桜', '神社']
        western_cultural = ['ハンバーガー', 'ピザ', 'クリスマス', 'ハロウィン']
        modern_cultural = ['SNS', 'インスタ', 'ツイッター', 'TikTok', 'YouTube']
        
        cultural_categories = {
            'japanese_traditional': japanese_cultural,
            'western': western_cultural,
            'digital_modern': modern_cultural
        }
        
        cultural_references = {}
        for category, references in cultural_categories.items():
            count = sum(1 for ref in references if ref in user_message)
            if count > 0:
                cultural_references[category] = count
        
        if cultural_references:
            cultural_data['cultural_familiarity'] = {
                'cultural_references': cultural_references,
                'cultural_diversity': len(cultural_references),
                'dominant_culture': max(cultural_references.items(), key=lambda x: x[1])[0]
            }
        
        return cultural_data
    
    async def _detect_new_categories(self, user_message: str, ai_response: str) -> Dict[str, List]:
        """新しいカテゴリの検出"""
        new_categories = {}
        
        # 特殊な興味分野の検出
        specialized_interests = [
            '投資', '株', '仮想通貨', 'NFT', 'DeFi',
            'ヨガ', '瞑想', 'マインドフルネス',
            'コスプレ', '同人', 'ボードゲーム',
            'キャンプ', 'アウトドア', '登山',
            'カメラ', '写真', '動画編集',
            'ペット', '動物', '植物', 'ガーデニング'
        ]
        
        detected_interests = [interest for interest in specialized_interests if interest in user_message]
        if detected_interests:
            new_categories['specialized_interests'] = detected_interests
        
        return new_categories
    
    async def _apply_extracted_data(self, profile: UserProfile, extractor_name: str, extracted_data: Dict) -> List[str]:
        """抽出されたデータをプロフィールに適用"""
        applied_fields = []
        
        try:
            # 動的属性に保存
            if not hasattr(profile, 'dynamic_attributes') or profile.dynamic_attributes is None:
                profile.dynamic_attributes = {}
            
            if extractor_name not in profile.dynamic_attributes:
                profile.dynamic_attributes[extractor_name] = {}
            
            # データをマージ
            for key, value in extracted_data.items():
                if key in profile.dynamic_attributes[extractor_name]:
                    # 既存データとマージ
                    if isinstance(value, dict) and isinstance(profile.dynamic_attributes[extractor_name][key], dict):
                        profile.dynamic_attributes[extractor_name][key].update(value)
                    else:
                        profile.dynamic_attributes[extractor_name][key] = value
                else:
                    profile.dynamic_attributes[extractor_name][key] = value
                
                applied_fields.append(f"{extractor_name}.{key}")
            
            return applied_fields
            
        except Exception as e:
            logger.error(f"Error applying extracted data: {e}")
            return []
    
    async def _add_dynamic_category(self, profile: UserProfile, category: str, items: List) -> bool:
        """動的カテゴリの追加"""
        try:
            # 適切なプロフィールフィールドに保存
            field_mapping = {
                'specialized_interests': 'interests',
                'cultural_preferences': 'media_preferences',
                'lifestyle_choices': 'lifestyle_and_habits',
                'professional_skills': 'skills_and_abilities'
            }
            
            target_field = field_mapping.get(category)
            if target_field and hasattr(profile, target_field):
                field_dict = getattr(profile, target_field)
                if not isinstance(field_dict, dict):
                    field_dict = {}
                    setattr(profile, target_field, field_dict)
                
                field_dict[category] = items
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding dynamic category: {e}")
            return False
    
    async def _update_meta_information(self, profile: UserProfile, expansion_results: Dict):
        """メタ情報の更新"""
        try:
            if not hasattr(profile, 'dynamic_attributes') or profile.dynamic_attributes is None:
                profile.dynamic_attributes = {}
            
            if '_meta' not in profile.dynamic_attributes:
                profile.dynamic_attributes['_meta'] = {}
            
            profile.dynamic_attributes['_meta'].update({
                'last_expansion': datetime.now().isoformat(),
                'expansion_count': profile.dynamic_attributes['_meta'].get('expansion_count', 0) + 1,
                'total_categories': len(expansion_results.get('new_categories', [])),
                'total_fields_updated': len(expansion_results.get('updated_fields', []))
            })
            
        except Exception as e:
            logger.error(f"Error updating meta information: {e}")