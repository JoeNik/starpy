#!/bin/bash

# 钱包API测试脚本
# 用于测试所有钱包相关的API端点

# 配置
BASE_URL="http://localhost:38001/api/wallet"
CHILD_ID=6
CONTENT_TYPE="Content-Type: application/json"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查jq是否可用
if command -v jq &> /dev/null; then
    HAS_JQ=true
    FORMAT_JSON="jq ."
else
    HAS_JQ=false
    FORMAT_JSON="cat"
    echo -e "${YELLOW}提示: 安装jq可以获得更好的JSON格式化输出${NC}\n"
fi

# 打印分隔线
print_separator() {
    echo -e "\n${BLUE}========================================${NC}"
}

# 打印测试标题
print_test() {
    print_separator
    echo -e "${BLUE}测试: $1${NC}"
    print_separator
}

# 打印成功消息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 打印失败消息
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 执行API调用并显示结果
call_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "\n${YELLOW}请求: $method $endpoint${NC}"
    if [ ! -z "$data" ]; then
        echo -e "${YELLOW}数据: $data${NC}"
    fi
    
    local response
    local http_code
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL$endpoint" -H "$CONTENT_TYPE")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL$endpoint" -H "$CONTENT_TYPE" -d "$data")
    fi
    
    # 分离响应体和状态码
    http_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | sed '$d')
    
    echo -e "\n${YELLOW}状态码: $http_code${NC}"
    echo -e "${YELLOW}响应:${NC}"
    echo "$response_body" | $FORMAT_JSON
    
    # 检查状态码
    if [ "$http_code" = "200" ]; then
        print_success "$description - 成功"
        return 0
    else
        print_error "$description - 失败 (HTTP $http_code)"
        return 1
    fi
}

# 开始测试
echo -e "${BLUE}======================================"
echo "钱包API测试"
echo "======================================"
echo "测试用户ID: $CHILD_ID"
echo "API地址: $BASE_URL"
echo -e "======================================${NC}\n"

# 等待用户确认
echo -e "${YELLOW}确保后端服务已启动 (python main.py)${NC}"
read -p "按回车键开始测试..."

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0

# 1. 获取钱包总览 (应该自动创建钱包账户)
print_test "1. 获取钱包总览 (自动创建钱包)"
if call_api "GET" "/$CHILD_ID/overview" "" "获取钱包总览"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 2. 存钱罐存款 - 100元
print_test "2. 存钱罐存款 - 100元"
if call_api "POST" "/$CHILD_ID/savings-box/deposit" '{"amount": 100.00, "remark": "测试存款100元"}' "存钱罐存款"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 3. 查询存钱罐信息
print_test "3. 查询存钱罐信息"
if call_api "GET" "/$CHILD_ID/savings-box" "" "查询存钱罐"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 4. 查询存钱罐交易明细
print_test "4. 查询存钱罐交易明细"
if call_api "GET" "/$CHILD_ID/savings-box/transactions?page=1&page_size=10" "" "存钱罐交易明细"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 5. 存钱罐取款 - 50元
print_test "5. 存钱罐取款 - 50元"
if call_api "POST" "/$CHILD_ID/savings-box/withdraw" '{"amount": 50.00, "remark": "测试取款50元"}' "存钱罐取款"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 6. 存钱罐余额不足测试 - 尝试取出超额金额
print_test "6. 存钱罐余额不足测试 (应该失败)"
echo -e "${YELLOW}这个测试预期会失败,用于验证余额不足的错误处理${NC}"
if call_api "POST" "/$CHILD_ID/savings-box/withdraw" '{"amount": 1000.00, "remark": "测试余额不足"}' "存钱罐余额不足"; then
    print_error "余额不足测试应该失败但成功了!"
else
    print_success "余额不足测试正确地返回了错误"
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 7. 零花钱存款 - 50元
print_test "7. 零花钱存款 - 50元"
if call_api "POST" "/$CHILD_ID/pocket-money/deposit" '{"amount": 50.00, "remark": "测试零花钱存款50元"}' "零花钱存款"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 8. 查询零花钱信息
print_test "8. 查询零花钱信息"
if call_api "GET" "/$CHILD_ID/pocket-money" "" "查询零花钱"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 9. 查询零花钱交易明细
print_test "9. 查询零花钱交易明细"
if call_api "GET" "/$CHILD_ID/pocket-money/transactions?page=1&page_size=10" "" "零花钱交易明细"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 10. 零花钱取款 - 20元
print_test "10. 零花钱取款 - 20元"
if call_api "POST" "/$CHILD_ID/pocket-money/withdraw" '{"amount": 20.00, "remark": "测试零花钱取款20元"}' "零花钱取款"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))
sleep 1

# 11. 再次获取钱包总览 (验证所有数据)
print_test "11. 再次获取钱包总览 (验证最终状态)"
if call_api "GET" "/$CHILD_ID/overview" "" "获取钱包总览"; then
    ((PASSED_TESTS++))
fi
((TOTAL_TESTS++))

# 测试总结
print_separator
echo -e "\n${BLUE}======================================"
echo "测试总结"
echo "======================================"
echo -e "总测试数: $TOTAL_TESTS"
echo -e "通过测试: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败测试: ${RED}$((TOTAL_TESTS - PASSED_TESTS))${NC}"
echo -e "通过率: $(awk "BEGIN {printf \"%.1f\", ($PASSED_TESTS/$TOTAL_TESTS)*100}")%"
echo -e "======================================${NC}\n"

# 预期结果说明
echo -e "${BLUE}预期最终状态:${NC}"
echo "- 存钱罐余额: 50.00元 (存入100 - 取出50)"
echo "- 零花钱余额: 30.00元 (存入50 - 取出20)"
echo "- 存钱罐应该有待结算利息字段"
echo "- 所有交易都应该有记录"
echo ""

if [ $PASSED_TESTS -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✓ 所有测试通过!${NC}"
    exit 0
else
    echo -e "${RED}✗ 部分测试失败,请检查API实现${NC}"
    exit 1
fi