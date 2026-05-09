import { useQuery } from '@tanstack/react-query'
import { getProfile, getSubmissions } from '../api/endpoints'
import { useAuthStore } from '../store/authStore'
import XPBar from '../components/XPBar'
import AchievementBadge from '../components/AchievementBadge'

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  approved:  { label: 'Одобрено',    color: 'var(--success)', icon: '✓' },
  pending:   { label: 'На проверке', color: 'var(--warning)', icon: '⏳' },
  rejected:  { label: 'Отклонено',   color: 'var(--danger)',  icon: '✗' },
  cancelled: { label: 'Отменено',    color: 'var(--text-muted)', icon: '—' },
}

function StatCard({ label, value, icon }: { label: string; value: string | number; icon: React.ReactNode }) {
  return (
    <div style={{
      background: 'var(--bg-card)', border: '1px solid var(--border)',
      borderRadius: 16, padding: '14px 10px', textAlign: 'center',
      flex: 1,
    }}>
      <div style={{ color: 'var(--text-sub)', marginBottom: 6, display: 'flex', justifyContent: 'center' }}>
        {icon}
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', marginBottom: 2 }}>
        {value}
      </div>
      <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{label}</div>
    </div>
  )
}

export default function ProfilePage() {
  const { profile: cachedProfile } = useAuthStore()

  const { data: profile } = useQuery({
    queryKey: ['profile'],
    queryFn: getProfile,
    initialData: cachedProfile ?? undefined,
    staleTime: 30_000,
  })

  const { data: submissions = [] } = useQuery({
    queryKey: ['submissions'],
    queryFn: () => getSubmissions(10),
    staleTime: 30_000,
  })

  if (!profile) {
    return (
      <div style={{ padding: '48px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {[1, 2, 3].map(i => (
          <div key={i} className="skeleton" style={{ height: 72, borderRadius: 16 }} />
        ))}
      </div>
    )
  }

  const initials = (profile.first_name[0] + (profile.last_name?.[0] || '')).toUpperCase()

  return (
    <div className="anim-up" style={{ paddingBottom: 24 }}>

      {/* ── Hero Banner ── */}
      <div style={{
        padding: '32px 20px 24px',
        background: 'linear-gradient(180deg, rgba(62,126,255,0.12) 0%, transparent 100%)',
        borderBottom: '1px solid var(--border)',
        marginBottom: 20,
      }}>
        {/* Avatar + Name */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 20 }}>
          <div style={{
            width: 64, height: 64, borderRadius: 20, flexShrink: 0,
            background: 'linear-gradient(135deg, #3E7EFF, #00C8FF)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 24, fontWeight: 700, color: 'white',
            boxShadow: '0 8px 24px rgba(62,126,255,0.3)',
          }}>
            {initials}
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <h1 style={{
              fontSize: 20, fontWeight: 700, color: 'var(--text)',
              marginBottom: 6, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'
            }}>
              {profile.display_name}
            </h1>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <span style={{
                fontSize: 11, fontWeight: 600, letterSpacing: 0.3,
                background: 'rgba(62,126,255,0.15)', color: 'var(--accent)',
                padding: '3px 10px', borderRadius: 99,
              }}>
                Уровень {profile.level}
              </span>
              {profile.role === 'developer' && (
                <span style={{
                  fontSize: 11, fontWeight: 600,
                  background: 'rgba(255,214,10,0.15)', color: 'var(--gold)',
                  padding: '3px 10px', borderRadius: 99,
                }}>
                  Admin
                </span>
              )}
              {profile.role === 'moderator' && (
                <span style={{
                  fontSize: 11, fontWeight: 600,
                  background: 'rgba(191,90,242,0.15)', color: '#BF5AF2',
                  padding: '3px 10px', borderRadius: 99,
                }}>
                  Mod
                </span>
              )}
            </div>
          </div>
        </div>

        {/* XP Bar */}
        <XPBar xp={profile.xp_points} level={profile.level} />
      </div>

      {/* ── Stats ── */}
      <div style={{ padding: '0 16px', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 10 }}>
          <StatCard
            label="Рейтинг"
            value={`#${profile.rank}`}
            icon={
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M8 18V10M12 18V6M16 18v-4"/>
              </svg>
            }
          />
          <StatCard
            label="Заданий"
            value={profile.tasks_completed}
            icon={
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <rect x="3" y="3" width="18" height="18" rx="3"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
            }
          />
          <StatCard
            label="Рефералов"
            value={profile.referrals_count}
            icon={
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            }
          />
        </div>
      </div>

      {/* ── Info Cards ── */}
      <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>

        {/* Wallet */}
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 16, padding: '14px 16px',
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12, flexShrink: 0,
            background: profile.wallet_connected ? 'rgba(0,200,255,0.12)' : 'rgba(136,136,170,0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: profile.wallet_connected ? '#00C8FF' : 'var(--text-muted)',
          }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <rect x="2" y="6" width="20" height="14" rx="3"/>
              <path d="M2 10h20"/>
              {profile.wallet_connected && <circle cx="16" cy="16" r="1.5" fill="currentColor" stroke="none"/>}
            </svg>
          </div>
          <div style={{ flex: 1 }}>
            <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>
              {profile.wallet_connected ? 'Кошелёк подключён' : 'Кошелёк не подключён'}
            </p>
            {profile.wallet_address ? (
              <p style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                {profile.wallet_address.slice(0, 8)}…{profile.wallet_address.slice(-6)}
              </p>
            ) : (
              <p style={{ fontSize: 12, color: 'var(--accent)' }}>Подключи и получи +500 XP →</p>
            )}
          </div>
          {profile.wallet_connected && (
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--success)', flexShrink: 0 }} />
          )}
        </div>

        {/* Streak */}
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 16, padding: '14px 16px',
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <div style={{
            width: 40, height: 40, borderRadius: 12, flexShrink: 0,
            background: 'rgba(255,159,10,0.12)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 20,
          }}>
            🔥
          </div>
          <div>
            <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)', marginBottom: 2 }}>
              Серия: <span style={{ color: 'var(--warning)' }}>{profile.daily_streak} дней</span>
            </p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>Заходи каждый день для бонуса</p>
          </div>
        </div>

        {/* Referral code */}
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 16, padding: '14px 16px',
        }}>
          <p style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.8 }}>
            Реферальный код
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{
              fontSize: 18, fontWeight: 700, color: 'var(--text)',
              fontFamily: 'monospace', letterSpacing: 2,
            }}>
              {profile.referral_code}
            </p>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round">
              <rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
            </svg>
          </div>
        </div>
      </div>

      {/* ── Achievements ── */}
      {profile.achievements.length > 0 && (
        <div style={{ padding: '0 16px', marginBottom: 20 }}>
          <p style={{
            fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
            textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14,
          }}>
            Достижения
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            {profile.achievements.map((a) => (
              <AchievementBadge key={a.type} type={a.type} />
            ))}
          </div>
        </div>
      )}

      {/* ── Recent submissions ── */}
      {submissions.length > 0 && (
        <div style={{ padding: '0 16px' }}>
          <p style={{
            fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
            textTransform: 'uppercase', letterSpacing: 1, marginBottom: 14,
          }}>
            История заданий
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {submissions.map((sub) => {
              const s = STATUS_CONFIG[sub.status]
              return (
                <div key={sub.id} style={{
                  background: 'var(--bg-card)', border: '1px solid var(--border)',
                  borderRadius: 14, padding: '12px 16px',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{
                      fontSize: 13, fontWeight: 500, color: 'var(--text)',
                      overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      marginBottom: 2,
                    }}>
                      {sub.task_title || `Задание #${sub.task_id}`}
                    </p>
                    <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                      {new Date(sub.submitted_at).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                  <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: 12 }}>
                    <p style={{ fontSize: 12, fontWeight: 500, color: s?.color }}>
                      {s?.icon} {s?.label || sub.status}
                    </p>
                    {sub.xp_awarded > 0 && (
                      <p style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold)' }}>
                        +{sub.xp_awarded} XP
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
