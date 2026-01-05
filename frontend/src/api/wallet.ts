import api from './index'
import type { 
  WalletOverview, 
  SavingsBox, 
  PocketMoney, 
  WalletTransaction, 
  TransactionForm,
  ApiResponse 
} from '@/types'

export const walletApi = {
  // ==================== 钱包总览 ====================
  
  /**
   * 获取钱包总览
   * @param childId 孩子ID
   * @returns 钱包总览信息(包括存钱罐、零花钱和最近交易记录)
   */
  getOverview: async (childId: number): Promise<WalletOverview> => {
    const response = await api.get<ApiResponse<WalletOverview>>(`/wallet/${childId}/overview`)
    if (!response.data.data) {
      throw new Error('Failed to get wallet overview')
    }
    return response.data.data
  },

  // ==================== 存钱罐 ====================

  /**
   * 存钱罐 - 存入
   * @param childId 孩子ID
   * @param data 交易表单(金额和备注)
   * @returns 更新后的存钱罐信息
   */
  depositToSavingsBox: async (childId: number, data: TransactionForm): Promise<SavingsBox> => {
    const response = await api.post<ApiResponse<SavingsBox>>(
      `/wallet/${childId}/savings-box/deposit`,
      data
    )
    if (!response.data.data) {
      throw new Error('Failed to deposit to savings box')
    }
    return response.data.data
  },

  /**
   * 存钱罐 - 取出
   * @param childId 孩子ID
   * @param data 交易表单(金额和备注)
   * @returns 更新后的存钱罐信息
   */
  withdrawFromSavingsBox: async (childId: number, data: TransactionForm): Promise<SavingsBox> => {
    const response = await api.post<ApiResponse<SavingsBox>>(
      `/wallet/${childId}/savings-box/withdraw`,
      data
    )
    if (!response.data.data) {
      throw new Error('Failed to withdraw from savings box')
    }
    return response.data.data
  },

  /**
   * 获取存钱罐余额
   * @param childId 孩子ID
   * @returns 存钱罐信息
   */
  getSavingsBoxBalance: async (childId: number): Promise<SavingsBox> => {
    const response = await api.get<ApiResponse<SavingsBox>>(`/wallet/${childId}/savings-box`)
    if (!response.data.data) {
      throw new Error('Failed to get savings box balance')
    }
    return response.data.data
  },

  /**
   * 获取存钱罐交易记录
   * @param childId 孩子ID
   * @param limit 返回记录数量限制(可选)
   * @returns 交易记录列表
   */
  getSavingsBoxTransactions: async (childId: number, limit?: number): Promise<WalletTransaction[]> => {
    const params = limit ? { limit } : {}
    const response = await api.get<ApiResponse<WalletTransaction[]>>(
      `/wallet/${childId}/savings-box/transactions`,
      { params }
    )
    return response.data.data || []
  },

  // ==================== 零花钱 ====================

  /**
   * 零花钱 - 存入
   * @param childId 孩子ID
   * @param data 交易表单(金额和备注)
   * @returns 更新后的零花钱信息
   */
  depositToPocketMoney: async (childId: number, data: TransactionForm): Promise<PocketMoney> => {
    const response = await api.post<ApiResponse<PocketMoney>>(
      `/wallet/${childId}/pocket-money/deposit`,
      data
    )
    if (!response.data.data) {
      throw new Error('Failed to deposit to pocket money')
    }
    return response.data.data
  },

  /**
   * 零花钱 - 取出
   * @param childId 孩子ID
   * @param data 交易表单(金额和备注)
   * @returns 更新后的零花钱信息
   */
  withdrawFromPocketMoney: async (childId: number, data: TransactionForm): Promise<PocketMoney> => {
    const response = await api.post<ApiResponse<PocketMoney>>(
      `/wallet/${childId}/pocket-money/withdraw`,
      data
    )
    if (!response.data.data) {
      throw new Error('Failed to withdraw from pocket money')
    }
    return response.data.data
  },

  /**
   * 获取零花钱余额
   * @param childId 孩子ID
   * @returns 零花钱信息
   */
  getPocketMoneyBalance: async (childId: number): Promise<PocketMoney> => {
    const response = await api.get<ApiResponse<PocketMoney>>(`/wallet/${childId}/pocket-money`)
    if (!response.data.data) {
      throw new Error('Failed to get pocket money balance')
    }
    return response.data.data
  },

  /**
   * 获取零花钱交易记录
   * @param childId 孩子ID
   * @param limit 返回记录数量限制(可选)
   * @returns 交易记录列表
   */
  getPocketMoneyTransactions: async (childId: number, limit?: number): Promise<WalletTransaction[]> => {
    const params = limit ? { limit } : {}
    const response = await api.get<ApiResponse<WalletTransaction[]>>(
      `/wallet/${childId}/pocket-money/transactions`,
      { params }
    )
    return response.data.data || []
  },
}