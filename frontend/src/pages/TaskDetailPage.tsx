import { useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTask, submitTask } from '../api/endpoints'

const DIFFICULTY_CONFIG: Record<string, { label: string; color: string }> = {
  easy:      { label: 'Easy',      color: 'var(--success)' },
  medium:    { label: 'Medium',    color: 'var(--warning)' },
  hard:      { label: 'Hard',      color: 'var(--danger)' },
  legendary: { label: 'Legendary', color: 'var(--gold)' },
}

const CATEGORY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  social:      { label: 'Social',     color: '#3E7EFF', bg: 'rgba(62,126,255,0.12)' },
  community:   { label: 'Community',  color: '#30D158', bg: 'rgba(48,209,88,0.12)' },
  development: { label: 'Dev',        color: '#00C8FF', bg: 'rgba(0,200,255,0.12)' },
  creative:    { label: 'Creative',   color: '#BF5AF2', bg: 'rgba(191,90,242,0.12)' },
  special:     { label: 'Special',    color: '#FFD60A', bg: 'rgba(255,214,10,0.12)' },
}

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)

  const [proofLink, setProofLink] = useState('')
  const [proofText, setProofText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [submitted, setSubmitted] = useState(false)

  const { data: task, isLoading } = useQuery({
    queryKey: ['task', id],
    queryFn: () => getTask(Number(id)),
  })

  const mutation = useMutation({
    mutationFn: () =>
      submitTask(Number(id), {
        proof_link: proofLink || undefined,
        proof_text: proofText || undefined,
        file: file || undefined,
      }),
    onSuccess: () => {
      setSubmitted(true)
      qc.invalidateQueries({ queryKey: ['tasks'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  if (isLoading) {
    return (
      <div style={{ padding: '48px 16px', display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="skeleton" style={{ height: 40, width: '60%', borderRadius: 10 }} />
        <div className="skeleton" style={{ height: 120, borderRadius: 16 }} />
        <div className="skeleton" style={{ height: 80, borderRadius: 16 }} />
      </div>
    )
  }

  if (!task) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', padding: '80px 24px', textAlign: 'center',
      }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>😕</div>
        <p style={{ fontSize: 16, color: 'var(--text-muted)', marginBottom: 16 }}>Задание не найдено</p>
        <button onClick={() => navigate(-1)} style={{
          color: 'var(--accent)', fontSize: 14, fontWeight: 500,
          background: 'none', border: 'none', cursor: 'pointer',
        }}>
          ← Назад
        </button>
      </div>
    )
  }

  if (submitted) {
    return (
      <div style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', minHeight: '100dvh', padding: '0 32px',
        textAlign: 'center', gap: 16,
      }}>
        <div style={{
          width: 80, height: 80, borderRadius: 28,
          background: 'rgba(48,209,88,0.12)', border: '1px solid rgba(48,209,88,0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 40, marginBottom: 8,
          animation: 'fadeSlideUp 0.4s ease both',
        }}>
          🎉
        </div>
        <h2 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text)', letterSpacing: -0.5 }}>
          Отправлено!
        </h2>
        {task.requires_moderation ? (
          <p style={{ fontSize: 14, color: 'var(--text-sub)', lineHeight: 1.6 }}>
            Задание отправлено на проверку. Мы уведомим вас о результате через бота.
          </p>
        ) : (
          <div>
            <p style={{ fontSize: 14, color: 'var(--text-sub)', marginBottom: 12 }}>
              Задание выполнено успешно!
            </p>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: 'rgba(255,214,10,0.12)', border: '1px solid rgba(255,214,10,0.2)',
              borderRadius: 14, padding: '8px 18px',
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--gold)">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
              </svg>
              <span style={{ fontSize: 20, fontWeight: 800, color: 'var(--gold)' }}>
                +{task.xp_reward} XP
              </span>
            </div>
          </div>
        )}
        <button
          onClick={() => navigate('/tasks')}
          style={{
            marginTop: 8, padding: '14px 32px', borderRadius: 16,
            background: 'var(--accent)', color: 'white',
            fontSize: 15, fontWeight: 700, border: 'none', cursor: 'pointer',
            boxShadow: '0 8px 20px rgba(62,126,255,0.3)',
          }}
        >
          К заданиям
        </button>
      </div>
    )
  }

  const canSubmit = task.user_status === 'not_started' || task.user_status === 'rejected'
  const cat = CATEGORY_CONFIG[task.category] || CATEGORY_CONFIG.special
  const diff = DIFFICULTY_CONFIG[task.difficulty] || DIFFICULTY_CONFIG.easy

  return (
    <div className="anim-up" style={{ paddingBottom: 32 }}>

      {/* Back button */}
      <div style={{ padding: '20px 16px 0' }}>
        <button
          onClick={() => navigate(-1)}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            color: 'var(--accent)', fontSize: 14, fontWeight: 500,
            background: 'none', border: 'none', cursor: 'pointer', padding: 0,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
          Назад
        </button>
      </div>

      {/* ── Task Header ── */}
      <div style={{ padding: '20px 16px 0' }}>
        {/* Tags */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          <span style={{
            fontSize: 12, fontWeight: 600,
            background: cat.bg, color: cat.color,
            padding: '4px 12px', borderRadius: 99,
          }}>
            {cat.label}
          </span>
          <span style={{
            fontSize: 12, fontWeight: 600,
            background: `${diff.color}15`, color: diff.color,
            padding: '4px 12px', borderRadius: 99,
          }}>
            {diff.label}
          </span>
          {task.is_repeatable && (
            <span style={{
              fontSize: 12, fontWeight: 600,
              background: 'rgba(136,136,170,0.1)', color: 'var(--text-muted)',
              padding: '4px 12px', borderRadius: 99,
            }}>
              Повторяемое
            </span>
          )}
        </div>

        <h1 style={{
          fontSize: 24, fontWeight: 800, color: 'var(--text)',
          letterSpacing: -0.5, marginBottom: 16, lineHeight: 1.2,
        }}>
          {task.title}
        </h1>

        {/* XP reward */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: 'rgba(255,214,10,0.1)', border: '1px solid rgba(255,214,10,0.2)',
          borderRadius: 14, padding: '10px 16px', marginBottom: 20,
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="var(--gold)">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
          <span style={{ fontSize: 18, fontWeight: 800, color: 'var(--gold)' }}>
            +{task.xp_reward} XP
          </span>
        </div>

        {/* Description */}
        <div style={{
          background: 'var(--bg-card)', border: '1px solid var(--border)',
          borderRadius: 16, padding: 16, marginBottom: 8,
        }}>
          <p style={{
            fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
            textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10,
          }}>
            Описание
          </p>
          <p style={{ fontSize: 14, color: 'var(--text-sub)', lineHeight: 1.65 }}>
            {task.description}
          </p>
          {task.link_hint && (
            <a
              href={task.link_hint}
              target="_blank"
              rel="noreferrer"
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                marginTop: 12, color: 'var(--accent)', fontSize: 13,
                textDecoration: 'none',
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
              {task.link_hint}
            </a>
          )}
        </div>
      </div>

      {/* ── Status Banner ── */}
      {!canSubmit && (
        <div style={{ padding: '12px 16px' }}>
          <div style={{
            borderRadius: 14, padding: '14px 16px', textAlign: 'center',
            fontSize: 14, fontWeight: 500,
            background: task.user_status === 'completed'
              ? 'rgba(48,209,88,0.1)' : 'rgba(255,159,10,0.1)',
            color: task.user_status === 'completed' ? 'var(--success)' : 'var(--warning)',
            border: `1px solid ${task.user_status === 'completed' ? 'rgba(48,209,88,0.2)' : 'rgba(255,159,10,0.2)'}`,
          }}>
            {task.user_status === 'completed' ? '✓ Задание выполнено' : '⏳ Задание на проверке'}
          </div>
        </div>
      )}

      {/* ── Submit Form ── */}
      {canSubmit && (
        <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <p style={{
            fontSize: 11, fontWeight: 700, color: 'var(--text-muted)',
            textTransform: 'uppercase', letterSpacing: 1,
          }}>
            Подтверждение выполнения
          </p>

          {/* Link proof */}
          {task.requires_link && (
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 16, padding: 16,
            }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 8 }}>
                Ссылка-доказательство {task.link_hint && `(${task.link_hint})`}
              </label>
              <input
                type="url"
                value={proofLink}
                onChange={(e) => setProofLink(e.target.value)}
                placeholder="https://..."
                className="input-base"
              />
            </div>
          )}

          {/* Text proof */}
          <div style={{
            background: 'var(--bg-card)', border: '1px solid var(--border)',
            borderRadius: 16, padding: 16,
          }}>
            <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 8 }}>
              Комментарий <span style={{ color: 'var(--text-muted)', opacity: 0.5 }}>(опционально)</span>
            </label>
            <textarea
              value={proofText}
              onChange={(e) => setProofText(e.target.value)}
              placeholder="Опишите как вы выполнили задание..."
              rows={3}
              style={{
                background: 'var(--bg-card2)', border: '1px solid var(--border)',
                borderRadius: 12, color: 'var(--text)',
                padding: '12px 14px', width: '100%',
                fontSize: 14, outline: 'none', resize: 'none',
                fontFamily: 'inherit',
              }}
            />
          </div>

          {/* File proof */}
          {(task.requires_photo || task.requires_video) && (
            <div style={{
              background: 'var(--bg-card)', border: '1px solid var(--border)',
              borderRadius: 16, padding: 16,
            }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', display: 'block', marginBottom: 10 }}>
                {task.requires_photo ? 'Фото-доказательство' : 'Видео-доказательство'}
              </label>
              <input
                ref={fileRef}
                type="file"
                accept={task.requires_photo ? 'image/*' : 'video/*'}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                style={{ display: 'none' }}
              />
              <button
                onClick={() => fileRef.current?.click()}
                style={{
                  width: '100%', border: `2px dashed ${file ? 'var(--accent)' : 'var(--border)'}`,
                  borderRadius: 14, padding: '24px 16px',
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
                  background: file ? 'rgba(62,126,255,0.05)' : 'transparent',
                  cursor: 'pointer', transition: 'all 0.2s',
                }}
              >
                {file ? (
                  <>
                    <div style={{
                      width: 40, height: 40, borderRadius: 12,
                      background: 'rgba(48,209,88,0.1)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                        stroke="var(--success)" strokeWidth="2.5" strokeLinecap="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text)' }}>{file.name}</span>
                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {(file.size / 1024 / 1024).toFixed(1)} MB
                    </span>
                  </>
                ) : (
                  <>
                    <div style={{
                      width: 40, height: 40, borderRadius: 12,
                      background: 'var(--bg-card2)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                        stroke="var(--text-muted)" strokeWidth="2" strokeLinecap="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                      </svg>
                    </div>
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                      Нажмите чтобы выбрать файл
                    </span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error */}
          {mutation.isError && (
            <div style={{
              background: 'rgba(255,69,58,0.1)', border: '1px solid rgba(255,69,58,0.2)',
              borderRadius: 12, padding: '12px 14px',
              fontSize: 13, color: 'var(--danger)', textAlign: 'center',
            }}>
              {(mutation.error as any)?.response?.data?.detail || 'Ошибка при отправке'}
            </div>
          )}

          {/* Submit */}
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            style={{
              width: '100%', padding: '16px', borderRadius: 16,
              background: mutation.isPending ? 'rgba(62,126,255,0.4)' : 'var(--accent)',
              color: 'white', fontSize: 16, fontWeight: 700,
              border: 'none', cursor: mutation.isPending ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              boxShadow: mutation.isPending ? 'none' : '0 8px 20px rgba(62,126,255,0.3)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            }}
          >
            {mutation.isPending ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="white" strokeWidth="2" strokeLinecap="round"
                  style={{ animation: 'spin 1s linear infinite' }}>
                  <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
                </svg>
                Отправка...
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="white" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="22" y1="2" x2="11" y2="13"/>
                  <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
                Отправить
              </>
            )}
          </button>
        </div>
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
