"""Check text, local Markdown links/anchors, roadmap and M1 catalogue references."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".idea", ".vscode"}
TEXT_SUFFIXES = {".md", ".py"}
TEXT_NAMES = {".editorconfig", ".gitignore"}
LINK = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
MILESTONE = re.compile(r"^\|\s*(?:\*\*)?(M\d+ — [^|*]+?)(?:\*\*)?\s*\|", re.M)


def anchors(file: Path) -> set[str]:
    """Heading slugs for the simple ATX headings used in project documents."""
    slugs = set()
    counts = {}
    for heading in re.findall(r"^#{1,6}\s+(.+)$", file.read_text(), re.M):
        slug = re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")
        duplicate = counts.get(slug, 0)
        counts[slug] = duplicate + 1
        slugs.add(f"{slug}-{duplicate}" if duplicate else slug)
    return slugs


def main() -> int:
    errors = []
    text_count = 0
    markdown_count = 0
    local_link_count = 0
    for file in sorted(ROOT.rglob("*")):
        relative = file.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if not file.is_file():
            continue
        if file.suffix not in TEXT_SUFFIXES and file.name not in TEXT_NAMES:
            continue
        text_count += 1
        try:
            content = file.read_bytes().decode("utf-8")
        except UnicodeError:
            errors.append(f"{relative}: invalid UTF-8")
            continue
        if not content:
            errors.append(f"{relative}: empty file")
        elif not content.endswith("\n"):
            errors.append(f"{relative}: missing final newline")
        if "\r" in content:
            errors.append(f"{relative}: use LF line endings")
        for number, line in enumerate(content.splitlines(), 1):
            if line != line.rstrip():
                errors.append(f"{relative}:{number}: trailing whitespace")
        if file.suffix != ".md":
            continue
        markdown_count += 1
        # The M0 documents use inline links without titles or nested parentheses.
        for match in LINK.finditer(content):
            target = match.group(1).strip().removeprefix("<").removesuffix(">")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc:
                continue
            local_link_count += 1
            destination = (file.parent / unquote(parsed.path)).resolve() if parsed.path else file
            if not destination.is_relative_to(ROOT):
                errors.append(f"{relative}: link leaves repository: {target}")
            elif not destination.exists():
                errors.append(f"{relative}: missing link target: {target}")
            elif parsed.fragment and destination.suffix == ".md":
                if unquote(parsed.fragment) not in anchors(destination):
                    errors.append(f"{relative}: missing heading anchor: {target}")
    brief = ROOT / "docs/project/master-brief.md"
    roadmap = ROOT / "docs/roadmap.md"
    if brief.exists() and roadmap.exists():
        expected = MILESTONE.findall(brief.read_text())
        actual = MILESTONE.findall(roadmap.read_text())
        if len(expected) != 13 or actual != expected:
            errors.append("docs/roadmap.md: M0–M12 titles/order differ from master brief")
    else:
        errors.append("master brief or roadmap missing")
    if (ROOT / "docs/architecture.md").exists():
        catalogues = {
            "J": ("docs/requirements.md", r"^\| (J\d{2}) /"),
            "NF": ("docs/requirements.md", r"^\| (NF\d{2}) "),
            "V": ("docs/validation-strategy.md", r"^\| (V\d{2}) \|"),
            "T": ("docs/threat-model.md", r"^\| (T\d{2}) "),
        }
        for prefix, (name, pattern) in catalogues.items():
            catalogue = ROOT / name
            if not catalogue.exists():
                errors.append(f"{name}: required M1 catalogue missing")
                continue
            definitions = set(re.findall(pattern, catalogue.read_text(), re.M))
            if not definitions:
                errors.append(f"{name}: no {prefix} definitions found")
            for doc in (ROOT / "docs").rglob("*.md"):
                references = set(re.findall(rf"\b{prefix}\d{{2}}\b", doc.read_text()))
                for missing in sorted(references - definitions):
                    errors.append(f"{doc.relative_to(ROOT)}: undefined {missing} reference")
    if errors:
        print("FAIL: repository documentation checks")
        print("\n".join(errors))
        return 1
    print(
        f"PASS: {text_count} text files, {markdown_count} Markdown files, "
        f"{local_link_count} relative file links; UTF-8/LF, final newlines, "
        "and trailing whitespace checked."
    )
    print("Scope: includes untracked files and local heading anchors; external URLs are not checked.")
    print("PASS: all 13 roadmap milestone titles/order match the authoritative master brief.")
    if (ROOT / "docs/architecture.md").exists():
        print("PASS: M1 journey, non-functional, validation and threat references resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
