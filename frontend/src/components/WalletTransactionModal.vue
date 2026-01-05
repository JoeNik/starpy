<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click="handleClose">
        <Transition name="slide-up">
          <div
            v-if="show"
            class="modal-content"
            :style="{ '--theme-color': themeColor }"
            @click.stop
          >
            <button class="btn-close" @click="handleClose">×</button>

            <!-- 头部 -->
            <div class="modal-header">
              <div class="title-row">
                <span class="icon">{{ icon }}</span>
                <h2 class="title">{{ title }}</h2>
              </div>
            </div>

            <!-- 余额信息 -->
            <div class="balance-info">
              <span class="label">当前余额</span>
              <span class="balance">¥{{ balanceFloat.toFixed(2) }}</span>
            </div>

            <!-- 表单内容 -->
            <form @submit.prevent="handleSubmit" class="modal-body">
              <!-- 金额输入 -->
              <div class="form-group">
                <label class="form-label required">金额</label>
                <div class="input-wrapper">
                  <span class="currency">¥</span>
                  <input
                    v-model.number="form.amount"
                    type="number"
                    step="0.01"
                    min="0.01"
                    class="form-input amount-input"
                    placeholder="请输入金额"
                    required
                  />
                </div>
              </div>

              <!-- 备注输入 -->
              <div class="form-group">
                <label class="form-label">备注</label>
                <textarea
                  v-model="form.remark"
                  class="form-textarea"
                  placeholder="添加备注（可选）"
                  rows="3"
                  maxlength="200"
                ></textarea>
              </div>

              <!-- 错误提示 -->
              <div v-if="error" class="error-message">{{ error }}</div>

              <!-- 按钮组 -->
              <div class="button-group">
                <button type="button" @click="handleClose" class="btn btn-secondary" :disabled="loading">
                  取消
                </button>
                <button type="submit" class="btn btn-primary" :disabled="loading">
                  {{ loading ? '处理中...' : '确认' }}
                </button>
              </div>
            </form>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { walletApi } from '@/api/wallet'
import type { TransactionForm } from '@/types'

// Props定义
interface Props {
  show: boolean
  walletType: 'savings' | 'pocket'
  transactionType: 'deposit' | 'withdraw'
  childId: number
  currentBalance: string
}

const props = defineProps<Props>()

// Emits定义
const emit = defineEmits<{
  'update:show': [value: boolean]
  'success': []
}>()

// 响应式状态
const form = ref<TransactionForm>({
  amount: 0,
  remark: ''
})
const loading = ref(false)
const error = ref('')

// 计算属性
const title = computed(() => {
  const walletName = props.walletType === 'savings' ? '存钱罐' : '零花钱'
  const actionName = props.transactionType === 'deposit' ? '存入' : '取出'
  return `${walletName} - ${actionName}`
})

const icon = computed(() => {
  return props.walletType === 'savings' ? '🐷' : '💰'
})

const themeColor = computed(() => {
  return props.transactionType === 'deposit' ? '#4CAF50' : '#FF9800'
})

const balanceFloat = computed(() => parseFloat(props.currentBalance))

// 表单验证
const validateForm = (): boolean => {
  error.value = ''
  
  if (!form.value.amount || form.value.amount <= 0) {
    error.value = '请输入有效的金额'
    return false
  }
  
  if (props.transactionType === 'withdraw' && form.value.amount > balanceFloat.value) {
    error.value = `取出金额不能超过当前余额 ¥${balanceFloat.value.toFixed(2)}`
    return false
  }
  
  return true
}

// 提交表单
const handleSubmit = async () => {
  if (!validateForm()) return
  
  loading.value = true
  error.value = ''
  
  try {
    // 根据钱包类型和交易类型调用对应的API
    if (props.walletType === 'savings') {
      if (props.transactionType === 'deposit') {
        await walletApi.depositToSavingsBox(props.childId, form.value)
      } else {
        await walletApi.withdrawFromSavingsBox(props.childId, form.value)
      }
    } else {
      if (props.transactionType === 'deposit') {
        await walletApi.depositToPocketMoney(props.childId, form.value)
      } else {
        await walletApi.withdrawFromPocketMoney(props.childId, form.value)
      }
    }
    
    // 成功后关闭对话框并触发success事件
    handleClose()
    emit('success')
  } catch (err: any) {
    error.value = err.response?.data?.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}

// 关闭对话框
const handleClose = () => {
  emit('update:show', false)
  // 重置表单
  setTimeout(() => {
    form.value = { amount: 0, remark: '' }
    error.value = ''
  }, 300)
}

// 监听ESC键
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.show) {
    handleClose()
  }
}

// 生命周期
watch(() => props.show, (newVal) => {
  if (newVal) {
    document.addEventListener('keydown', handleKeydown)
  } else {
    document.removeEventListener('keydown', handleKeydown)
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 24px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  position: relative;
}

.btn-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: #f5f5f5;
  font-size: 28px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  z-index: 1;
}

.btn-close:hover {
  background: #e0e0e0;
}

.modal-header {
  padding: 32px 20px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.icon {
  font-size: 32px;
}

.title {
  font-size: 24px;
  font-weight: bold;
  margin: 0;
  color: #333;
}

.balance-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #f9f9f9;
  border-bottom: 1px solid #e0e0e0;
}

.balance-info .label {
  font-size: 14px;
  color: #666;
}

.balance-info .balance {
  font-size: 20px;
  font-weight: bold;
  color: var(--theme-color);
}

.modal-body {
  padding: 24px 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #333;
}

.form-label.required::after {
  content: ' *';
  color: #ff4444;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.currency {
  position: absolute;
  left: 12px;
  font-size: 18px;
  font-weight: bold;
  color: var(--theme-color);
}

.form-input {
  width: 100%;
  padding: 12px 12px 12px 32px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.amount-input {
  font-size: 20px;
  font-weight: 600;
}

.form-input:focus {
  outline: none;
  border-color: var(--theme-color);
}

.form-textarea {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.3s;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--theme-color);
}

.error-message {
  padding: 12px;
  background: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 12px;
  color: #c62828;
  font-size: 14px;
  margin-bottom: 20px;
}

.button-group {
  display: flex;
  gap: 12px;
}

.btn {
  flex: 1;
  padding: 14px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover:not(:disabled) {
  background: #e0e0e0;
}

.btn-primary {
  background: var(--theme-color);
  color: white;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

/* 动画效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* 响应式设计 */
@media (max-width: 600px) {
  .modal-content {
    max-width: 100%;
    border-radius: 16px 16px 0 0;
    margin-top: auto;
  }

  .icon {
    font-size: 28px;
  }

  .title {
    font-size: 20px;
  }
}
</style>