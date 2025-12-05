from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.gacha_engine import GachaEngine, BattleState

app = FastAPI(title="Stella Gacha API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = GachaEngine()

# Models
class PullRequest(BaseModel):
    user_id: str
    count: int

class DeckUpdateRequest(BaseModel):
    user_id: str
    deck: Dict[str, Any] # {main: card_index, equip: card_index, support: card_index}

class BattleRequest(BaseModel):
    user_id: str
    opponent_id: str
    user_deck: Dict[str, Any]
    opponent_deck: Dict[str, Any]

@app.get("/")
def read_root():
    return {"status": "online", "service": "Stella Gacha API"}

@app.get("/user/{user_id}")
def get_user(user_id: str):
    player = engine.get_player(user_id)
    return {
        "points": player["points"],
        "inventory_count": len(player["inventory"]),
        "inventory": player["inventory"] # Send full inventory for now
    }

@app.post("/gacha/pull")
def pull_gacha(req: PullRequest):
    player = engine.get_player(req.user_id)
    cost = 100 * req.count
    
    if player["points"] < cost:
        raise HTTPException(status_code=400, detail="Not enough points")
    
    # Deduct
    engine.add_points(req.user_id, -cost)
    
    results = []
    for _ in range(req.count):
        card = engine.generate_random_item()
        # Web pull doesn't support member cards yet (needs guild context)
        # We could add a placeholder or just use items
        card["obtained_at"] = "Web"
        player["inventory"].append(card)
        results.append(card)
        
    engine.save_data()
    return {"results": results, "remaining_points": player["points"]}

@app.post("/battle/simulate")
def simulate_battle(req: BattleRequest):
    # Mock data for battle
    p1_data = {"id": req.user_id, "name": "Player"}
    p2_data = {"id": req.opponent_id, "name": "Opponent"}
    
    # We need to reconstruct full card objects from indices or passed data
    # For simplicity, let's assume the frontend passes the FULL card objects in the deck
    # If passing indices, we'd need to look them up in inventory.
    
    # Let's assume the request body contains the full card objects for now to be stateless-ish
    # But actually, looking up from inventory is safer.
    # Let's support passing full objects for the prototype.
    
    import random
    from utils.gacha_engine import FIELDS
    
    field_key = random.choice(list(FIELDS.keys()))
    field = FIELDS[field_key]
    
    state = BattleState(p1_data, p2_data, req.user_deck, req.opponent_deck, field, engine)
    
    logs = []
    while state.turn <= 3 and state.p1_hp > 0 and state.p2_hp > 0:
        log = state.process_turn()
        logs.append({
            "turn": state.turn - 1,
            "log": log,
            "p1_hp": state.p1_hp,
            "p2_hp": state.p2_hp,
            "p1_max_hp": state.p1_stats["hp"],
            "p2_max_hp": state.p2_stats["hp"]
        })
        
    winner = req.user_id if state.p1_hp > 0 else req.opponent_id
    
    return {
        "field": field,
        "logs": logs,
        "winner": winner
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
