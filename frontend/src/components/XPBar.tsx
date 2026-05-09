interface XPBarProps {
  xp: number
  level: number
  compact?: boolean
}

function xpForLevel(level: number) {
  return level * (level + 1) * 50
}

export default function XPBar({ xp, level, compact }: XPBarProps) {
  const needed = xpForLevel(level)
  const prev = xpForLevel(level - 1)
  const progress = Math.min(Math.max(((xp - prev) / (needed - prev)) * 100, 0), 100)

  return (
    <div style={{ width: '100%' }}>
      {!compact && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
          <span style={{ fontSize: 12, color: 'var(--text-sub)', fontWeight: 500 }}>
            Уровень {level}
          </span>
          <span style={{ fontSize: 12, color: 'var(--text-sub)' }}>
            {xp.toLocaleString()} <span style={{ color: 'var(--text-muted)' }}>/ {needed.toLocaleString()} XP</span>
          </span>
        </div>
      )}

      {/* Track */}
      <div style={{
        width: '100%', height: compact ? 4 : 6,
        background: 'var(--border)',
        borderRadius: 99, overflow: 'hidden',
      }}>
        {/* Fill */}
        <div style={{
          height: '100%',
          width: `${progress}%`,
          background: 'linear-gradient(90deg, #3E7EFF, #00C8FF)',
          borderRadius: 99,
          transition: 'width 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: '0 0 8px rgba(62,126,255,0.5)',
        }} />
      </div>

      {compact && (
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          marginTop: 4,
        }}>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Ур. {level}</span>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>{Math.round(progress)}%</span>
        </div>
      )}
    </div>
  )
}
