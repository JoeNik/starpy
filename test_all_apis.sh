#!/bin/bash

# Base URL for the API
BASE_URL="http://localhost:8008/api"

# Function to print test headers
print_header() {
    echo ""
    echo "======================================================"
    echo "$1"
    echo "======================================================"
}

# Function to check command success
check_success() {
    if [ $? -eq 0 ]; then
        echo "✓ SUCCESS"
    else
        echo "✗ FAILURE"
    fi
}

# 1. Health Check
print_header "1. Testing Health Check"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8008/health
echo ""
check_success

# 2. Create a new child (with all required fields)
print_header "2. Creating a new child: 'Test Child'"
CHILD_RESPONSE=$(curl -s -X POST "$BASE_URL/children" \
    -H "Content-Type: application/json" \
    -d '{"name": "Test Child", "birthday": "2018-01-15", "gender": "male"}')
CHILD_ID=$(echo $CHILD_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)
echo "Create Child Response: $CHILD_RESPONSE"
echo "Created Child with ID: $CHILD_ID"
check_success

# 3. Get the child
print_header "3. Retrieving child with ID: $CHILD_ID"
curl -s "$BASE_URL/children/$CHILD_ID"
echo ""
check_success

# 4. Update the child
print_header "4. Updating child's name to 'Updated Child'"
curl -s -X PUT "$BASE_URL/children/$CHILD_ID" \
    -H "Content-Type: application/json" \
    -d '{"name": "Updated Child"}'
echo ""
check_success

# 5. Add stars to the child
print_header "5. Adding 10 stars to child ID: $CHILD_ID"
curl -s -X POST "$BASE_URL/children/$CHILD_ID/stars" \
    -H "Content-Type: application/json" \
    -d '{"type": "earn", "amount": 10, "reason": "Good behavior"}'
echo ""
check_success

# 6. Deduct stars from the child
print_header "6. Deducting 5 stars from child ID: $CHILD_ID"
curl -s -X POST "$BASE_URL/children/$CHILD_ID/stars" \
    -H "Content-Type: application/json" \
    -d '{"type": "spend", "amount": 5, "reason": "Forgot homework"}'
echo ""
check_success

# 7. Create a new reward (with all required fields)
print_header "7. Creating a new reward: 'Ice Cream'"
REWARD_RESPONSE=$(curl -s -X POST "$BASE_URL/rewards" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Ice Cream\", \"star_cost\": 20, \"child_ids\": [$CHILD_ID]}")
REWARD_ID=$(echo $REWARD_RESPONSE | grep -o '"id":[0-9]*' | cut -d':' -f2)
echo "Create Reward Response: $REWARD_RESPONSE"
echo "Created Reward with ID: $REWARD_ID"
check_success

# 8. Get the reward
print_header "8. Retrieving reward with ID: $REWARD_ID"
curl -s "$BASE_URL/rewards/$REWARD_ID"
echo ""
check_success

# 9. Redeem the reward
print_header "9. Redeeming reward ID: $REWARD_ID for child ID: $CHILD_ID"
curl -s -X POST "$BASE_URL/rewards/$REWARD_ID/redeem" \
    -H "Content-Type: application/json" \
    -d "{\"deductions\": [{\"child_id\": $CHILD_ID, \"amount\": 20}]}"
echo ""
check_success

# 10. Get the child again to verify star count
print_header "10. Verifying final star count for child ID: $CHILD_ID"
curl -s "$BASE_URL/children/$CHILD_ID"
echo ""
check_success

# 11. Delete the reward
print_header "11. Deleting reward with ID: $REWARD_ID"
curl -s -X DELETE "$BASE_URL/rewards/$REWARD_ID"
echo ""
check_success

# 12. Delete the child
print_header "12. Deleting child with ID: $CHILD_ID"
curl -s -X DELETE "$BASE_URL/children/$CHILD_ID"
echo ""
check_success

echo ""
echo "======================================================"
echo "All tests completed."
echo "======================================================"