from pathlib import Path
import zipfile


def build_api():
  """
  Build and zip lambda code.
  """
  root = Path(__file__).parent.parent
  builddir = root / "build"
  builddir.mkdir(exist_ok=True)
  with zipfile.ZipFile(builddir / "api.zip", "w") as z:
    z.write(root / "api" / "api.py", "api.py")
    z.write(root / "api" / "resources" / "strongs.json", "resources/strongs.json")
    z.write(root / "api" / "resources" / "books.json", "resources/books.json")
