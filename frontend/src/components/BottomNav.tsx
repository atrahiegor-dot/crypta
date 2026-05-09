import { NavLink } from 'react-router-dom'

const TABS = [
  {
    path: '/profile',
    label: 'Профиль',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
        stroke={active ? 'var(--accent)' : 'var(--text-muted)'}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="8" r="4"/>
        <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/>
      </svg>
    ),
  },
  {
    path: '/tasks',
    label: 'Задания',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
        stroke={active ? 'var(--accent)' : 'var(--text-muted)'}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="3"/>
        <path d="M9 12l2 2 4-4"/>
      </svg>
    ),
  },
  {
    path: '/leaderboard',
    label: 'Рейтинг',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
        stroke={active ? 'var(--accent)' : 'var(--text-muted)'}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 18V10M12 18V6M16 18v-4"/>
      </svg>
    ),
  },
  {
    path: '/wallet',
    label: 'Кошелёк',
    icon: (active: boolean) => (
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
        stroke={active ? 'var(--accent)' : 'var(--text-muted)'}
        strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="6" width="20" height="14" rx="3"/>
        <path d="M16 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" fill={active ? 'var(--accent)' : 'var(--text-muted)'} strokeWidth="0"/>
        <path d="M2 10h20"/>
        <path d="M6 6V4"/>
        <path d="M18 6V4"/>
      </svg>
    ),
  },
]

export default function BottomNav() {
  return (
    <nav style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 40,
      background: 'rgba(11,11,18,0.92)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      borderTop: '1px solid var(--border)',
      paddingBottom: 'env(safe-area-inset-bottom, 0px)',
    }}>
      <div style={{ display: 'flex' }}>
        {TABS.map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            style={{ flex: 1, textDecoration: 'none' }}
          >
            {({ isActive }) => (
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center',
                gap: 4, padding: '10px 4px',
                transition: 'opacity 0.15s',
              }}>
                {/* Icon with active glow */}
                <div style={{
                  position: 'relative',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  width: 36, height: 36, borderRadius: 12,
                  background: isActive ? 'rgba(62,126,255,0.12)' : 'transparent',
                  transition: 'background 0.2s',
                }}>
                  {tab.icon(isActive)}
                </div>
                <span style={{
                  fontSize: 10,
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                  transition: 'color 0.15s',
                  letterSpacing: 0.2,
                }}>
                  {tab.label}
                </span>
              </div>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
