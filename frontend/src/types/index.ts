export interface Achievement {
  type: string
  earned_at: string
}

export interface UserProfile {
  id: number
  telegram_id: number
  username: string | null
  first_name: string
  last_name: string | null
  display_name: string
  xp_points: number
  level: number
  wallet_address: string | null
  wallet_connected: boolean
  daily_streak: number
  referral_code: string
  role: string
  achievements: Achievement[]
  tasks_completed: number
  referrals_count: number
  rank: number
}

export type TaskStatus = 'not_started' | 'pending' | 'completed' | 'rejected'
export type TaskCategory = 'social' | 'community' | 'development' | 'creative' | 'special'
export type TaskDifficulty = 'easy' | 'medium' | 'hard' | 'legendary'

export interface Task {
  id: number
  title: string
  description: string
  category: TaskCategory
  difficulty: TaskDifficulty
  xp_reward: number
  requires_photo: boolean
  requires_video: boolean
  requires_link: boolean
  link_hint: string | null
  is_repeatable: boolean
  requires_moderation: boolean
  completions_count: number
  max_completions: number | null
  user_status: TaskStatus
}

export interface Submission {
  id: number
  task_id: number
  task_title: string | null
  status: string
  submitted_at: string
  reviewed_at: string | null
  xp_awarded: number
  review_comment: string | null
  proof_link: string | null
  proof_file_url: string | null
}

export interface LeaderboardEntry {
  rank: number
  user_id: number
  username: string | null
  first_name: string
  display_name: string
  xp_points: number
  level: number
  is_current_user: boolean
}

export interface WalletStatus {
  connected: boolean
  address: string | null
  connected_at: string | null
}
