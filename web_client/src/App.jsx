import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { Sword, Coins, Gift, User, LogOut } from 'lucide-react'
import GachaScreen from './components/GachaScreen'
import BattleScreen from './components/BattleScreen'

const API_URL = "http://localhost:8000"

function App() {
  const [userId, setUserId] = useState('')
  const [user, setUser] = useState(null)
  const [view, setView] = useState('home') // home, gacha, battle
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const login = async () => {
    if (!userId) return
    setLoading(true)
    setError('')
    try {
      const res = await axios.get(`${API_URL}/user/${userId}`)
      setUser({ id: userId, ...res.data })
    } catch (err) {
      setError('User not found or API error')
    } finally {
      setLoading(false)
    }
  }

  const refreshUser = async () => {
    if (!user) return
    try {
      const res = await axios.get(`${API_URL}/user/${user.id}`)
      setUser({ ...user, ...res.data })
    } catch (err) {
      console.error(err)
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gacha-dark text-white p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-slate-800 p-8 rounded-2xl shadow-2xl w-full max-w-md border border-slate-700"
        >
          <h1 className="text-3xl font-bold text-center mb-2 bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">Stella Gacha</h1>
          <p className="text-slate-400 text-center mb-8">Enter your Discord User ID to start</p>

          <div className="space-y-4">
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="User ID (e.g. 123456789)"
              className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 focus:outline-none focus:border-blue-500 transition-colors"
            />
            <button
              onClick={login}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Login'}
            </button>
            {error && <p className="text-red-400 text-center text-sm">{error}</p>}
          </div>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gacha-dark text-white">
      {/* Header */}
      <header className="bg-slate-900/50 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-bold text-xl bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">Stella</span>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
              <Coins className="w-4 h-4 text-gacha-gold" />
              <span className="font-mono font-bold">{user.points.toLocaleString()} SP</span>
            </div>
            <button onClick={() => setUser(null)} className="text-slate-400 hover:text-white">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto p-4 pb-24">
        <AnimatePresence mode="wait">
          {view === 'home' && (
            <motion.div
              key="home"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8"
            >
              <div
                onClick={() => setView('gacha')}
                className="bg-gradient-to-br from-indigo-900 to-slate-900 p-8 rounded-2xl border border-indigo-500/30 cursor-pointer hover:border-indigo-400 transition-all hover:scale-[1.02] group"
              >
                <Gift className="w-12 h-12 text-indigo-400 mb-4 group-hover:rotate-12 transition-transform" />
                <h2 className="text-2xl font-bold mb-2">Gacha</h2>
                <p className="text-slate-400">Spend SP to get rare cards and items.</p>
              </div>

              <div
                onClick={() => setView('battle')}
                className="bg-gradient-to-br from-red-900 to-slate-900 p-8 rounded-2xl border border-red-500/30 cursor-pointer hover:border-red-400 transition-all hover:scale-[1.02] group"
              >
                <Sword className="w-12 h-12 text-red-400 mb-4 group-hover:scale-110 transition-transform" />
                <h2 className="text-2xl font-bold mb-2">Battle</h2>
                <p className="text-slate-400">Fight against opponents using your deck.</p>
              </div>
            </motion.div>
          )}

          {view === 'gacha' && (
            <GachaScreen user={user} refreshUser={refreshUser} goBack={() => setView('home')} />
          )}

          {view === 'battle' && (
            <BattleScreen user={user} goBack={() => setView('home')} />
          )}
        </AnimatePresence>
      </main>

      {/* Bottom Nav (Mobile style but used for desktop too for now) */}
      <nav className="fixed bottom-0 w-full bg-slate-900 border-t border-slate-800 p-4 md:hidden">
        <div className="flex justify-around">
          <button onClick={() => setView('home')} className={`p-2 rounded-lg ${view === 'home' ? 'bg-slate-800 text-white' : 'text-slate-500'}`}>
            <User className="w-6 h-6" />
          </button>
          <button onClick={() => setView('gacha')} className={`p-2 rounded-lg ${view === 'gacha' ? 'bg-slate-800 text-white' : 'text-slate-500'}`}>
            <Gift className="w-6 h-6" />
          </button>
          <button onClick={() => setView('battle')} className={`p-2 rounded-lg ${view === 'battle' ? 'bg-slate-800 text-white' : 'text-slate-500'}`}>
            <Sword className="w-6 h-6" />
          </button>
        </div>
      </nav>
    </div>
  )
}

export default App
