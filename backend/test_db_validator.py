#!/usr/bin/env python3
"""Test database validator after migration."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import DatabaseValidator


async def main():
    """Test database validator."""
    print("Testing database validator...")
    print()
    
    validator = DatabaseValidator()
    
    # Test write operation
    print("Testing write operation...")
    result = await validator.test_write_operation()
    
    if result:
        print("✅ Database validator test PASSED")
        print("   Users can be created with only telegram_id")
        return 0
    else:
        print("❌ Database validator test FAILED")
        print("   Check logs above for details")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
