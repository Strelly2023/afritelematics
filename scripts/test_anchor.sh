#!/usr/bin/env bash

BASE_URL=$1
TOKEN=$2

curl -s -X POST $BASE_URL/v1/architecture/anchor/blockchain \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"profile":"sepolia","mode":"contract"}' | jq .