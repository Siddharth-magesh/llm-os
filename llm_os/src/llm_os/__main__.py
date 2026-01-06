"""
LLM-OS Module Entry Point

Allows running LLM-OS as a module: python -m llm_os
"""

import sys
from llm_os.cli import main

if __name__ == "__main__":
    sys.exit(main())
