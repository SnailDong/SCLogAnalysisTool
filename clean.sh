#!/bin/bash

# 清除所有缓存和生成物
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; find . -type f -name "*.pyc" -delete; rm -rf build/ dist/ venv/ *.spec .pytest_cache/ .coverage htmlcov/ .DS_Store; rm -f caches/*