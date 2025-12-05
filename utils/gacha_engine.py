import json
import os
import random
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DATA_FILE = "data/gacha/players.json"
CUSTOM_CARDS_FILE = "data/gacha/custom_cards.json"

# Expanded Item Pool Definitions
ITEM_PREFIXES = ["古びた", "普通の", "上質な", "名匠の", "伝説の", "呪われた", "光り輝く", "暗黒の", "神々の", "異世界の", "失われた", "禁断の", "量産型", "未来の"]
ITEM_SUFFIXES = ["オブ・パワー", "オブ・スピード", "改", "真打", "Mk-II", "V", "X", "Z", "（偽物）", "（本物）", "・極", "・零", "Ω", "α"]

NPC_NAMES = [
    "勇者アルス", "魔法使いマリサ", "戦士ガッツ", "盗賊ルパン", "僧侶クリス", "騎士セイバー", "射手アーチャー", "暗殺者キルア", "武闘家リュウ", "踊り子マイ",
    "魔王の娘", "村の英雄", "謎の旅人", "王宮の兵士", "森のエルフ", "鉱山のドワーフ", "海賊船長", "吸血鬼の貴族", "機械仕掛けの少女", "精霊使い"
]

WEAPON_NAMES = [
    "ロングソード", "グレートアクス", "マジックワンド", "ミスリルダガー", "バトルハンマー", "ドラゴンランス", "妖刀ムラマサ", "ビームサーベル", "チェーンソー", "フライパン",
    "エクスカリバー", "グングニル", "ゲイボルグ", "ロンギヌスの槍", "斬鉄剣", "バスターソード", "ライトセーバー", "モーニングスター", "クロスボウ", "火縄銃"
]

ARMOR_NAMES = [
    "レザーアーマー", "プレートメイル", "魔法のローブ", "ミスリルヘルム", "ドラゴンスケイル", "天使の羽衣", "呪いの鎧", "パワーパワードスーツ", "学生服", "着ぐるみ",
    "イージスの盾", "源氏の鎧", "クリスタルヘルム", "忍び装束", "聖騎士の鎧", "暗黒騎士の鎧", "ビキニアーマー", "フルフェイスメット", "マント", "王冠"
]

ACCESSORY_NAMES = [
    "力の指輪", "守りのアミュレット", "疾風のブーツ", "賢者の石", "フェニックスの尾", "ドラゴンの涙", "天使の輪", "悪魔の尻尾", "猫耳", "眼鏡",
    "エナジードリンク", "ゲーミングマウス", "古びたコイン", "召喚石", "身代わり人形", "幸運のお守り", "呪いの指輪", "王家の紋章", "マフラー", "ヘッドホン"
]

ITEM_NAMES = WEAPON_NAMES + ARMOR_NAMES + ACCESSORY_NAMES # For backward compatibility if needed

ELEMENTS = ["Fire", "Water", "Wind", "Light", "Dark"]
FIELDS = {
    "Plain": {"name": "平原", "buff": None},
    "Volcano": {"name": "火山", "buff": "Fire"},
    "Ocean": {"name": "深海", "buff": "Water"},
    "Forest": {"name": "密林", "buff": "Wind"},
    "Sanctuary": {"name": "聖域", "buff": "Light"},
    "Graveyard": {"name": "墓地", "buff": "Dark"}
}

