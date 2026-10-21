"""ScreenInk entry point."""

def main():
    """Keep unattended package-check failures out of windowed error dialogs."""
    import sys
    import tempfile
    import traceback
    from pathlib import Path

    try:
        from screenink.application import run
        return run()
    except Exception:
        if "--smoke-test" in sys.argv:
            (Path(tempfile.gettempdir()) / "ScreenInk-beta-smoke.log").write_text(
                traceback.format_exc(), encoding="utf-8")
            return 1
        raise


if __name__ == "__main__":
    raise SystemExit(main())
