import { useNavigate } from 'react-router-dom'
import type { Task } from '../types'

const CATEGORY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  social: { label: 'Social', color: '#3E7EFF', bg: 'rgba(62,126,255,0.12)' },
  community: { label: 'Community', color: '#30D158', bg: 'rgba(48,209,88,0.12)' },
  development: { label: 'Dev', color: '#00C8FF', bg: 'rgba(0,200,255,0.12)' },
  creative: { label: 'Creative', color: '#BF5AF2', bg: 'rgba(191,90,242,0.12)' },
  special: { label: 'Special', color: '#FFD60A', bg: 'rgba(255,214,10,0.12)' },
}

const DIFFICULTY_CONFIG: Record<string, { label: string; color: string }> = {
  easy: { label: 'Easy', color: 'var(--success)' },
  medium: { label: 'Medium', color: 'var(--warning)' },
  hard: { label: 'Hard', color: 'var(--danger)' },
  legendary: { label: 'Legendary', color: 'var(--gold)' },
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  not_started: { label: 'Доступно', color: 'var(--accent)', bg: 'rgba(62,126,255,0.12)' },
  pending: { label: 'На проверке', color: 'var(--warning)', bg: 'rgba(255,159,10,0.12)' },
  completed: { label: 'Выполнено', color: 'var(--success)', bg: 'rgba(48,209,88,0.12)' },
  rejected: { label: 'Отклонено', color: 'var(--danger)', bg: 'rgba(255,69,58,0.12)' },
}

const CategoryIcon = ({ category }: { category: string }) => {
  const icons: Record<string, JSX.Element> = {
    social: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    community: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    development: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>
      </svg>
    ),
    creative: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/>
        <line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
      </svg>
    ),
    special: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
      </svg>
    ),
  }
  return icons[category] || icons.special
}

interface TaskCardProps {
  task: Task
}

export default function TaskCard({ task }: TaskCardProps) {
  const navigate = useNavigate()
  const cat = CATEGORY_CONFIG[task.category] || CATEGORY_CONFIG.special
  const diff = DIFFICULTY_CONFIG[task.difficulty] || DIFFICULTY_CONFIG.easy
  const status = STATUS_CONFIG[task.user_status] || STATUS_CONFIG.not_started

  return (
    <button
      onClick={() => navigate(`/tasks/${task.id}`)}
      className="card-press"
      style={{
        width: '100%', display: 'flex', alignItems: 'flex-start',
        gap: 14, padding: '14px 16px', textAlign: 'left',
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 16, cursor: 'pointer',
        transition: 'border-color 0.2s, background 0.2s',
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-light)'
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border)'
      }}
    >
      {/* Category icon */}
      <div style={{
        width: 44, height: 44, borderRadius: 12,
        background: cat.bg, color: cat.color,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <CategoryIcon category={task.category} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
          <h3 style={{
            fontSize: 14, fontWeight: 600, color: 'var(--text)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            flex: 1,
          }}>
            {task.title}
          </h3>
          <span style={{
            fontSize: 10, fontWeight: 600, color: diff.color,
            flexShrink: 0, textTransform: 'uppercase', letterSpacing: 0.5,
          }}>
            {diff.label}
          </span>
        </div>

        <p className="line-clamp-2" style={{
          fontSize: 12, color: 'var(--text-sub)', lineHeight: 1.5, marginBottom: 10
        }}>
          {task.description}
        </p>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {/* XP reward */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            background: 'rgba(255,214,10,0.1)', borderRadius: 8,
            padding: '3px 8px',
          }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="var(--gold)">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--gold)' }}>
              +{task.xp_reward} XP
            </span>
          </div>

          {/* Status badge */}
          <span style={{
            fontSize: 11, fontWeight: 500,
            color: status.color, background: status.bg,
            padding: '3px 8px', borderRadius: 8,
          }}>
            {status.label}
          </span>
        </div>
      </div>

      {/* Chevron */}
      <svg style={{ flexShrink: 0, color: 'var(--text-muted)', marginTop: 2 }}
        width="16" height="16" viewBox="0 0 24 24" fill="none"
        stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="9 18 15 12 9 6"/>
      </svg>
    </button>
  )
}
