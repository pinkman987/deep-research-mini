import sys
from pathlib import Path

# 让 tests 能 import 项目根目录下的 research / search_tool
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
