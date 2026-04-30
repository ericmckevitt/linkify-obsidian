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

        # only replace first occurrence (cleaner output, still update for debate)
        text = re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)

    # restore existing links
    text = restore_links(text, links)

    return text


def main():
    if len(sys.argv) != 2:
        print("Usage: python linkify.py <file_name.md>")
        sys.exit(1)

    # vault_path = Path(__file__).parent
    vault_path = Path(__file__).parent / "vault"
    file_path = Path(sys.argv[1])

    # handle relative paths
    if not file_path.is_absolute():
        file_path = vault_path / file_path

    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    notes = load_notes(vault_path)
    content = file_path.read_text()

    updated = linkify(content, notes, file_path.stem)

    file_path.write_text(updated)

    print(f"Linkified: {file_path}")


if __name__ == "__main__":
    main()
