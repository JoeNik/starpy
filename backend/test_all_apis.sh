#!/bin/bash

# 快速测试所有API接口
BASE_URL="http://localhost:8000"

echo "=========================================="
echo "开始快速测试所有API接口"
echo "=========================================="

# 1. 创建第一个孩子
echo -e "\n1. 创建孩子 (小明)"
CHILD1=$(curl -s -X POST "$BASE_URL/api/children" \
  -F "name=小明" \
  -F "birthday=2018-05-01" \
  -F "gender=male")
echo "$CHILD1" | python3 -m json.tool
CHILD1_ID=$(echo "$CHILD1" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "孩子1 ID: $CHILD1_ID"

# 2. 创建第二个孩子
echo -e "\n2. 创建孩子 (小红)"
CHILD2=$(curl -s -X POST "$BASE_URL/api/children" \
  -F "name=小红" \
  -F "birthday=2019-08-15" \
  -F "gender=female")
echo "$CHILD2" | python3 -m json.tool
CHILD2_ID=$(echo "$CHILD2" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "孩子2 ID: $CHILD2_ID"

# 3. 查询所有孩子
echo -e "\n3. 查询所有孩子"
curl -s "$BASE_URL/api/children" | python3 -m json.tool

# 4. 查询单个孩子
echo -e "\n4. 查询孩子详情 (ID: $CHILD1_ID)"
curl -s "$BASE_URL/api/children/$CHILD1_ID" | python3 -m json.tool

# 5. 给孩子1增加星星
echo -e "\n5. 给小明增加10颗星星"
curl -s -X POST "$BASE_URL/api/children/$CHILD1_ID/stars/add" \
  -H "Content-Type: application/json" \
  -d "{\"amount\":10,\"reason\":\"完成作业\"}" | python3 -m json.tool

# 6. 给孩子2增加星星
echo -e "\n6. 给小红增加15颗星星"
curl -s -X POST "$BASE_URL/api/children/$CHILD2_ID/stars/add" \
  -H "Content-Type: application/json" \
  -d "{\"amount\":15,\"reason\":\"帮助家务\"}" | python3 -m json.tool

# 7. 创建奖励 (Form-data with child_ids as JSON string)
echo -e "\n7. 创建奖励 (玩具车)"
REWARD1=$(curl -s -X POST "$BASE_URL/api/rewards" \
  -F "name=玩具车" \
  -F "star_cost=20" \
  -F "description=小汽车玩具" \
  -F "child_ids=[${CHILD1_ID},${CHILD2_ID}]")
echo "$REWARD1" | python3 -m json.tool
REWARD1_ID=$(echo "$REWARD1" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "奖励1 ID: $REWARD1_ID"

# 8. 创建第二个奖励
echo -e "\n8. 创建奖励 (绘本书)"
REWARD2=$(curl -s -X POST "$BASE_URL/api/rewards" \
  -F "name=绘本书" \
  -F "star_cost=8" \
  -F "child_ids=[${CHILD1_ID}]")
echo "$REWARD2" | python3 -m json.tool
REWARD2_ID=$(echo "$REWARD2" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
echo "奖励2 ID: $REWARD2_ID"

# 9. 查询所有奖励
echo -e "\n9. 查询所有奖励"
curl -s "$BASE_URL/api/rewards" | python3 -m json.tool

# 10. 查询单个奖励
echo -e "\n10. 查询奖励详情 (ID: $REWARD1_ID)"
curl -s "$BASE_URL/api/rewards/$REWARD1_ID" | python3 -m json.tool

# 11. 更新孩子信息
echo -e "\n11. 更新孩子信息 (小明改名)"
curl -s -X PUT "$BASE_URL/api/children/$CHILD1_ID" \
  -F "name=小明明" | python3 -m json.tool

# 12. 扣除星星
echo -e "\n12. 从小明扣除3颗星星"
curl -s -X POST "$BASE_URL/api/children/$CHILD1_ID/stars/deduct" \
  -H "Content-Type: application/json" \
  -d "{\"amount\":3,\"reason\":\"调皮\"}" | python3 -m json.tool

# 13. 兑换奖励
echo -e "\n13. 兑换奖励 (小明和小红一起兑换玩具车)"
curl -s -X POST "$BASE_URL/api/rewards/$REWARD1_ID/redeem" \
  -F "deductions=[{\"child_id\":${CHILD1_ID},\"amount\":7},{\"child_id\":${CHILD2_ID},\"amount\":13}]" | python3 -m json.tool

# 14. 再次查询孩子详情(查看星星变化)
echo -e "\n14. 查询孩子详情 (查看星星变化)"
curl -s "$BASE_URL/api/children/$CHILD1_ID" | python3 -m json.tool

# 15. 更新奖励
echo -e "\n15. 更新奖励 (绘本书改价)"
curl -s -X PUT "$BASE_URL/api/rewards/$REWARD2_ID" \
  -F "star_cost=5" | python3 -m json.tool

# 16. 删除奖励
echo -e "\n16. 删除奖励 (绘本书)"
curl -s -X DELETE "$BASE_URL/api/rewards/$REWARD2_ID" | python3 -m json.tool

# 17. 删除孩子
echo -e "\n17. 删除孩子 (小红)"
curl -s -X DELETE "$BASE_URL/api/children/$CHILD2_ID" | python3 -m json.tool

echo -e "\n=========================================="
echo "所有API测试完成!"
echo "=========================================="