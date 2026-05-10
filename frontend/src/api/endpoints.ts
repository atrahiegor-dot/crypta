import api from './client'
import type { LeaderboardEntry, Submission, Task, UserProfile, WalletStatus } from '../types'

// ─── Profile ──────────────────────────────────────────────────────────────────

export const getProfile = () =>
  api.get<UserProfile>('/profile/me').then((r) => r.data)

export const getSubmissions = (limit = 20, offset = 0) =>
  api.get<Submission[]>('/profile/submissions', { params: { limit, offset } }).then((r) => r.data)

// ─── Tasks ────────────────────────────────────────────────────────────────────

export const getTasks = (category?: string) =>
  api.get<Task[]>('/tasks', { params: category ? { category } : {} }).then((r) => r.data)

export const getTask = (id: number) =>
  api.get<Task>(`/tasks/${id}`).then((r) => r.data)

export const submitTask = (
  taskId: number,
  data: { proof_link?: string; proof_text?: string; file?: File },
) => {
  const form = new FormData()
  if (data.proof_link) form.append('proof_link', data.proof_link)
  if (data.proof_text) form.append('proof_text', data.proof_text)
  if (data.file) form.append('file', data.file)
  return api.post<{ message: string; xp_awarded?: number }>(`/tasks/${taskId}/submit`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data)
}

// ─── Leaderboard ──────────────────────────────────────────────────────────────

export const getLeaderboard = (period: 'all' | 'weekly' | 'monthly' = 'all', limit = 50) =>
  api.get<LeaderboardEntry[]>('/leaderboard', { params: { period, limit } }).then((r) => r.data)

// ─── Wallet ───────────────────────────────────────────────────────────────────

export const getWalletStatus = () =>
  api.get<WalletStatus>('/wallet/status').then((r) => r.data)

export const connectWallet = (wallet_address: string) =>
  api.post('/wallet/connect', { wallet_address }).then((r) => r.data)

export const disconnectWallet = () =>
  api.delete('/wallet/disconnect').then((r) => r.data)
