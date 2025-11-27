"""
AbsData Profile Integration Utility
既存のユーザープロファイルとabsdata.jsonの情報を統合するスクリプト
"""

import json
import os
from pathlib import Path

def load_absdata():
    """Load absdata.json"""
    absdata_path = Path(__file__).parent / 'data' / 'absdata.json'
    if absdata_path.exists():
        with open(absdata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def load_profile(profile_path):
    """Load a user profile"""
    with open(profile_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_profile(profile_path, profile_data):
    """Save a user profile"""
    with open(profile_path, 'w', encoding='utf-8') as f:
        json.dump(profile_data, f, ensure_ascii=False, indent=2)

def find_matching_absdata(profile_data, absdata):
    """
    Find matching absdata entry for a profile
    Matches by nickname or display_name
    """
    nickname = profile_data.get('nickname', '').lower()
    display_name = profile_data.get('display_name', '').lower()
    
    for member in absdata:
        player_name = member.get('プレイヤー名', '').lower()
        if not player_name:
            continue
        
        # Check if player name matches nickname or display name
        if (player_name in nickname or nickname in player_name or
            player_name in display_name or display_name in player_name):
            return member
    
    return None

def integrate_absdata_into_profile(profile_data, absdata_entry):
    """
    Integrate absdata information into a user profile
    """
    changes = []
    
    # Add favorite games
    games = []
    for i in range(1, 4):
        game = absdata_entry.get(f'好きなゲーム{i}')
        if game and game != 'null' and game.strip():
            games.append(game)
    
    if games:
        if 'favorite_games' not in profile_data:
            profile_data['favorite_games'] = []
        for game in games:
            if game not in profile_data['favorite_games']:
                profile_data['favorite_games'].append(game)
                changes.append(f"Added game: {game}")
    
    # Add interests from 主なジャンル
    genre = absdata_entry.get('主なジャンル')
    if genre:
        if 'interests' not in profile_data:
            profile_data['interests'] = []
        genres = [g.strip() for g in genre.split(',')]
        for g in genres:
            if g and g not in profile_data['interests']:
                profile_data['interests'].append(g)
                changes.append(f"Added interest: {g}")
    
    # Add interests from 好きなもの
    favorite_thing = absdata_entry.get('好きなもの')
    if favorite_thing and favorite_thing.strip():
        if 'interests' not in profile_data:
            profile_data['interests'] = []
        if favorite_thing not in profile_data['interests']:
            profile_data['interests'].append(favorite_thing)
            changes.append(f"Added interest: {favorite_thing}")
    
    # Add custom attributes
    if 'custom_attributes' not in profile_data:
        profile_data['custom_attributes'] = {}
    
    # Add role
    role = absdata_entry.get('役職')
    if role and role.strip():
        profile_data['custom_attributes']['AbsCL役職'] = role
        changes.append(f"Added role: {role}")
    
    # Add group
    group = absdata_entry.get('グループ')
    if group and group.strip():
        profile_data['custom_attributes']['グループ'] = group
        changes.append(f"Added group: {group}")
    
    # Add traits from 追記1 and 追記2
    if 'personality_traits' not in profile_data:
        profile_data['personality_traits'] = []
    
    note1 = absdata_entry.get('追記1')
    if note1 and note1.strip():
        if note1 not in profile_data['personality_traits']:
            profile_data['personality_traits'].append(note1)
            changes.append(f"Added trait: {note1}")
    
    note2 = absdata_entry.get('追記2')
    if note2 and note2.strip():
        if note2 not in profile_data['personality_traits']:
            profile_data['personality_traits'].append(note2)
            changes.append(f"Added trait: {note2}")
    
    return changes

def main():
    """Main integration function"""
    print("=== AbsData Profile Integration ===\n")
    
    # Load absdata
    absdata = load_absdata()
    print(f"Loaded {len(absdata)} entries from absdata.json\n")
    
    # Get all profile files
    profiles_dir = Path(__file__).parent / 'data' / 'profiles'
    profile_files = list(profiles_dir.glob('profile_*.json'))
    
    print(f"Found {len(profile_files)} profile files\n")
    
    integrated_count = 0
    total_changes = 0
    
    for profile_path in profile_files:
        try:
            profile_data = load_profile(profile_path)
            
            # Find matching absdata
            matching_absdata = find_matching_absdata(profile_data, absdata)
            
            if matching_absdata:
                player_name = matching_absdata.get('プレイヤー名', 'Unknown')
                print(f"\n✓ Match found for {profile_path.name}")
                print(f"  Player: {player_name}")
                
                # Integrate data
                changes = integrate_absdata_into_profile(profile_data, matching_absdata)
                
                if changes:
                    # Save updated profile
                    save_profile(profile_path, profile_data)
                    integrated_count += 1
                    total_changes += len(changes)
                    
                    print(f"  Changes made ({len(changes)}):")
                    for change in changes:
                        print(f"    - {change}")
                else:
                    print(f"  No new information to add")
            else:
                print(f"\n✗ No match found for {profile_path.name}")
                if profile_data.get('nickname'):
                    print(f"  Nickname: {profile_data['nickname']}")
                if profile_data.get('display_name'):
                    print(f"  Display name: {profile_data['display_name']}")
        
        except Exception as e:
            print(f"\n✗ Error processing {profile_path.name}: {e}")
    
    print(f"\n\n=== Integration Complete ===")
    print(f"Profiles updated: {integrated_count}/{len(profile_files)}")
    print(f"Total changes: {total_changes}")

if __name__ == '__main__':
    main()
