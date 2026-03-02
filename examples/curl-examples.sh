#!/bin/bash
# Eliza Lobster API - cURL Examples
# Make sure the server is running on http://localhost:3000

API_BASE="http://localhost:3000/api"
WALLET="11111111111111111111111111111112"

echo "=== Eliza Lobster API Examples ==="
echo

# Health check
echo "1. Health Check:"
curl -s http://localhost:3000/health | jq .
echo
echo

# Get all tasks
echo "2. Get All Tasks:"
curl -s "$API_BASE/tasks" | jq .
echo
echo

# Get task by ID
echo "3. Get Task by ID:"
curl -s "$API_BASE/tasks/1" | jq .
echo
echo

# Get tasks by category
echo "4. Get Tasks by Category (social):"
curl -s "$API_BASE/tasks/category/social" | jq .
echo
echo

# Request a bounty
echo "5. Request Bounty:"
BOUNTY_RESPONSE=$(curl -s -X POST "$API_BASE/bounties/request" \
  -H "Content-Type: application/json" \
  -d "{\"taskId\": \"1\", \"wallet\": \"$WALLET\"}")

echo "$BOUNTY_RESPONSE" | jq .
BOUNTY_ID=$(echo "$BOUNTY_RESPONSE" | jq -r '.data.id')
echo "Bounty ID: $BOUNTY_ID"
echo
echo

# Get user bounties
echo "6. Get User Bounties:"
curl -s "$API_BASE/bounties/$WALLET" | jq .
echo
echo

# Complete bounty (requires valid treasury)
echo "7. Complete Bounty (requires SOL in treasury):"
curl -s -X POST "$API_BASE/bounties/complete" \
  -H "Content-Type: application/json" \
  -d "{\"bountyId\": \"$BOUNTY_ID\", \"wallet\": \"$WALLET\", \"rewardToken\": \"SOL\"}" | jq .
echo
echo

echo "=== Examples Complete ==="
