#!/bin/bash

# Test script for improved bank selection
# Tests multiple bank name variations

set -e

BASE_URL="http://localhost:8000"
USERNAME="bank_test_$(date +%s)"
PASSWORD="test123"

echo "🧪 Testing Improved Bank Selection"
echo "===================================="
echo ""

# Register and login
echo "📝 Registering user..."
curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"email\": \"${USERNAME}@test.com\",
    \"password\": \"$PASSWORD\",
    \"role\": \"citizen\"
  }" > /dev/null

echo "🔐 Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Failed to get token"
    exit 1
fi

echo "✅ Authenticated"
echo ""

# Test 1: Start conversation with emotional message
echo "Test 1: Emotional complaint"
echo "----------------------------"
echo "💬 User: Oh my god my payment failed! I am so worried!"
echo ""

START_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Oh my god my payment failed! I am so worried!"
  }')

echo "$START_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('🤖 AI:', data['ai_response'])"
echo ""
echo "----------------------------"
echo ""

# Test 2: Try different bank names
echo "Test 2: Bank name variations"
echo "----------------------------"

BANKS=("HDFC" "State Bank of India" "ICICI Bank" "Axis" "Kotak Mahindra")

for BANK in "${BANKS[@]}"; do
    echo "Testing: $BANK"
    
    # Start new conversation
    START=$(curl -s -X POST "$BASE_URL/conversation/start" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"message\": \"My payment failed\"}")
    
    # Send bank name
    BANK_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/message" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{\"message\": \"$BANK\"}")
    
    echo "$BANK_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('  ✓ Detected:', data.get('ai_response', 'Error')[:50])"
    echo ""
done

echo "===================================="
echo "✅ All tests completed!"
