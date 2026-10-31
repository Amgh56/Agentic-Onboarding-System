from pathlib import Path

FOLDER = Path(__file__).parent


def render(name: str, **values) -> str:
    """The Arabic text first, then the English text, in one email."""
    arabic = (FOLDER / "ar" / f"{name}.txt").read_text().format(**values)
    english = (FOLDER / "en" / f"{name}.txt").read_text().format(**values)
    return f"{arabic}\n---\n\n{english}"
