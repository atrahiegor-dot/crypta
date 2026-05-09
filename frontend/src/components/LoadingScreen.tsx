export default function LoadingScreen() {
  return (
    <div style={{
      position: 'fixed', inset: 0, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg)', zIndex: 50
    }}>
      {/* Logo */}
      <div style={{
        width: 80, height: 80, borderRadius: 24,
        background: 'linear-gradient(135deg, #3E7EFF 0%, #00C8FF 100%)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: 20,
        boxShadow: '0 0 40px rgba(62,126,255,0.4), 0 16px 40px rgba(0,0,0,0.4)'
      }}>
        <svg width="36" height="36" viewBox="0 0 24 24" fill="none">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"
            fill="white" stroke="white" strokeWidth="1.5"
            strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>

      <h1 style={{ color: 'var(--text)', fontSize: 26, fontWeight: 800, marginBottom: 6, letterSpacing: -0.5 }}>
        Tasker
      </h1>
      <p style={{ color: 'var(--text-sub)', fontSize: 13, marginBottom: 32 }}>
        Загрузка...
      </p>

      {/* Animated dots */}
      <div style={{ display: 'flex', gap: 8 }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: 8, height: 8, borderRadius: '50%',
              background: 'var(--accent)',
              animation: 'loadDot 1.2s ease-in-out infinite',
              animationDelay: `${i * 0.2}s`,
              opacity: 0.3,
            }}
          />
        ))}
      </div>

      <style>{`
        @keyframes loadDot {
          0%, 100% { opacity: 0.3; transform: translateY(0); }
          50% { opacity: 1; transform: translateY(-6px); }
        }
      `}</style>
    </div>
  )
}
