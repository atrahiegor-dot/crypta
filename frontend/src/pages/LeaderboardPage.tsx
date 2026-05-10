import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getLeaderboard } from '../api/endpoints'

const PERIODS = [
  { value: 'all',     label: 'Всё время' },
  { value: 'monthly', label: 'Месяц' },
  { value: 'weekly',  label: 'Неделя' },
] as const

const PODIUM_CONFIG = [
  { index: 1, medal: '🥈', size: 52, height: 60, avatarBg: 'linear-gradient(135deg,#8E8E8E,#5A5A5A)', place: 2, labelColor: '#9E9E9E' },
  { index: 0, medal: '🥇', size: 64, height: 80, avatarBg: 'linear-gradient(135deg,#FFD60A,#FF8C00)', place: 1, labelColor: 'var(--gold)' },
  { index: 2, medal: '🥉', size: 48, height: 44, avatarBg: 'linear-gradient(135deg,#CD7F32,#8B5E3C)', place: 3, labelColor: '#CD7F32' },
]

export default function LeaderboardPage() {
  const [period, setPeriod] = useState<'all' | 'weekly' | 'monthly'>('all')

  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['leaderboard', period],
    queryFn: () => getLeaderboard(period),
    staleTime: 60_000,
  })

  return (
    <div className="anim-up">

      {/* ── Sticky Header ── */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 10,
        background: 'rgba(11,11,18,0.92)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid var(--border)',
        padding: '20px 16px 14px',
      }}>
        <h1 style={{
          fontSize: 22, fontWeight: 800, color: 'var(--text)',
          letterSpacing: -0.5, marginBottom: 14,
        }}>
          Рейтинг
        </h1>

        {/* Period tabs */}
        <div style={{
          display: 'flex',
          background: 'var(--bg-card2)', borderRadius: 14,
          padding: 4, gap: 4,
        }}>
          {PERIODS.map((p) => {
            const active = period === p.value
            return (
              <button
                key={p.value}
                onClick={() => setPeriod(p.value)}
                style={{
                  flex: 1, padding: '8px 0', borderRadius: 10,
                  fontSize: 13, fontWeight: active ? 600 : 400,
                  background: active ? 'var(--bg-card)' : 'transparent',
                  color: active ? 'var(--text)' : 'var(--text-muted)',
                  border: active ? '1px solid var(--border)' : '1px solid transparent',
                  cursor: 'pointer', transition: 'all 0.2s',
                  boxShadow: active ? '0 2px 8px rgba(0,0,0,0.2)' : 'none',
                }}
              >
                {p.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="skeleton" style={{ height: 64, borderRadius: 16 }} />
          ))}
        </div>
      )}

      {!isLoading && (
        <>
          {/* ── Podium ── */}
          {entries.length >= 3 && (
            <div style={{
              padding: '28px 24px 20px',
              background: 'linear-gradient(180deg, rgba(255,214,10,0.06) 0%, transparent 100%)',
              borderBottom: '1px solid var(--border)',
              marginBottom: 12,
            }}>
              <div style={{
                display: 'flex', alignItems: 'flex-end',
                justifyContent: 'center', gap: 12,
              }}>
                {PODIUM_CONFIG.map(({ index, medal, size, height, avatarBg, place, labelColor }) => {
                  const entry = entries[index]
                  if (!entry) return null
                  return (
                    <div key={place} style={{
                      display: 'flex', flexDirection: 'column',
                      alignItems: 'center', gap: 6, flex: 1,
                    }}>
                      {/* Avatar */}
                      <div style={{
                        width: size, height: size, borderRadius: size * 0.3,
                        background: avatarBg,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: size * 0.35, fontWeight: 700, color: 'white',
                        boxShadow: place === 1 ? '0 8px 20px rgba(255,214,10,0.3)' : '0 4px 12px rgba(0,0,0,0.3)',
                        border: place === 1 ? '2px solid rgba(255,214,10,0.4)' : '2px solid rgba(255,255,255,0.1)',
                        flexShrink: 0,
                      }}>
                        {entry.first_name[0]?.toUpperCase()}
                      </div>

                      {/* Name */}
                      <span style={{
                        fontSize: 11, fontWeight: 600,
                        color: 'var(--text-sub)', textAlign: 'center',
                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        maxWidth: '100%',
                      }}>
                        {entry.display_name}
                      </span>

                      {/* XP */}
                      <span style={{ fontSize: 11, fontWeight: 700, color: labelColor }}>
                        {entry.xp_points.toLocaleString()}
                      </span>

                      {/* Podium bar */}
                      <div style={{
                        width: '100%', height: height,
                        background: place === 1
                          ? 'linear-gradient(180deg,rgba(255,214,10,0.2),rgba(255,214,10,0.05))'
                          : place === 2
                          ? 'linear-gradient(180deg,rgba(158,158,158,0.2),rgba(158,158,158,0.05))'
                          : 'linear-gradient(180deg,rgba(205,127,50,0.2),rgba(205,127,50,0.05))',
                        borderRadius: '10px 10px 0 0',
                        border: `1px solid ${place === 1 ? 'rgba(255,214,10,0.2)' : 'rgba(255,255,255,0.05)'}`,
                        borderBottom: 'none',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: 20,
                      }}>
                        {medal}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* ── Full list ── */}
          <div style={{ padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
            {entries.map((entry) => (
              <div
                key={entry.user_id}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12,
                  padding: '12px 14px', borderRadius: 16,
                  background: entry.is_current_user
                    ? 'rgba(62,126,255,0.1)'
                    : 'var(--bg-card)',
                  border: `1px solid ${entry.is_current_user ? 'rgba(62,126,255,0.3)' : 'var(--border)'}`,
                  transition: 'border-color 0.2s',
                }}
              >
                {/* Rank */}
                <div style={{
                  width: 32, textAlign: 'center', flexShrink: 0,
                }}>
                  {entry.rank <= 3 ? (
                    <span style={{ fontSize: 18 }}>
                      {entry.rank === 1 ? '🥇' : entry.rank === 2 ? '🥈' : '🥉'}
                    </span>
                  ) : (
                    <span style={{
                      fontSize: 13, fontWeight: 700,
                      color: entry.is_current_user ? 'var(--accent)' : 'var(--text-muted)',
                    }}>
                      #{entry.rank}
                    </span>
                  )}
                </div>

                {/* Avatar */}
                <div style={{
                  width: 40, height: 40, borderRadius: 13, flexShrink: 0,
                  background: entry.is_current_user
                    ? 'linear-gradient(135deg,#3E7EFF,#00C8FF)'
                    : 'linear-gradient(135deg,#23233A,#18182A)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 15, fontWeight: 700,
                  color: entry.is_current_user ? 'white' : 'var(--text-sub)',
                }}>
                  {entry.first_name[0]?.toUpperCase()}
                </div>

                {/* Name */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{
                    fontSize: 14, fontWeight: 600,
                    color: entry.is_current_user ? 'var(--accent)' : 'var(--text)',
                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                    marginBottom: 2,
                  }}>
                    {entry.display_name}
                    {entry.is_current_user && (
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', marginLeft: 6 }}>(вы)</span>
                    )}
                  </p>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    Уровень {entry.level}
                  </p>
                </div>

                {/* XP */}
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <p style={{ fontSize: 14, fontWeight: 700, color: 'var(--gold)' }}>
                    {entry.xp_points.toLocaleString()}
                  </p>
                  <p style={{ fontSize: 10, color: 'var(--text-muted)' }}>XP</p>
                </div>
              </div>
            ))}

            {entries.length === 0 && (
              <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
                Нет данных
              </div>
            )}
          </div>
        </>
      )}

      <div style={{ height: 16 }} />
    </div>
  )
}
