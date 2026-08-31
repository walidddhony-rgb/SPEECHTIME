"""Official SpeechScribe desktop launcher.

Run from the repository root:
    py run_app.py

The professional Tkinter interface is the current application entry point.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PRIMARY_UI = PROJECT_ROOT / "speechscribe_pro_ui.py"


def load_primary_application():
    if not PRIMARY_UI.is_file():
        raise FileNotFoundError(
            f"Primary interface was not found: {PRIMARY_UI.name}. "
            "Keep run_app.py next to speechscribe_pro_ui.py."
        )

    spec = importlib.util.spec_from_file_location("speechscribe_pro_ui", PRIMARY_UI)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the professional interface module.")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    app_class = getattr(module, "SpeechScribeUI", None)
    if app_class is None:
        raise AttributeError(
            "speechscribe_pro_ui.py must define a SpeechScribeUI class."
        )
    return app_class


def main() -> int:
    try:
        app_class = load_primary_application()
        app = app_class()
        app.mainloop()
        return 0
    except Exception as exc:
        print(f"\nSpeechScribe could not start: {exc}", file=sys.stderr)
        print("Run this command from the project root: py run_app.py", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
