<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="modal-overlay" @click="handleClose">
        <Transition name="slide-up">
          <div
            v-if="show"
            class="modal-content"
            @click.stop
          >
            <button class="btn-close" @click="handleClose">×</button>

            <!-- 头部 -->
            <div class="modal-header">
              <div class="title-row">
                <span class="icon">💰</span>
                <h2 class="title">收益计算器</h2>
              </div>
              <p class="subtitle">预估您的储蓄收益</p>
            </div>

            <!-- 表单内容 -->
            <div class="modal-body">
              <!-- 存入金额输入 -->
              <div class="form-group">
                <label class="form-label">存入金额</label>
                <div class="input-wrapper">
                  <span class="currency">¥</span>
                  <input
                    v-model.number="amount"
                    type="number"
                    step="0.01"
                    min="0"
                    class="form-input amount-input"
                    placeholder="请输入存入金额"
                  />
                </div>
              </div>

              <!-- 年化利率输入 -->
              <div class="form-group">
                <label class="form-label">年化利率</label>
                <div class="input-wrapper">
                  <input
                    v-model.number="annualRate"
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    class="form-input rate-input"
                    placeholder="年化利率"
                  />
                  <span class="suffix">%</span>
                </div>
              </div>

              <!-- 计算结果展示 -->
              <div v-if="showResults" class="results-section">
                <div class="result-card daily">
                  <div class="result-header">
                    <span class="result-icon">📈</span>
                    <span class="result-label">日收益</span>
                  </div>
                  <div class="result-value">+¥{{ dailyEarnings.toFixed(2) }}</div>
                </div>

                <div class="result-card annual">
                  <div class="result-header">
                    <span class="result-icon">💎</span>
                    <span class="result-label">年收益</span>
                  </div>
                  <div class="result-value">+¥{{ annualEarnings.toFixed(2) }}</div>
                </div>
              </div>

              <!-- 提示信息 -->
              <div class="tips">
                <p class="tip-item">💡 实际收益以每日结算为准</p>
                <p class="tip-item">收益将自动加入存钱罐余额</p>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// Props定义
interface Props {
  show: boolean
  defaultRate?: number
}

const props = withDefaults(defineProps<Props>(), {
  defaultRate: 5.0
})

// Emits定义
const emit = defineEmits<{
  'close': []
}>()

// 响应式状态
const amount = ref<number>(0)
const annualRate = ref<number>(props.defaultRate)

// 计算属性
const showResults = computed(() => {
  return amount.value > 0 && annualRate.value >= 0 && annualRate.value <= 100
})

const dailyEarnings = computed(() => {
  if (!amount.value || amount.value <= 0) return 0
  return (amount.value * (annualRate.value / 100)) / 365
})

const annualEarnings = computed(() => {
  if (!amount.value || amount.value <= 0) return 0
  return amount.value * (annualRate.value / 100)
})

// 关闭对话框
const handleClose = () => {
  emit('close')
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
    // 重置默认利率
    annualRate.value = props.defaultRate
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
  max-width: 450px;
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
  text-align: center;
}

.title-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
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

.subtitle {
  font-size: 14px;
  color: #999;
  margin: 0;
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
  color: #667eea;
}

.suffix {
  position: absolute;
  right: 12px;
  font-size: 16px;
  font-weight: bold;
  color: #667eea;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  font-size: 16px;
  transition: border-color 0.3s;
}

.amount-input {
  padding-left: 32px;
  font-size: 20px;
  font-weight: 600;
}

.rate-input {
  padding-right: 32px;
  font-size: 18px;
  font-weight: 600;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin: 24px 0;
}

.result-card {
  padding: 20px;
  border-radius: 16px;
  border: 2px solid;
  transition: transform 0.2s;
}

.result-card:hover {
  transform: translateY(-2px);
}

.result-card.daily {
  background: linear-gradient(135deg, #f0fff4 0%, #e8f5e9 100%);
  border-color: #4CAF50;
}

.result-card.annual {
  background: linear-gradient(135deg, #fff9e6 0%, #ffeaa7 100%);
  border-color: #FFB300;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.result-icon {
  font-size: 24px;
}

.result-label {
  font-size: 14px;
  color: #666;
  font-weight: 600;
}

.result-value {
  font-size: 28px;
  font-weight: bold;
  line-height: 1.2;
}

.result-card.daily .result-value {
  color: #2E7D32;
}

.result-card.annual .result-value {
  color: #F57C00;
}

.tips {
  padding: 16px;
  background: #f5f5f5;
  border-radius: 12px;
  margin-top: 20px;
}

.tip-item {
  font-size: 13px;
  color: #666;
  margin: 6px 0;
  line-height: 1.5;
}

.tip-item:first-child {
  margin-top: 0;
}

.tip-item:last-child {
  margin-bottom: 0;
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

  .result-value {
    font-size: 24px;
  }
}
</style>