import { useState } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { ArrowLeft, Sword, Shield, Zap } from 'lucide-react'

const API_URL = "http://localhost:8000"

export default function BattleScreen({ user, goBack }) {
    const [simulating, setSimulating] = useState(false)
    const [battleData, setBattleData] = useState(null)
    const [opponentId, setOpponentId] = useState('')

    const startBattle = async () => {
        if (!opponentId) {
            alert("Enter opponent ID")
            return
        }

        setSimulating(true)
        setBattleData(null)

        // For prototype, we just pick random cards from inventory for deck
        // In real app, we would have a deck builder
        if (user.inventory.length < 3) {
            alert("You need at least 3 cards!")
            setSimulating(false)
            return
        }

        const deck = {
            main: user.inventory[0],
            equip: user.inventory[1],
            support: user.inventory[2]
        }

        // Mock opponent deck (same as user for now or random if we could)
        // We'll just send the same deck for opponent to simulate a mirror match for testing
        const opponentDeck = deck

        try {
            const res = await axios.post(`${API_URL}/battle/simulate`, {
                user_id: user.id,
                opponent_id: opponentId,
                user_deck: deck,
                opponent_deck: opponentDeck
            })
            setBattleData(res.data)
        } catch (err) {
            alert("Error starting battle")
            console.error(err)
        } finally {
            setSimulating(false)
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="space-y-6"
        >
            <div className="flex items-center gap-4">
                <button onClick={goBack} className="p-2 hover:bg-slate-800 rounded-full transition-colors">
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <h1 className="text-2xl font-bold">Battle Arena</h1>
            </div>

            {!battleData && (
                <div className="max-w-md mx-auto bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <h2 className="text-xl font-bold mb-4">Find Match</h2>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Opponent ID</label>
                            <input
                                type="text"
                                value={opponentId}
                                onChange={(e) => setOpponentId(e.target.value)}
                                className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3"
                                placeholder="Enter ID"
                            />
                        </div>

                        <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
                            <p className="text-sm text-slate-400 mb-2">Your Deck (Auto-selected top 3)</p>
                            <div className="flex gap-2">
                                {user.inventory.slice(0, 3).map((c, i) => (
                                    <div key={i} className="w-12 h-16 bg-slate-800 border border-slate-600 rounded flex items-center justify-center text-xs">
                                        {c.rarity}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={startBattle}
                            disabled={simulating}
                            className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                        >
                            <Sword className="w-5 h-5" />
                            {simulating ? 'Simulating...' : 'Start Battle'}
                        </button>
                    </div>
                </div>
            )}

            {battleData && (
                <div className="space-y-6">
                    <div className="bg-gradient-to-r from-orange-900/50 to-red-900/50 p-4 rounded-xl border border-orange-500/30 flex justify-between items-center">
                        <div>
                            <p className="text-sm text-orange-300">Field Effect</p>
                            <p className="font-bold text-xl">{battleData.field.name}</p>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-orange-300">Bonus</p>
                            <p className="font-bold">{battleData.field.buff || "None"}</p>
                        </div>
                    </div>

                    <div className="space-y-4">
                        {battleData.logs.map((turn, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: i * 0.5 }}
                                className="bg-slate-800 p-4 rounded-xl border border-slate-700"
                            >
                                <div className="flex justify-between mb-2 text-sm text-slate-400">
                                    <span>Turn {turn.turn}</span>
                                    <div className="flex gap-4">
                                        <span className="text-blue-400">P1: {turn.p1_hp}/{turn.p1_max_hp}</span>
                                        <span className="text-red-400">P2: {turn.p2_hp}/{turn.p2_max_hp}</span>
                                    </div>
                                </div>
                                <p className="whitespace-pre-line leading-relaxed">
                                    {turn.log.replace(/\*\*/g, '')}
                                </p>
                            </motion.div>
                        ))}
                    </div>

                    <div className="text-center py-8">
                        <h2 className="text-3xl font-bold mb-2">
                            {battleData.winner === user.id ?
                                <span className="text-yellow-400">VICTORY!</span> :
                                <span className="text-red-500">DEFEAT</span>
                            }
                        </h2>
                        <button
                            onClick={() => setBattleData(null)}
                            className="mt-4 bg-slate-700 hover:bg-slate-600 px-8 py-2 rounded-lg"
                        >
                            Back
                        </button>
                    </div>
                </div>
            )}
        </motion.div>
    )
}
