"""CLI Script to Execute LunarSynapse End-to-End Demo Mission."""

import sys
import json
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from outgraph.backend.app.database.session import SessionLocal, init_db
from outgraph.backend.app.services.demo_service import DemoService


def main():
    print("=" * 70)
    print("LunarSynapse -- Physics-Aware Lunar World Model")
    print("Executing End-to-End Automated Mission Pipeline...")
    print("=" * 70)

    init_db()
    db = SessionLocal()
    try:
        service = DemoService(db)
        result = service.run_complete_demo_mission()
        print("\n[SUCCESS] MISSION EXECUTION SUCCESSFUL!")
        print(json.dumps(result, indent=2))
        print("\n" + "=" * 70)
        print("You can now start the frontend and explore the Lunar World Model at http://localhost:5173")
        print("=" * 70)
    except Exception as e:
        print(f"\n[ERROR] Error executing demo mission: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
