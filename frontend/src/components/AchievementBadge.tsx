const ACHIEVEMENT_MAP: Record<string, { emoji: string; label: string; color: string }> = {
  first_task:          { emoji: '🎯', label: 'Первое задание', color: '#3E7EFF' },
  tasks_10:            { emoji: '🔟', label: '10 заданий',     color: '#30D158' },
  tasks_50:            { emoji: '🏅', label: '50 заданий',     color: '#FF9F0A' },
  tasks_100:           { emoji: '💯', label: '100 заданий',    color: '#FF453A' },
  level_5:             { emoji: '⭐', label: 'Уровень 5',      color: '#FFD60A' },
  level_10:            { emoji: '🌟', label: 'Уровень 10',     color: '#FFD60A' },
  level_25:            { emoji: '✨', label: 'Уровень 25',     color: '#FFD60A' },
  wallet_connected:    { emoji: '💎', label: 'Кошелёк',        color: '#00C8FF' },
  first_referral:      { emoji: '👥', label: 'Первый реф.',    color: '#BF5AF2' },
  referrals_10:        { emoji: '🤝', label: '10 рефералов',   color: '#BF5AF2' },
  top_10_leaderboard:  { emoji: '🏆', label: 'Топ-10',         color: '#FFD60A' },
  daily_streak_7:      { emoji: '🔥', label: '7 дней',         color: '#FF9F0A' },
  daily_streak_30:     { emoji: '💪', label: '30 дней',        color: '#FF453A' },
}

interface AchievementBadgeProps {
  type: string
  size?: 'sm' | 'md'
}

export default function AchievementBadge({ type, size = 'md' }: AchievementBadgeProps) {
  const info = ACHIEVEMENT_MAP[type] || { emoji: '🏆', label: type, color: '#FFD60A' }
  const dim = size === 'sm' ? 40 : 48
  const fontSize = size === 'sm' ? 18 : 22

  return (
    <div
      title={info.label}
      style={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', gap: 6,
        width: size === 'sm' ? 56 : 64,
      }}
    >
      <div style={{
        width: dim, height: dim, borderRadius: 14,
        background: `${info.color}15`,
        border: `1px solid ${info.color}30`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize,
      }}>
        {info.emoji}
      </div>
      <span style={{
        fontSize: 10, color: 'var(--text-muted)',
        textAlign: 'center', lineHeight: 1.3,
      }}>
        {info.label}
      </span>
    </div>
  )
}
