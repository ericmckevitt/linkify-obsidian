import sys
import re
from pathlib import Path

EXCLUDE = {"README", "_index", "TEMPLATE"}

def load_notes(vault_path):
    notes = []
    for f in vault_path.iterdir():
        if f.is_file() and f.suffix == ".md":
            if f.stem in EXCLUDE:
                continue
            notes.append(f.stem)
    return notes

def protect_existing_links(text):
    links = []

    def replacer(match):
        links.append(match.group(0))
        return f"__LINK_{len(links)-1}__"

    text = re.sub(r"\[\[.*?\]\]", replacer, text)
    return text, links


def restore_links(text, links):
    for i, link in enumerate(links):
        text = text.replace(f"__LINK_{i}__", link)
    return text


def linkify(text, notes, current_note):
    # protect existing [[links]]
    text, links = protect_existing_links(text)

    # sort longest names first to avoid partial matches
    notes_sorted = sorted(notes, key=len, reverse=True)

    for note in notes_sorted:
        if note == current_note:
            continue

        pattern = r'\b' + re.escape(note) + r'\b'
        replacement = f'[[{note}]]'

        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # restore existing links
    text = restore_links(text, links)

    return text


def main():
    vault_path = Path(__file__).parent / "vault"

    if not vault_path.exists():
        print(f"Vault folder not found: {vault_path}")
        sys.exit(1)

    notes = load_notes(vault_path)

    if len(sys.argv) == 2 and sys.argv[1] == "--all":
        files = list(vault_path.glob("*.md"))
    elif len(sys.argv) == 2:
        file_path = Path(sys.argv[1])
        if not file_path.is_absolute():
            file_path = vault_path / file_path

        if not file_path.exists():
            print(f"File not found: {file_path}")
            sys.exit(1)

        files = [file_path]
    else:
        print("Usage:")
        print("  python linkify.py <file.md>")
        print("  python linkify.py --all")
        sys.exit(1)

    for f in files:
        content = f.read_text()
        updated = linkify(content, notes, f.stem)
        f.write_text(updated)
        print(f"Linkified: {f}")
