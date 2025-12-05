import { useState } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { ArrowLeft, Sparkles } from 'lucide-react'

const API_URL = "http://localhost:8000"

export default function GachaScreen({ user, refreshUser, goBack }) {
    const [pulling, setPulling] = useState(false)
    const [results, setResults] = useState(null)

    const pull = async (count) => {
        if (user.points < count * 100) {
            alert("Not enough points!")
            return
        }

        setPulling(true)
        setResults(null)

        // Fake animation delay
        await new Promise(r => setTimeout(r, 2000))

        try {
            const res = await axios.post(`${API_URL}/gacha/pull`, {
                user_id: user.id,
                count: count
            })
            setResults(res.data.results)
            refreshUser()
        } catch (err) {
            alert("Error pulling gacha")
        } finally {
            setPulling(false)
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
                <h1 className="text-2xl font-bold">Gacha</h1>
            </div>

            {!results && !pulling && (
                <div className="flex flex-col items-center justify-center py-12 gap-8">
                    <div className="w-64 h-64 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-3xl shadow-[0_0_50px_rgba(99,102,241,0.3)] flex items-center justify-center relative overflow-hidden group">
                        <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-30"></div>
                        <Sparkles className="w-32 h-32 text-white/80 group-hover:scale-110 transition-transform duration-500" />
                    </div>

                    <div className="flex gap-4">
                        <button
                            onClick={() => pull(1)}
                            className="bg-slate-800 hover:bg-slate-700 border border-slate-600 px-8 py-4 rounded-xl font-bold transition-all hover:scale-105 active:scale-95"
                        >
                            Pull 1x <br />
                            <span className="text-sm text-gacha-gold font-normal">100 SP</span>
                        </button>
                        <button
                            onClick={() => pull(10)}
                            className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 px-8 py-4 rounded-xl font-bold shadow-lg shadow-indigo-500/30 transition-all hover:scale-105 active:scale-95"
                        >
                            Pull 10x <br />
                            <span className="text-sm text-yellow-200 font-normal">1000 SP</span>
                        </button>
                    </div>
                </div>
            )}

            {pulling && (
                <div className="flex flex-col items-center justify-center py-24">
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                        className="w-24 h-24 border-4 border-indigo-500 border-t-transparent rounded-full"
                    />
                    <p className="mt-8 text-xl font-bold animate-pulse">Summoning...</p>
                </div>
            )}

            {results && (
                <div className="space-y-8">
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        {results.map((card, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.1 }}
                                className={`
                  relative aspect-[3/4] rounded-xl p-3 flex flex-col justify-between overflow-hidden border-2
                  ${card.rarity === 'UR' || card.rarity === 'LE' ? 'border-yellow-400 shadow-[0_0_20px_rgba(250,204,21,0.3)] bg-gradient-to-b from-slate-800 to-yellow-900/20' :
                                        card.rarity === 'SR' ? 'border-yellow-200/50 bg-slate-800' : 'border-slate-700 bg-slate-800'}
                `}
                            >
                                <div className="text-xs font-bold px-2 py-1 bg-black/50 rounded w-fit backdrop-blur-sm">
                                    {card.rarity}
                                </div>

                                <div className="text-center z-10">
                                    <p className="font-bold text-sm line-clamp-2">{card.name}</p>
                                    {card.stats && (
                                        <p className="text-xs text-slate-400 mt-1">ATK: {card.stats.attack}</p>
                                    )}
                                </div>

                                {/* Background decoration */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent pointer-events-none"></div>
                            </motion.div>
                        ))}
                    </div>

                    <div className="flex justify-center">
                        <button
                            onClick={() => setResults(null)}
                            className="bg-slate-700 hover:bg-slate-600 px-8 py-3 rounded-lg font-bold"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </motion.div>
    )
}
