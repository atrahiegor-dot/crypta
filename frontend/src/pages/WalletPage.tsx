import { useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useTonConnectUI, useTonWallet } from '@tonconnect/ui-react'
import { getWalletStatus, connectWallet, disconnectWallet } from '../api/endpoints'

function InfoRow({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div style={{
      display: 'flex', gap: 14, alignItems: 'flex-start',
      padding: '14px 0',
      borderBottom: '1px solid var(--border)',
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 10, flexShrink: 0,
        background: 'var(--bg-card2)', border: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: 'var(--text-sub)',
      }}>
        {icon}
      </div>
      <div>
        <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginBottom: 3 }}>{title}</p>
        <p style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.5 }}>{desc}</p>
      </div>
    </div>
  )
}

export default function WalletPage() {
  const qc = useQueryClient()
  const [tonConnectUI] = useTonConnectUI()
  const tonWallet = useTonWallet()

  const { data: walletStatus } = useQuery({
    queryKey: ['wallet'],
    queryFn: getWalletStatus,
    staleTime: 30_000,
  })

  const connectMutation = useMutation({
    mutationFn: (address: string) => connectWallet(address),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wallet'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  const disconnectMutation = useMutation({
    mutationFn: disconnectWallet,
    onSuccess: () => {
      tonConnectUI.disconnect()
      qc.invalidateQueries({ queryKey: ['wallet'] })
      qc.invalidateQueries({ queryKey: ['profile'] })
    },
  })

  useEffect(() => {
    if (tonWallet?.account?.address) {
      const addr = tonWallet.account.address
      if (!walletStatus?.connected || walletStatus.address !== addr) {
        connectMutation.mutate(addr)
      }
    }
  }, [tonWallet?.account?.address])

  const address = walletStatus?.address || tonWallet?.account?.address
  const connected = walletStatus?.connected || !!tonWallet

  return (
    <div className="anim-up" style={{ padding: '24px 16px' }}>

      {/* ── Page Title ── */}
      <h1 style={{
        fontSize: 22, fontWeight: 800, color: 'var(--text)',
        letterSpacing: -0.5, marginBottom: 24,
      }}>
        TON Кошелёк
      </h1>

      {/* ── Connection Card ── */}
      <div style={{
        borderRadius: 24, overflow: 'hidden',
        border: `1px solid ${connected ? 'rgba(0,200,255,0.25)' : 'var(--border)'}`,
        marginBottom: 16,
        background: connected
          ? 'linear-gradient(135deg,rgba(0,200,255,0.08),rgba(62,126,255,0.08))'
          : 'var(--bg-card)',
      }}>
        <div style={{ padding: '28px 24px', textAlign: 'center' }}>

          {/* Icon */}
          <div style={{
            width: 72, height: 72, borderRadius: 22,
            background: connected
              ? 'linear-gradient(135deg,rgba(0,200,255,0.2),rgba(62,126,255,0.2))'
              : 'var(--bg-card2)',
            border: `1px solid ${connected ? 'rgba(0,200,255,0.3)' : 'var(--border)'}`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            margin: '0 auto 20px',
            fontSize: 32,
          }}>
            💎
          </div>

          {connected && address ? (
            <>
              {/* Connected state */}
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                background: 'rgba(48,209,88,0.1)', border: '1px solid rgba(48,209,88,0.2)',
                borderRadius: 99, padding: '4px 12px', marginBottom: 14,
              }}>
                <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'var(--success)' }} />
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--success)' }}>Подключён</span>
              </div>

              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>
                Подключённый адрес
              </p>
              <div style={{
                background: 'var(--bg-card2)', border: '1px solid var(--border)',
                borderRadius: 12, padding: '10px 14px',
                fontFamily: 'monospace', fontSize: 13, color: 'var(--text)',
                letterSpacing: 0.5,
              }}>
                {address.slice(0, 12)}...{address.slice(-8)}
              </div>

              {walletStatus?.connected_at && (
                <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 10 }}>
                  Подключён {new Date(walletStatus.connected_at).toLocaleDateString('ru-RU')}
                </p>
              )}
            </>
          ) : (
            <>
              <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text)', marginBottom: 10 }}>
                Подключи кошелёк
              </h2>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                background: 'rgba(255,214,10,0.1)', border: '1px solid rgba(255,214,10,0.2)',
                borderRadius: 10, padding: '6px 14px',
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="var(--gold)">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--gold)' }}>
                  +500 XP за подключение
                </span>
              </div>
            </>
          )}
        </div>

        {/* Success banner */}
        {connectMutation.isSuccess && (
          <div style={{
            background: 'rgba(48,209,88,0.1)',
            borderTop: '1px solid rgba(48,209,88,0.2)',
            padding: '12px 20px',
            display: 'flex', alignItems: 'center', gap: 10,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="var(--success)" strokeWidth="2.5" strokeLinecap="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            <div>
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--success)' }}>
                Кошелёк подключён!
              </p>
              <p style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                +500 XP начислено на ваш счёт
              </p>
            </div>
          </div>
        )}
      </div>

      {/* ── Action button ── */}
      {connected ? (
        <button
          onClick={() => disconnectMutation.mutate()}
          disabled={disconnectMutation.isPending}
          style={{
            width: '100%', padding: '15px', borderRadius: 16,
            background: 'transparent',
            border: '2px solid rgba(255,69,58,0.4)',
            color: 'var(--danger)', fontSize: 15, fontWeight: 700,
            cursor: disconnectMutation.isPending ? 'not-allowed' : 'pointer',
            opacity: disconnectMutation.isPending ? 0.6 : 1,
            marginBottom: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>
            <line x1="12" y1="2" x2="12" y2="12"/>
          </svg>
          {disconnectMutation.isPending ? 'Отключение...' : 'Отключить кошелёк'}
        </button>
      ) : (
        <button
          onClick={() => tonConnectUI.openModal()}
          style={{
            width: '100%', padding: '16px', borderRadius: 16,
            background: 'linear-gradient(135deg,#3E7EFF,#00C8FF)',
            color: 'white', fontSize: 16, fontWeight: 700,
            border: 'none', cursor: 'pointer', marginBottom: 20,
            boxShadow: '0 8px 24px rgba(62,126,255,0.35)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="white" strokeWidth="2.5" strokeLinecap="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
          </svg>
          Подключить кошелёк
        </button>
      )}

      {/* ── Info section ── */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 20, padding: '4px 16px', overflow: 'hidden',
      }}>
        <InfoRow
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <rect x="3" y="11" width="18" height="11" rx="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
          }
          title="Безопасно"
          desc="Мы храним только публичный адрес. Seed phrase нам не нужен."
        />
        <InfoRow
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="var(--gold)">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
          }
          title="+500 XP бонус"
          desc="Получите XP бонус за первое подключение кошелька."
        />
        <div style={{ borderBottom: 'none' }}>
          <InfoRow
            icon={
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <rect x="2" y="6" width="20" height="14" rx="3"/>
                <path d="M2 10h20"/><circle cx="16" cy="16" r="1" fill="currentColor" stroke="none"/>
              </svg>
            }
            title="Популярные кошельки"
            desc="Tonkeeper, MyTonWallet и другие TON кошельки."
          />
        </div>
      </div>
    </div>
  )
}
