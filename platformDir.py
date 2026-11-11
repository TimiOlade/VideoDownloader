from pathlib import Path

downloads = Path.home() / "Downloads"
if not downloads.exists():
    raise FileNotFoundError(f"Downloads folder not found: {downloads}")
else:
    print(downloads)