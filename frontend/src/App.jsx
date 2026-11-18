import { NavLink, Route, Routes } from 'react-router-dom'
import Books from './pages/Books.jsx'
import Borrow from './pages/Borrow.jsx'
import Home from './pages/Home.jsx'
import Members from './pages/Members.jsx'
import Return from './pages/Return.jsx'

const NAV = [
  { to: '/', label: 'หน้าหลัก', icon: '🏠' },
  { to: '/books', label: 'หนังสือ', icon: '📚' },
  { to: '/members', label: 'สมาชิก', icon: '👤' },
  { to: '/borrow', label: 'ยืม', icon: '📤' },
  { to: '/return', label: 'คืน', icon: '📥' },
]

export default function App() {
  return (
    <div className="min-h-screen pb-20 md:pb-0">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
          <span className="text-lg font-bold text-teal-800">📖 ห้องสมุด</span>
          {/* เมนูด้านบน: จอใหญ่ */}
          <nav className="hidden gap-1 md:flex">
            {NAV.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 text-sm font-medium ${isActive ? 'bg-teal-50 text-teal-800' : 'text-slate-600 hover:bg-slate-100'}`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-4xl px-4 py-5">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/books" element={<Books />} />
          <Route path="/members" element={<Members />} />
          <Route path="/borrow" element={<Borrow />} />
          <Route path="/return" element={<Return />} />
        </Routes>
      </main>

      {/* เมนูด้านล่าง: มือถือ */}
      <nav className="fixed inset-x-0 bottom-0 z-10 grid grid-cols-5 border-t border-slate-200 bg-white md:hidden">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center py-2 text-xs ${isActive ? 'font-semibold text-teal-700' : 'text-slate-500'}`
            }
          >
            <span className="text-lg leading-none" aria-hidden>
              {item.icon}
            </span>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
