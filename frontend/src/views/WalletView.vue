<template>
  <div class="wallet-view">
    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="wallet && child" class="wallet-container">
      <!-- 头部 -->
      <header class="wallet-header">
        <button class="btn-back" @click="goBack">←</button>
        <h1 class="page-title">小小钱包 👛</h1>
        <div class="child-info">
          <div class="avatar-small">
            <img v-if="child.avatar" :src="child.avatar" :alt="child.name" />
            <span v-else class="avatar-placeholder">{{ genderEmoji }}</span>
          </div>
          <span class="child-name">{{ child.name }}</span>
        </div>
      </header>

      <!-- Tab切换 -->
      <div class="tabs card">
        <button 
          :class="['tab', { active: activeTab === 'savings' }]"
          @click="activeTab = 'savings'"
        >
          <span class="tab-icon">👛</span>
          <span class="tab-label">存钱罐</span>
        </button>
        <button 
          :class="['tab', { active: activeTab === 'pocket' }]"
          @click="activeTab = 'pocket'"
        >
          <span class="tab-icon">💰</span>
          <span class="tab-label">零花钱</span>
        </button>
      </div>

      <!-- 存钱罐Tab内容 -->
      <div v-show="activeTab === 'savings'" class="tab-content">
        <!-- 余额卡片 -->
        <div class="balance-card card">
          <div class="balance-header">
            <span class="balance-label">余额</span>
          </div>
          <div class="balance-amount">{{ formatAmount(wallet.savings_box.balance) }}</div>
          
          <!-- 收益信息 -->
          <div class="info-grid">
            <div class="info-item highlight-item">
              <span class="info-icon">✨</span>
              <div class="info-content">
                <span class="info-label">今日收益</span>
                <span class="info-value highlight">{{ formatAmount(wallet.savings_box.today_interest) }}</span>
              </div>
            </div>
            <div class="info-item">
              <span class="info-icon">💎</span>
              <div class="info-content">
                <span class="info-label">累计利息</span>
                <span class="info-value">{{ formatAmount(wallet.savings_box.total_interest) }}</span>
              </div>
            </div>
            <div class="info-item">
              <span class="info-icon">📈</span>
              <div class="info-content">
                <span class="info-label">年化利率</span>
                <span class="info-value">{{ (Number(wallet.savings_box.interest_rate) * 100).toFixed(2) }}%</span>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <button @click="handleDeposit('savings')" class="btn-action btn-deposit">
              <span class="btn-icon">💵</span>
              <span>存入</span>
            </button>
            <button @click="handleWithdraw('savings')" class="btn-action btn-withdraw">
              <span class="btn-icon">💸</span>
              <span>取出</span>
            </button>
            <button @click="showCalculator = true" class="btn-action btn-calculator">
              <span class="btn-icon">🧮</span>
              <span>收益计算器</span>
            </button>
          </div>
        </div>

        <!-- 交易记录 -->
        <div class="transactions-section card">
          <h3 class="section-title">📋 交易记录</h3>
          <div v-if="savingsTransactions.length === 0" class="empty-state">
            <p>暂无交易记录</p>
          </div>
          <div v-else class="transaction-list">
            <div 
              v-for="transaction in savingsTransactions"
              :key="transaction.id"
              :class="['transaction-item', getTransactionClass(transaction.transaction_type)]"
            >
              <div class="transaction-left">
                <div class="transaction-type">
                  {{ getTransactionTypeLabel(transaction.transaction_type) }}
                </div>
                <div class="transaction-time">
                  {{ formatDateTime(transaction.created_at) }}
                </div>
              </div>
              <div class="transaction-right">
                <div class="transaction-amount" :class="getTransactionClass(transaction.transaction_type)">
                  {{ getTransactionSign(transaction.transaction_type) }}{{ formatAmount(transaction.amount) }}
                </div>
                <div v-if="transaction.remark" class="transaction-remark">
                  {{ transaction.remark }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 零花钱Tab内容 -->
      <div v-show="activeTab === 'pocket'" class="tab-content">
        <!-- 余额卡片 -->
        <div class="balance-card card">
          <div class="balance-header">
            <span class="balance-label">余额</span>
          </div>
          <div class="balance-amount">{{ formatAmount(wallet.pocket_money.balance) }}</div>

          <!-- 操作按钮 -->
          <div class="action-buttons">
            <button @click="handleDeposit('pocket')" class="btn-action btn-deposit">
              <span class="btn-icon">💵</span>
              <span>存入</span>
            </button>
            <button @click="handleWithdraw('pocket')" class="btn-action btn-withdraw">
              <span class="btn-icon">💸</span>
              <span>取出</span>
            </button>
          </div>
        </div>

        <!-- 交易记录 -->
        <div class="transactions-section card">
          <h3 class="section-title">📋 交易记录</h3>
          <div v-if="pocketTransactions.length === 0" class="empty-state">
            <p>暂无交易记录</p>
          </div>
          <div v-else class="transaction-list">
            <div 
              v-for="transaction in pocketTransactions"
              :key="transaction.id"
              :class="['transaction-item', getTransactionClass(transaction.transaction_type)]"
            >
              <div class="transaction-left">
                <div class="transaction-type">
                  {{ getTransactionTypeLabel(transaction.transaction_type) }}
                </div>
                <div class="transaction-time">
                  {{ formatDateTime(transaction.created_at) }}
                </div>
              </div>
              <div class="transaction-right">
                <div class="transaction-amount" :class="getTransactionClass(transaction.transaction_type)">
                  {{ getTransactionSign(transaction.transaction_type) }}{{ formatAmount(transaction.amount) }}
                </div>
                <div v-if="transaction.remark" class="transaction-remark">
                  {{ transaction.remark }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-state">
      <p>数据加载失败</p>
      <button @click="loadData" class="btn-retry">重试</button>
    </div>

    <!-- 交易表单对话框 -->
    <WalletTransactionModal
      v-model:show="showTransactionModal"
      :wallet-type="transactionWalletType"
      :transaction-type="transactionType"
      :child-id="childId"
      :current-balance="currentBalance"
      @success="handleTransactionSuccess"
    />

    <!-- 收益计算器对话框 -->
    <EarningsCalculatorModal
      :show="showCalculator"
      :default-rate="wallet?.savings_box?.interest_rate ? Number(wallet.savings_box.interest_rate) * 100 : 5.0"
      @close="showCalculator = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { walletApi } from '@/api/wallet'
import { childrenApi } from '@/api/children'
import type { WalletOverview, Child, WalletTransaction, TransactionType } from '@/types'
import { getGenderEmoji } from '@/utils/helpers'
import WalletTransactionModal from '@/components/WalletTransactionModal.vue'
import EarningsCalculatorModal from '@/components/EarningsCalculatorModal.vue'

const route = useRoute()
const router = useRouter()

// 响应式状态
const child = ref<Child | null>(null)
const wallet = ref<WalletOverview | null>(null)
const loading = ref(false)
const activeTab = ref<'savings' | 'pocket'>('savings')

// 交易表单状态
const showTransactionModal = ref(false)
const transactionWalletType = ref<'savings' | 'pocket'>('savings')
const transactionType = ref<'deposit' | 'withdraw'>('deposit')

// 收益计算器状态
const showCalculator = ref(false)

// 计算属性
const childId = computed(() => Number(route.params.id))

const genderEmoji = computed(() => 
  child.value ? getGenderEmoji(child.value.gender) : ''
)

// 过滤交易记录
const savingsTransactions = computed(() => {
  if (!wallet.value) return []
  return wallet.value.recent_transactions
    .filter(t => t.wallet_type === 'savings_box')
    .slice(0, 10)
})

const pocketTransactions = computed(() => {
  if (!wallet.value) return []
  return wallet.value.recent_transactions
    .filter(t => t.wallet_type === 'pocket_money')
    .slice(0, 10)
})

// 获取当前余额（用于表单验证）
const currentBalance = computed(() => {
  if (!wallet.value) return '0'
  return transactionWalletType.value === 'savings'
    ? wallet.value.savings_box.balance
    : wallet.value.pocket_money.balance
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    // 并行加载孩子信息和钱包数据
    const [childData, walletData] = await Promise.all([
      childrenApi.getById(childId.value),
      walletApi.getOverview(childId.value)
    ])
    child.value = childData
    wallet.value = walletData
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 格式化金额显示
const formatAmount = (amount: string): string => {
  return `¥${parseFloat(amount).toFixed(2)}`
}

// 格式化日期时间
const formatDateTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else if (days === 1) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  } else if (days < 7) {
    return `${days}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    })
  }
}

// 获取交易类型标签
const getTransactionTypeLabel = (type: TransactionType): string => {
  const labels: Record<string, string> = {
    deposit: '存入',
    withdraw: '取出',
    interest: '利息',
    transfer_in: '转入',
    transfer_out: '转出'
  }
  return labels[type] || type
}

// 获取交易类型样式类
const getTransactionClass = (type: TransactionType): string => {
  const classes: Record<string, string> = {
    deposit: 'type-deposit',
    withdraw: 'type-withdraw',
    interest: 'type-interest',
    transfer_in: 'type-deposit',
    transfer_out: 'type-withdraw'
  }
  return classes[type] || ''
}

// 获取交易符号
const getTransactionSign = (type: TransactionType): string => {
  return ['deposit', 'interest', 'transfer_in'].includes(type) ? '+' : '-'
}

// 返回上一页
const goBack = () => {
  router.back()
}

// 打开交易表单
const openTransactionModal = (walletType: 'savings' | 'pocket', type: 'deposit' | 'withdraw') => {
  transactionWalletType.value = walletType
  transactionType.value = type
  showTransactionModal.value = true
}

// 处理存入操作
const handleDeposit = (walletType: 'savings' | 'pocket') => {
  openTransactionModal(walletType, 'deposit')
}

// 处理取出操作
const handleWithdraw = (walletType: 'savings' | 'pocket') => {
  openTransactionModal(walletType, 'withdraw')
}

// 交易成功后刷新数据
const handleTransactionSuccess = async () => {
  await loadData()
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.wallet-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.loading,
.error-state {
  text-align: center;
  padding: 60px 20px;
  font-size: 20px;
  color: #999;
}

.btn-retry {
  margin-top: 20px;
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-retry:hover {
  transform: scale(1.05);
}

.wallet-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.wallet-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 10px;
}

.btn-back {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: none;
  background: white;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.btn-back:hover {
  transform: scale(1.1);
}

.page-title {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  margin: 0;
  flex: 1;
}

.child-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar-small {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #667eea;
}

.avatar-small img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-size: 20px;
}

.child-name {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.tabs {
  display: flex;
  padding: 8px;
  gap: 8px;
}

.tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border: none;
  background: transparent;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.tab:hover {
  background: #f5f5f5;
}

.tab.active {
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  color: white;
}

.tab-icon {
  font-size: 24px;
}

.tab-label {
  font-size: 16px;
}

.balance-card {
  padding: 30px;
}

.balance-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.balance-label {
  font-size: 14px;
  color: #999;
  font-weight: 500;
}

.balance-amount {
  font-size: 48px;
  font-weight: bold;
  background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 24px;
  line-height: 1.2;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 24px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 12px;
  transition: transform 0.2s;
}

.info-item:hover {
  transform: translateY(-2px);
}

.highlight-item {
  background: linear-gradient(135deg, #fff5e1 0%, #ffe4b5 100%);
}

.info-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.info-label {
  font-size: 12px;
  color: #999;
  font-weight: 500;
}

.info-value {
  font-size: 18px;
  font-weight: 700;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.info-value.highlight {
  color: #FF8C00;
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.btn-action {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.btn-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.btn-action:active {
  transform: translateY(0);
}

.btn-deposit {
  background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
  color: white;
}

.btn-withdraw {
  background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
  color: #333;
}

.btn-calculator {
  background: linear-gradient(135deg, #a29bfe 0%, #6c5ce7 100%);
  color: white;
}

.btn-icon {
  font-size: 20px;
}

.transactions-section {
  padding: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: bold;
  margin: 0 0 20px 0;
  color: #333;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
  font-size: 14px;
}

.transaction-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 12px;
  border-left: 4px solid #ccc;
  transition: transform 0.2s;
}

.transaction-item:hover {
  transform: translateX(4px);
}

.transaction-item.type-deposit {
  border-left-color: #84fab0;
  background: linear-gradient(135deg, #f0fff4 0%, #f9f9f9 100%);
}

.transaction-item.type-withdraw {
  border-left-color: #fdcb6e;
  background: linear-gradient(135deg, #fffbf0 0%, #f9f9f9 100%);
}

.transaction-item.type-interest {
  border-left-color: #FF8C00;
  background: linear-gradient(135deg, #fff5e1 0%, #f9f9f9 100%);
}

.transaction-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.transaction-type {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.transaction-time {
  font-size: 12px;
  color: #999;
}

.transaction-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.transaction-amount {
  font-size: 20px;
  font-weight: bold;
}

.transaction-amount.type-deposit {
  color: #4CAF50;
}

.transaction-amount.type-withdraw {
  color: #FF9800;
}

.transaction-amount.type-interest {
  color: #FF8C00;
}

.transaction-remark {
  font-size: 13px;
  color: #666;
  max-width: 200px;
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 768px) {
  .wallet-view {
    padding: 15px;
  }

  .page-title {
    font-size: 24px;
  }

  .balance-amount {
    font-size: 36px;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    grid-template-columns: 1fr;
  }

  .transaction-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .transaction-right {
    align-items: flex-start;
    width: 100%;
  }

  .transaction-remark {
    text-align: left;
    max-width: 100%;
  }
}
</style>