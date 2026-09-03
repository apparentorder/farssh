"""PEP 517 backend: copy the repo README so hatchling can include it."""

import shutil
from pathlib import Path


def _ensure_readme():
	root = Path(__file__).resolve().parent
	dst = root / "README.md"
	src = root.parent / "README.md"
	if src.is_file():
		shutil.copyfile(src, dst)
	elif not dst.is_file():
		raise FileNotFoundError(dst)


def __getattr__(name):
	_ensure_readme()
	import hatchling.build as hatchling_build

	try:
		return getattr(hatchling_build, name)
	except AttributeError:
		raise AttributeError(name) from None
