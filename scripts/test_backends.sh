#!/bin/bash

echo "=================================="
echo "Testing Backend A"
echo "=================================="

curl -i http://localhost:3001/
echo ""

curl -i http://localhost:3001/api/status
echo ""

echo "=================================="
echo "Testing Backend B"
echo "=================================="

curl -i http://localhost:3002/
echo ""

curl -i http://localhost:3002/api/status
echo ""

echo "=================================="
echo "Backend testing complete"
echo "=================================="