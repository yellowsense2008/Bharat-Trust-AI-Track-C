#!/bin/bash

# Conversational Intake API - Interactive Test Script
# Usage: ./test_conversation_curl.sh

set -e

BASE_URL="http://localhost:8000"
USERNAME="conv_test_user_$(date +%s)"
PASSWORD="test123"
TOKEN=""

echo "=================================================="
echo "🧪 Conversational Intake API - Interactive Test"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if server is running
print_step "Checking if server is running..."
if ! curl -s "$BASE_URL/health" > /dev/null; then
    print_error "Server is not running at $BASE_URL"
    echo "Please start the server with: docker compose up"
    exit 1
fi
print_success "Server is running"
echo ""

# Register user
print_step "Registering test user: $USERNAME"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"email\": \"${USERNAME}@test.com\",
    \"password\": \"$PASSWORD\",
    \"role\": \"citizen\"
  }")

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    print_success "User registered successfully"
else
    print_info "User might already exist, continuing..."
fi
echo ""

# Login
print_step "Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$USERNAME&password=$PASSWORD")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    print_error "Failed to get authentication token"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

print_success "Login successful"
print_info "Token: ${TOKEN:0:20}..."
echo ""

# Start conversation
print_step "Starting conversation with emotional message..."
echo ""
echo "💬 User: Oh my god my payment failed! I am so worried!"
echo ""

START_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Oh my god my payment failed! I am so worried!"
  }')

AI_RESPONSE=$(echo "$START_RESPONSE" | grep -o '"ai_response":"[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g')
echo "🤖 AI: $AI_RESPONSE"
echo ""

read -p "Press Enter to continue..."
echo ""

# Message 2: Bank name
print_step "Providing bank name..."
echo ""
echo "💬 User: State Bank of India"
echo ""

MSG2_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "State Bank of India"
  }')

AI_RESPONSE=$(echo "$MSG2_RESPONSE" | grep -o '"ai_response":"[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g')
echo "🤖 AI: $AI_RESPONSE"
echo ""

read -p "Press Enter to continue..."
echo ""

# Message 3: Transaction type
print_step "Providing transaction type..."
echo ""
echo "💬 User: UPI payment"
echo ""

MSG3_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "UPI payment"
  }')

AI_RESPONSE=$(echo "$MSG3_RESPONSE" | grep -o '"ai_response":"[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g')
echo "🤖 AI: $AI_RESPONSE"
echo ""

read -p "Press Enter to continue..."
echo ""

# Message 4: Amount
print_step "Providing amount..."
echo ""
echo "💬 User: 5000 rupees"
echo ""

MSG4_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "5000 rupees"
  }')

AI_RESPONSE=$(echo "$MSG4_RESPONSE" | grep -o '"ai_response":"[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g')
echo "🤖 AI: $AI_RESPONSE"
echo ""

read -p "Press Enter to continue..."
echo ""

# Message 5: Date
print_step "Providing date..."
echo ""
echo "💬 User: Today morning around 10 AM"
echo ""

MSG5_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Today morning around 10 AM"
  }')

AI_RESPONSE=$(echo "$MSG5_RESPONSE" | grep -o '"ai_response":"[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g')
echo "🤖 AI: $AI_RESPONSE"
echo ""

read -p "Press Enter to continue..."
echo ""

# Message 6: Transaction ID
print_step "Providing transaction ID..."
echo ""
echo "💬 User: I don't have the transaction ID"
echo ""

MSG6_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I dont have the transaction ID"
  }')

AI_RESPONSE=$(echo "$MSG6_RESPONSE" | grep -o '"ai_response":"[^"]*' | cut -d'"' -f4 | sed 's/\\n/\n/g')
echo "🤖 AI: $AI_RESPONSE"
echo ""

read -p "Press Enter to continue..."
echo ""

# Message 7: Issue description (final)
print_step "Providing issue description (final step)..."
echo ""
echo "💬 User: Money was deducted from my account but the merchant did not receive it. The payment shows failed in my app but amount is gone."
echo ""

FINAL_RESPONSE=$(curl -s -X POST "$BASE_URL/conversation/message" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Money was deducted from my account but the merchant did not receive it. The payment shows failed in my app but amount is gone."
  }')

echo "$FINAL_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$FINAL_RESPONSE"
echo ""

# Check if conversation completed
if echo "$FINAL_RESPONSE" | grep -q '"conversation_complete":true'; then
    print_success "Conversation completed successfully!"
    
    REFERENCE_ID=$(echo "$FINAL_RESPONSE" | grep -o '"reference_id":"[^"]*' | cut -d'"' -f4)
    if [ ! -z "$REFERENCE_ID" ]; then
        print_success "Complaint Reference ID: $REFERENCE_ID"
    fi
else
    print_info "Conversation not yet complete, may need more information"
fi

echo ""
echo "=================================================="
echo "✅ Test completed!"
echo "=================================================="
