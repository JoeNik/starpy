// Child types
export interface Child {
  id: number
  name: string
  birthday: string
  age: number
  gender: 'male' | 'female'
  avatar: string | null
  star_count: number
  star_records?: StarRecord[]
  rewards?: Reward[]
}

// Star record types
export interface StarRecord {
  id: number
  amount: number
  type: 'add' | 'subtract' | 'redeem'
  reason?: string
  reward?: {
    id: number
    name: string
    image: string | null
  } | null
  created_at: string
}

// Reward types
export interface Reward {
  id: number
  name: string
  image: string | null
  star_cost: number
  is_redeemed: boolean
  redeemed_at?: string
  children?: ChildInReward[]
  total_stars?: number
  is_achieved?: boolean
}

export interface ChildInReward {
  id: number
  name: string
  star_count: number
  gender: 'male' | 'female'
  avatar: string | null
}

// API Response types
export interface ApiResponse<T> {
  success: boolean
  data?: T
  message?: string
  errors?: Record<string, string[]>
}

// Star operation request
export interface StarOperationRequest {
  amount: number
  reason?: string
}

// Reward creation request
export interface RewardCreateRequest {
  name: string
  star_cost: number
  child_ids: number[]
  image?: File
}

// Reward redemption request
export interface RewardRedeemRequest {
  deductions: Array<{
    child_id: number
    amount: number
  }>
}

// Reward update request
export interface RewardUpdateRequest {
  name?: string
  star_cost?: number
  child_ids?: number[]
  image?: File
}

// Child form data
export interface ChildFormData {
  name: string
  birthday: string
  gender: 'male' | 'female'
  avatar?: File
}

// 钱包类型
export const WalletType = {
  SAVINGS_BOX: 'savings_box',
  POCKET_MONEY: 'pocket_money'
} as const

export type WalletType = typeof WalletType[keyof typeof WalletType]

// 交易类型
export const TransactionType = {
  DEPOSIT: 'deposit',          // 存入
  WITHDRAW: 'withdraw',        // 取出
  INTEREST: 'interest',        // 利息
  TRANSFER_IN: 'transfer_in',  // 转入
  TRANSFER_OUT: 'transfer_out' // 转出
} as const

export type TransactionType = typeof TransactionType[keyof typeof TransactionType]

// 存钱罐
export interface SavingsBox {
  id: number
  child_id: number
  balance: string           // 使用字符串表示Decimal类型
  total_interest: string    // 累计利息
  last_interest_date: string | null  // 最后计息日期
  interest_rate: string     // 年化利率
  today_interest: string    // 今日待结算利息(计算字段)
  created_at: string
  updated_at: string
}

// 零花钱
export interface PocketMoney {
  id: number
  child_id: number
  balance: string           // 使用字符串表示Decimal类型
  created_at: string
  updated_at: string
}

// 交易记录
export interface WalletTransaction {
  id: number
  child_id: number
  wallet_type: WalletType
  transaction_type: TransactionType
  amount: string            // 使用字符串表示Decimal类型
  balance_after: string     // 交易后余额
  remark: string | null     // 备注
  created_at: string
}

// 钱包总览
export interface WalletOverview {
  savings_box: SavingsBox
  pocket_money: PocketMoney
  recent_transactions: WalletTransaction[]
}

// 交易表单(用于存款/取款)
export interface TransactionForm {
  amount: number
  remark?: string
}
