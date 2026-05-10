import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getTasks } from '../api/endpoints'
import TaskCard from '../components/TaskCard'
import type { TaskCategory } from '../types'

const CATEGORIES: Array<{ value: TaskCategory | ''; label: string }> = [
  { value: '', label: 'Все' },
  { value: 'social', label: 'Social' },
  { value: 'community', label: 'Community' },
  { value: 'development', label: 'Dev' },
  { value: 'creative', label: 'Creative' },
  { value: 'special', label: 'Special' },
]

function SectionLabel({ children, count, color }: { children: string; count: number; color?: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
      <p style={{
        fontSize: 11, fontWeight: 700, color: color || 'var(--text-muted)',
        textTransform: 'uppercase', letterSpacing: 1,
      }}>
        {children}
      </p>
      <div style={{
        height: 18, minWidth: 18, borderRadius: 6,
        background: color ? `${color}20` : 'var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '0 5px',
      }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: color || 'var(--text-muted)' }}>
          {count}
        </span>
      </div>
    </div>
  )
}

export default function TasksPage() {
  const [category, setCategory] = useState<TaskCategory | ''>('')

  const { data: tasks = [], isLoading } = useQuery({
    queryKey: ['tasks', category],
    queryFn: () => getTasks(category || undefined),
    staleTime: 60_000,
  })

  const notStarted = tasks.filter((t) => t.user_status === 'not_started')
  const inProgress = tasks.filter((t) => t.user_status === 'pending')
  const done = tasks.filter((t) => t.user_status === 'completed')

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
          Задания
        </h1>

        {/* Category filter chips */}
        <div className="scrollbar-hide" style={{
          display: 'flex', gap: 8, overflowX: 'auto',
          paddingBottom: 2,
        }}>
          {CATEGORIES.map((cat) => {
            const active = category === cat.value
            return (
              <button
                key={cat.value}
                onClick={() => setCategory(cat.value as TaskCategory | '')}
                style={{
                  padding: '6px 14px', borderRadius: 99, whiteSpace: 'nowrap',
                  fontSize: 13, fontWeight: active ? 600 : 400,
                  background: active ? 'var(--accent)' : 'var(--bg-card2)',
                  color: active ? 'white' : 'var(--text-sub)',
                  border: `1px solid ${active ? 'var(--accent)' : 'var(--border)'}`,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                }}
              >
                {cat.label}
              </button>
            )
          })}
        </div>
      </div>

      {/* ── Content ── */}
      <div style={{ padding: '16px 16px 0' }}>

        {/* Loading skeleton */}
        {isLoading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="skeleton" style={{ height: 88, borderRadius: 16 }} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!isLoading && tasks.length === 0 && (
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', padding: '60px 24px', textAlign: 'center',
          }}>
            <div style={{
              width: 64, height: 64, borderRadius: 20,
              background: 'var(--bg-card2)', border: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 16, fontSize: 28,
            }}>
              📭
            </div>
            <p style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)', marginBottom: 6 }}>
              Нет заданий
            </p>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              В этой категории пока нет доступных заданий
            </p>
          </div>
        )}

        {/* In progress */}
        {inProgress.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <SectionLabel color="var(--warning)" count={inProgress.length}>На проверке</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {inProgress.map((t) => <TaskCard key={t.id} task={t} />)}
            </div>
          </div>
        )}

        {/* Available */}
        {notStarted.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <SectionLabel count={notStarted.length}>Доступно</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {notStarted.map((t) => <TaskCard key={t.id} task={t} />)}
            </div>
          </div>
        )}

        {/* Completed */}
        {done.length > 0 && (
          <div style={{ marginBottom: 20 }}>
            <SectionLabel color="var(--success)" count={done.length}>Выполнено</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {done.map((t) => <TaskCard key={t.id} task={t} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
