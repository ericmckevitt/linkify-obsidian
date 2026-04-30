import sys
import re
from pathlib import Path

EXCLUDE = {"README", "_index", "TEMPLATE"}


def load_notes_and_aliases(vault_path):
    """
    Returns:
      - list of canonical note names
      - dict mapping phrase (lowercase) -> canonical note
    """
    phrase_map = {}
    notes = []

    for f in vault_path.iterdir():
        if not (f.is_file() and f.suffix == ".md"):
            continue
        if f.stem in EXCLUDE:
            continue

        note_name = f.stem
        notes.append(note_name)

        # Always map the note name itself
        phrase_map[note_name.lower()] = note_name

        content = f.read_text()

        # Extract frontmatter
        if content.startswith("---"):
            end = content.find("\n---", 3)
            if end != -1:
                frontmatter = content[3:end]

                # Find aliases block
                alias_match = re.search(r"aliases:\s*(.*)", frontmatter, re.DOTALL)
                if alias_match:
                    alias_block = alias_match.group(1)

                    # Find list items: - alias
                    aliases = re.findall(r"-\s*(.+)", alias_block)

                    for alias in aliases:
                        alias_clean = alias.strip()
                        phrase_map[alias_clean.lower()] = note_name

    return notes, phrase_map


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


def linkify(text, phrase_map, current_note):
    text, links = protect_existing_links(text)

    phrases = sorted(phrase_map.keys(), key=len, reverse=True)

    for phrase in phrases:
        canonical = phrase_map[phrase]

        if canonical == current_note:
            continue

        pattern = r'(?<!\[\[)(?<!\w)' + re.escape(phrase) + r'(?!\w)(?!\]\])'

        def replacer(match):
            original = match.group(0)

            if original.lower() == canonical.lower():
                return f'[[{canonical}]]'
            else:
                return f'[[{canonical}|{original}]]'

        text = re.sub(pattern, replacer, text, flags=re.IGNORECASE)

    text = restore_links(text, links)
    return text


def main():
    vault_path = Path(__file__).parent / "vault"

    if not vault_path.exists():
        print(f"Vault folder not found: {vault_path}")
        sys.exit(1)

    notes, phrase_map = load_notes_and_aliases(vault_path)

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
        updated = linkify(content, phrase_map, f.stem)

        if updated != content:
            f.write_text(updated)
            print(f"Updated: {f}")
        else:
            print(f"No changes: {f}")


if __name__ == "__main__":
    main()
