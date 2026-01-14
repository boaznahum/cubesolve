#!/bin/bash

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Running: PYRIGHT${NC}"
echo -e "${CYAN}========================================${NC}"
pyright src/cube
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}PYRIGHT FAILED${NC}"
    exit $?
fi
echo -e "${GREEN}PYRIGHT passed${NC}"

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Running: MYPY${NC}"
echo -e "${CYAN}========================================${NC}"
mypy -p cube
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}MYPY FAILED${NC}"
    exit $?
fi
echo -e "${GREEN}MYPY passed${NC}"

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Running: RUFF${NC}"
echo -e "${CYAN}========================================${NC}"
ruff check src/cube
if [ $? -ne 0 ]; then
    echo ""
    echo -e "${RED}RUFF FAILED${NC}"
    exit $?
fi
echo -e "${GREEN}RUFF passed${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ALL CHECKS PASSED${NC}"
echo -e "${GREEN}========================================${NC}"