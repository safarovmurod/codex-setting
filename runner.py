"""Works with the isolated Python runtime bundled in the pinned upstream release."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from codex_setting.cli import main
if __name__=='__main__':main()