class GachaEngine:
    def __init__(self):
        self.data = self.load_data()
        self.custom_cards = self.load_custom_cards()
        
    def load_data(self):
        if not os.path.exists("data/gacha"):
            os.makedirs("data/gacha")
        
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def load_custom_cards(self):
        if os.path.exists(CUSTOM_CARDS_FILE):
            try:
                with open(CUSTOM_CARDS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_data(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def save_custom_cards(self):
        with open(CUSTOM_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.custom_cards, f, ensure_ascii=False, indent=2)

    def get_player(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {
                "points": 1000, # Initial bonus
                "pity": 0,
                "inventory": [],
                "last_daily": None,
                "last_chat_point": None
            }
        return self.data[uid]

    def add_points(self, user_id, amount):
        player = self.get_player(user_id)
        player["points"] += amount
        self.save_data()
        return player["points"]

    def set_points(self, user_id, amount):
        player = self.get_player(user_id)
        player["points"] = amount
        self.save_data()
        return player["points"]

    def get_element_advantage(self, atk_elem, def_elem):
        """Return multiplier for attacker"""
        cycle = {"Fire": "Wind", "Wind": "Water", "Water": "Fire"}
        if cycle.get(atk_elem) == def_elem: return 1.5
        if cycle.get(def_elem) == atk_elem: return 0.8
        
        if atk_elem == "Light" and def_elem == "Dark": return 1.5
        if atk_elem == "Dark" and def_elem == "Light": return 1.5
        
        return 1.0

    def generate_stats(self, rarity):
        """Generate Basic ATK/DEF based on rarity"""
        base = {"N": 100, "R": 500, "SR": 1500, "UR": 4000, "LE": 8000}
        variance = 0.2
        
        b = base.get(rarity, 100)
        atk = int(b * random.uniform(1.0 - variance, 1.0 + variance))
        defense = int(b * random.uniform(1.0 - variance, 1.0 + variance))
        
        return {"attack": atk, "defense": defense}

    def generate_advanced_stats(self, rarity, item_type):
        """Generate HP, ATK, DEF, SPD, Element, Skill"""
        base = self.generate_stats(rarity)
        
        # Type Multipliers
        if item_type == "character":
            base["hp"] = base["defense"] * 5
            base["speed"] = random.randint(50, 100)
        elif item_type == "weapon":
            base["attack"] = int(base["attack"] * 1.5)
            base["hp"] = 0
            base["speed"] = random.randint(0, 20)
        elif item_type == "armor":
            base["defense"] = int(base["defense"] * 1.5)
            base["hp"] = base["defense"] * 2
            base["speed"] = random.randint(-10, 10)
        elif item_type == "accessory":
            base["attack"] = int(base["attack"] * 0.5)
            base["defense"] = int(base["defense"] * 0.5)
            base["hp"] = 100
            base["speed"] = random.randint(20, 50)
        else: # Generic item
            base["hp"] = 0
            base["speed"] = 0

        # Rarity Speed Bonus
        base["speed"] += (5 * {"N":1, "R":2, "SR":3, "UR":4, "LE":5}.get(rarity, 1))
        
        # Element
        base["element"] = random.choice(ELEMENTS)
        
        # Skill (Procedural)
        skill_types = ["Attack", "Heal", "Buff", "Debuff"]
        # Bias skill type by item type
        if item_type == "weapon": skill_types = ["Attack", "Debuff"]
        elif item_type == "armor": skill_types = ["Heal", "Buff"]
        elif item_type == "accessory": skill_types = ["Buff", "Debuff", "Heal"]
        
        stype = random.choice(skill_types)
        
        if stype == "Attack":
            base["skill"] = {"name": f"{base['element']} Strike", "type": "attack", "power": 1.5, "effect": None}
            if random.random() < 0.3:
                eff = random.choice(["Poison", "Burn", "Paralyze"])
                base["skill"]["effect"] = eff
                base["skill"]["name"] = f"{eff} Strike"
                
        elif stype == "Heal":
            base["skill"] = {"name": "Healing Light", "type": "heal", "power": 0.3}
            
        elif stype == "Buff":
            base["skill"] = {"name": "Berserk", "type": "buff", "stat": "attack", "amount": 1.5}
            
        elif stype == "Debuff":
            base["skill"] = {"name": "Intimidate", "type": "debuff", "stat": "defense", "amount": 0.5}
            
        return base

    def generate_random_item(self):
        """Generate a procedural RPG item or character"""
        # Check custom cards first (10% chance if available)
        if self.custom_cards and random.random() < 0.1:
            card = random.choice(self.custom_cards)
            if "stats" not in card:
                card["stats"] = self.generate_advanced_stats(card["rarity"], "item")
            return card.copy()

        rarity_roll = random.random()
        if rarity_roll < 0.03: rarity = "UR"
        elif rarity_roll < 0.15: rarity = "SR"
        elif rarity_roll < 0.50: rarity = "R"
        else: rarity = "N"
        if random.random() < 0.001: rarity = "LE"

        # Determine Type
        type_roll = random.random()
        if type_roll < 0.25:
            item_type = "character"
            name = random.choice(NPC_NAMES)
            title = "【仲間】"
        elif type_roll < 0.50:
            item_type = "weapon"
            name = random.choice(WEAPON_NAMES)
            title = "【武器】"
        elif type_roll < 0.75:
            item_type = "armor"
            name = random.choice(ARMOR_NAMES)
            title = "【防具】"
        else:
            item_type = "accessory"
            name = random.choice(ACCESSORY_NAMES)
            title = "【装飾】"

        full_name = ""
        if rarity in ["SR", "UR", "LE"] and item_type != "character":
            prefix = random.choice(ITEM_PREFIXES)
            suffix = random.choice(ITEM_SUFFIXES)
            full_name = f"{prefix}{name}{suffix}"
        else:
            full_name = name

        # Check for asset image
        image_path = None
        assets_dir = "data/gacha/images"
        potential_path = os.path.join(assets_dir, f"{name}.png")
        if os.path.exists(potential_path):
            image_path = os.path.abspath(potential_path)

        return {
            "type": item_type,
            "name": full_name,
            "title": title,
            "rarity": rarity,
            "image_url": None,
            "image_path": image_path,
            "stats": self.generate_advanced_stats(rarity, item_type)
        }

class BattleState:
    def __init__(self, p1_data, p2_data, p1_deck, p2_deck, field, engine):
        self.p1_data = p1_data # {name, id}
        self.p2_data = p2_data
        self.p1_deck = p1_deck # {main, equip, support}
        self.p2_deck = p2_deck
        self.field = field
        self.engine = engine
        self.turn = 1
        self.log = []
        
        # Init Stats
        self.p1_stats = self.calc_stats(p1_deck)
        self.p2_stats = self.calc_stats(p2_deck)
        self.p1_hp = self.p1_stats["hp"]
        self.p2_hp = self.p2_stats["hp"]
        self.p1_status = []
        self.p2_status = []

    def calc_stats(self, deck):
        main = deck["main"]
        equip = deck["equip"]
        
        # Base
        s = main.get("stats", {})
        e = equip.get("stats", {})
        
        # Combine
        total = {
            "hp": s.get("hp", 1000) + e.get("hp", 0),
            "attack": s.get("attack", 100) + e.get("attack", 50),
            "defense": s.get("defense", 100) + e.get("defense", 50),
            "speed": s.get("speed", 50) + e.get("speed", 10),
            "element": s.get("element", "Fire")
        }
        return total

    def process_turn(self):
        log_entry = f"**Turn {self.turn}**\n"
        
        # 1. Status Effects (Start)
        for p, hp, name, status in [(1, self.p1_hp, self.p1_data["name"], self.p1_status), (2, self.p2_hp, self.p2_data["name"], self.p2_status)]:
            if "Poison" in status:
                dmg = int(self.p1_stats["hp"] * 0.05) if p==1 else int(self.p2_stats["hp"] * 0.05)
                if p==1: self.p1_hp -= dmg
                else: self.p2_hp -= dmg
                log_entry += f"☠️ {name}は毒で {dmg} ダメージ！\n"
            if "Burn" in status:
                dmg = int(self.p1_stats["hp"] * 0.1) if p==1 else int(self.p2_stats["hp"] * 0.1)
                if p==1: self.p1_hp -= dmg
                else: self.p2_hp -= dmg
                log_entry += f"🔥 {name}は火傷で {dmg} ダメージ！\n"

        if self.p1_hp <= 0 or self.p2_hp <= 0: return log_entry # End check

        # 2. Action Order
        first = 1 if self.p1_stats["speed"] >= self.p2_stats["speed"] else 2
        
        actors = [(self.p1_data, self.p1_stats, self.p1_deck, self.p1_status), (self.p2_data, self.p2_stats, self.p2_deck, self.p2_status)]
        if first == 2: actors.reverse()
        
        for i, (actor_data, stats, deck, status) in enumerate(actors):
            is_p1 = (actor_data["id"] == self.p1_data["id"])
            target_hp = self.p2_hp if is_p1 else self.p1_hp
            target_stats = self.p2_stats if is_p1 else self.p1_stats
            target_name = self.p2_data["name"] if is_p1 else self.p1_data["name"]
            target_status = self.p2_status if is_p1 else self.p1_status
            
            # Check Skip
            if "Paralyze" in status and random.random() < 0.3:
                log_entry += f"⚡ {actor_data['name']}は麻痺して動けない！\n"
                continue
            if "Freeze" in status:
                log_entry += f"❄️ {actor_data['name']}は凍り付いている！\n"
                status.remove("Freeze")
                continue

            # Action
            dmg = 0
            action_text = ""
            
            # Turn 2: Support Skill
            if self.turn == 2:
                skill = deck["support"].get("stats", {}).get("skill", {"type": "attack", "power": 1.0, "name": "Attack"})
                log_entry += f"✨ {actor_data['name']}のサポートスキル発動！ **{skill['name']}**\n"
                
                if skill["type"] == "attack":
                    dmg = int(stats["attack"] * skill.get("power", 1.0))
                    if skill.get("effect"):
                        target_status.append(skill["effect"])
                        log_entry += f"  -> {target_name}に **{skill['effect']}** を付与！\n"
                elif skill["type"] == "heal":
                    heal = int(stats["hp"] * skill.get("power", 0.3))
                    if is_p1: self.p1_hp += heal
                    else: self.p2_hp += heal
                    log_entry += f"  -> HPが {heal} 回復した！\n"
                elif skill["type"] == "buff":
                    stats[skill["stat"]] *= skill["amount"]
                    log_entry += f"  -> {skill['stat']}がアップ！\n"
            
            else:
                # Normal Attack
                dmg = stats["attack"]
                action_text = "の攻撃！"
            
            if dmg > 0:
                # Calc Modifiers
                # 1. Element
                elem_mod = 1.0
                if self.field["buff"] == stats["element"]:
                    elem_mod *= 1.2
                    log_entry += f"  (フィールド効果! {self.field['name']})\n"
                
                adv_mod = 1.5 if self.engine.get_element_advantage(stats["element"], target_stats["element"]) == 1.5 else 1.0
                if adv_mod > 1.0: log_entry += "  (効果ばつぐんだ！)\n"
                
                # 2. Defense
                final_dmg = int((dmg * elem_mod * adv_mod) - (target_stats["defense"] * 0.5))
                if final_dmg < 1: final_dmg = 1
                
                # 3. Crit
                if random.random() < 0.1:
                    final_dmg = int(final_dmg * 1.5)
                    log_entry += "  **Critical Hit!!**\n"
                
                # Apply
                if is_p1: self.p2_hp -= final_dmg
                else: self.p1_hp -= final_dmg
                
                log_entry += f"💥 {actor_data['name']}{action_text} {target_name}に **{final_dmg}** ダメージ！\n"

            if self.p1_hp <= 0 or self.p2_hp <= 0: break

        self.turn += 1
        return log_entry

    def apply_item(self, user_id, item_card):
        """Apply item effect during intermission"""
        is_p1 = (user_id == self.p1_data["id"])
        stats = self.p1_stats if is_p1 else self.p2_stats
        hp = self.p1_hp if is_p1 else self.p2_hp
        max_hp = stats["hp"]
        
        # Simple Logic:
        # If item has "Heal" in name or type -> Heal
        # Else -> Buff Attack
        
        effect_log = ""
        
        # Determine effect based on item name/stats
        # For now, let's use the item's rarity to determine power
        rarity = item_card.get("rarity", "N")
        power = {"N": 0.1, "R": 0.2, "SR": 0.3, "UR": 0.5, "LE": 1.0}.get(rarity, 0.1)
        
        if "ポーション" in item_card["name"] or "薬" in item_card["name"] or "Heal" in str(item_card):
            heal_amount = int(max_hp * power)
            new_hp = min(max_hp, hp + heal_amount)
            if is_p1: self.p1_hp = new_hp
            else: self.p2_hp = new_hp
            effect_log = f"💚 HPが {heal_amount} 回復した！"
            
        else:
            # Buff Attack
            buff_amount = 1.0 + power
            stats["attack"] = int(stats["attack"] * buff_amount)
            effect_log = f"⚔️ 攻撃力が {int(power*100)}% アップした！"
            
        return effect_log
