"""Markdown <-> LionLingo JSON.

Markdown is grouped by language. A bullet list is one line per item.
Longer text is indented under the language label.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

LANGS = ("en", "fr", "de", "am", "ar", "es", "ja", "zh")
LEVELS = ("A1", "A2", "B1", "B2", "C1", "C2")
LANG_LINE = re.compile(r"^(en|fr|de|am|ar|es|ja|zh):$")

CHAPTERS = {
    1: "essentials",
    2: "conversation",
    3: "colours_and_numbers",
    4: "time_and_calendar",
    5: "transport_and_places",
    6: "family_and_contacts",
    7: "feelings_and_activities",
    8: "beach_and_weather",
    9: "food_drink_and_hotel",
    10: "emergency",
    11: "shopping",
    12: "celebrations",
}


def slugify(text: str, fallback: str = "item") -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "_", ascii_text).strip("_").lower()
    return (slug[:48] or fallback)


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ordered_langs(sample: dict) -> list[str]:
    found = [lang for lang in sample if lang in LANGS]
    return found or [lang for lang in LANGS if lang in sample]


def front_matter(meta: dict) -> str:
    lines = ["---"]
    for key, value in meta.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("Unclosed front matter")
    raw = text[4:end]
    body = text[end + 5 :]
    if body.startswith("\n"):
        body = body[1:]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError(f"Bad front matter line: {line}")
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def render_bullets(by_lang: dict[str, list[str]]) -> str:
    chunks = []
    for lang in ordered_langs(by_lang):
        if lang not in by_lang:
            continue
        lines = [f"{lang}:"] + [f"- {item}" for item in by_lang[lang]]
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


def render_text(by_lang: dict[str, str]) -> str:
    chunks = []
    for lang in ordered_langs(by_lang):
        if lang not in by_lang:
            continue
        rendered = []
        parts = by_lang[lang].split("\n")
        for index, line in enumerate(parts):
            if index == len(parts) - 1 and line == "":
                rendered.append("  ")
            elif line == "":
                rendered.append("")
            else:
                rendered.append(f"  {line}")
        chunks.append(f"{lang}:\n" + "\n".join(rendered))
    return "\n".join(chunks)


def render_strings(by_lang: dict[str, str]) -> str:
    if any("\n" in value for value in by_lang.values()):
        return render_text(by_lang)
    return render_bullets({lang: [value] for lang, value in by_lang.items()})


def render_section(name: str, body: str) -> str:
    if not body:
        return f"## {name}"
    return f"## {name}\n\n{body}"


def render_file(meta: dict | None, body: str) -> str:
    text = body.rstrip("\n") + "\n"
    if not meta:
        return text
    return front_matter(meta) + "\n\n" + text


def split_sections(body: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    name = ""
    lines: list[str] = []
    for line in body.split("\n"):
        if line.startswith("## "):
            sections.append((name, lines))
            name = line[3:].strip()
            lines = []
        else:
            lines.append(line)
    sections.append((name, lines))
    return sections


def language_blocks(lines: list[str]) -> dict[str, list[str]]:
    if lines and lines[-1] == "":
        lines = lines[:-1]
    blocks: dict[str, list[str]] = {}
    current = None
    buf: list[str] = []

    def flush() -> None:
        nonlocal buf
        if current is None:
            return
        while buf and buf[0] == "":
            buf.pop(0)
        blocks[current] = buf
        buf = []

    for line in lines:
        if LANG_LINE.match(line):
            flush()
            current = line[:-1]
        elif current is not None:
            buf.append(line)
    flush()
    return blocks


def undent(lines: list[str]) -> str:
    # A trailing two-space line is the preserved final newline, not an extra blank.
    if lines and lines[-1] == "  ":
        lines = lines[:-1]
        trailing = "\n"
    else:
        trailing = ""
    out = []
    for line in lines:
        if line.startswith("  "):
            out.append(line[2:])
        elif line == "":
            out.append("")
        else:
            raise ValueError(f"Expected indented text, got: {line}")
    return "\n".join(out) + trailing


def as_bullets(lines: list[str]) -> list[str]:
    items = []
    for line in lines:
        if line == "":
            continue
        if not line.startswith("- "):
            raise ValueError(f"Expected a bullet, got: {line}")
        items.append(line[2:])
    return items


def block_value(lines: list[str]):
    content = [line for line in lines if line != ""]
    if content and content[0].startswith("- "):
        return as_bullets(lines)
    return undent(lines)


def section_map(lines: list[str]) -> dict:
    parsed = {}
    for lang, block in language_blocks(lines).items():
        value = block_value(block)
        if isinstance(value, list):
            if len(value) != 1:
                raise ValueError(f"{lang} should have one entry")
            parsed[lang] = value[0]
        else:
            parsed[lang] = value
    return parsed


def section_lists(lines: list[str]) -> dict[str, list[str]]:
    parsed = {}
    for lang, block in language_blocks(lines).items():
        parsed[lang] = as_bullets(block)
    return parsed


def zip_langs(columns: dict[str, list[str]]) -> list[dict]:
    if not columns:
        return []
    length = len(next(iter(columns.values())))
    for lang, values in columns.items():
        if len(values) != length:
            raise ValueError(f"{lang} has {len(values)} entries, expected {length}")
    rows = []
    for index in range(length):
        rows.append({lang: columns[lang][index] for lang in columns})
    return rows


def vocab_columns(entries: list[dict]) -> dict[str, list[str]]:
    langs = ordered_langs(entries[0]) if entries else []
    columns = {lang: [] for lang in langs}
    for entry in entries:
        for lang in langs:
            word = (entry.get(lang) or {}).get("word", "")
            pronunciation = (entry.get(lang) or {}).get("pronunciation", "")
            columns[lang].append(f"{word} · {pronunciation}")
    return columns


def parse_vocab(columns: dict[str, list[str]]) -> list[dict]:
    rows = []
    for raw in zip_langs(columns):
        entry = {}
        for lang, text in raw.items():
            if " · " not in text:
                raise ValueError(f"Vocabulary line needs 'word · pronunciation': {text}")
            word, pronunciation = text.split(" · ", 1)
            entry[lang] = {"word": word, "pronunciation": pronunciation}
        rows.append(entry)
    return rows


def sentence_body(item: dict) -> str:
    columns = {
        lang: [item["titles"].get(lang, ""), item["sentences"].get(lang, "")]
        for lang in ordered_langs(item["titles"])
    }
    parts = [render_bullets(columns)]
    parts.append(render_section("vocabulary", render_bullets(vocab_columns(item.get("vocabulary") or []))))
    links = []
    for link in item.get("grammarLinks") or []:
        links.append(f"- {link.get('snippetId', '')} · {link.get('label', '')}")
    if links:
        parts.append(render_section("grammar", "\n".join(links)))
    return "\n\n".join(parts)


def load_sentence_file(path: Path) -> dict:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    sections = split_sections(body)
    pair = section_lists(sections[0][1])
    titles = {}
    sentences = {}
    for lang, values in pair.items():
        if len(values) != 2:
            raise ValueError(f"{path} {lang} needs a title bullet and a sentence bullet")
        titles[lang] = values[0]
        sentences[lang] = values[1]
    item = {"titles": titles, "sentences": sentences, "vocabulary": [], "grammarLinks": []}
    for name, lines in sections:
        if name == "vocabulary":
            item["vocabulary"] = parse_vocab(section_lists(lines))
        elif name == "grammar":
            links = []
            for bullet in as_bullets(lines):
                if " · " not in bullet:
                    raise ValueError(f"Grammar link needs 'snippetId · label': {bullet}")
                snippet_id, label = bullet.split(" · ", 1)
                links.append({"snippetId": snippet_id, "label": label})
            item["grammarLinks"] = links
    if meta.get("order"):
        item_order = meta["order"]
        item["_order"] = item_order
    return {key: value for key, value in item.items() if key != "_order"}


def notes_body(note: dict) -> str:
    parts = [
        render_section("title", render_strings(note["titles"])),
        render_section("short", render_strings(note["shortDescriptions"])),
    ]
    for block in note["content"]["explanation"]:
        parts.append(render_section("explanation", render_text(block)))
    rule_columns = {lang: [] for lang in ordered_langs(note["content"]["rules"][0])}
    for rule in note["content"]["rules"]:
        for lang in rule_columns:
            rule_columns[lang].append(rule.get(lang, ""))
    parts.append(render_section("rules", render_bullets(rule_columns)))
    example_columns = {lang: [] for lang in ordered_langs(note["content"]["examples"][0])}
    for example in note["content"]["examples"]:
        for lang in example_columns:
            example_columns[lang].append(example.get(lang, ""))
    parts.append(render_section("examples", render_bullets(example_columns)))
    if note.get("exerciseLinks"):
        lines = []
        for link in note["exerciseLinks"]:
            lines.append(
                "- {exerciseId} · {destinationTitle} · {level} · {exercise} · {source}".format(
                    exerciseId=link.get("exerciseId", ""),
                    destinationTitle=link.get("destinationTitle", ""),
                    level=link.get("level", ""),
                    exercise=link.get("exercise", ""),
                    source=link.get("source", ""),
                )
            )
        parts.append(render_section("links", "\n".join(lines)))
    return "\n\n".join(parts)


def reading_body(reading: dict) -> str:
    parts = [render_section("title", render_strings(reading["titles"][0]))]
    for sentence in reading["sentences"]:
        parts.append(render_section("passage", render_text(sentence)))
    return "\n\n".join(parts)


def questions_body(questions: list) -> str:
    parts = []
    for index, question in enumerate(questions, start=1):
        langs = ordered_langs(question["question"])
        columns = {lang: [] for lang in langs}
        correct = question["correct"]
        for lang in langs:
            columns[lang].append(question["question"].get(lang, ""))
            for option_index, option in enumerate(question["options"]):
                mark = "x" if option_index == correct else " "
                columns[lang].append(f"[{mark}] {option.get(lang, '')}")
            columns[lang].append(question["explanation"][0].get(lang, ""))
        parts.append(render_section(str(index), render_bullets(columns)))
    return "\n\n".join(parts)


def grammar_body(snippet: dict) -> str:
    chunks = []
    for lang in ordered_langs(snippet["content"]):
        body = snippet["content"][lang]
        lines = [f"# {body.get('title', '')}", "", body.get("description", ""), ""]
        for rule in body.get("rules") or []:
            lines.append(f"- {rule}")
        text = "\n".join(lines).rstrip("\n")
        chunks.append(render_text({lang: text}))
    return "\n".join(chunks)


def parse_grammar_text(text: str) -> dict:
    lines = text.split("\n")
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Grammar text needs a # title")
    title = lines[0][2:]
    rest = lines[1:]
    if rest and rest[0] == "":
        rest = rest[1:]
    rules = []
    description_lines = []
    started = False
    for line in rest:
        if line.startswith("- "):
            started = True
            rules.append(line[2:])
        elif started:
            if line == "":
                continue
            raise ValueError(f"Unexpected line after rules: {line}")
        else:
            description_lines.append(line)
    while description_lines and description_lines[-1] == "":
        description_lines.pop()
    description = "\n".join(description_lines)
    return {"title": title, "description": description, "rules": rules}


def load_grammar_file(path: Path, level: str) -> dict:
    meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
    content = {}
    for lang, lines in language_blocks(body.split("\n")).items():
        content[lang] = parse_grammar_text(undent(lines))
    levels = [part.strip() for part in (meta.get("levels") or level).split(",") if part.strip()]
    if level not in levels:
        levels.insert(0, level)
    tags = [part.strip() for part in (meta.get("tags") or "").split(",") if part.strip()]
    return {
        "id": meta.get("id") or path.stem,
        "tags": tags,
        "levels": levels,
        "content": content,
    }


def parse_question_block(columns: dict[str, list[str]]) -> dict:
    question = {}
    options = None
    explanation = {}
    correct = None
    for lang, bullets in columns.items():
        option_rows = []
        for index, bullet in enumerate(bullets):
            match = re.fullmatch(r"\[([ xX])\] (.*)", bullet)
            if match:
                option_rows.append((index, match.group(1), match.group(2)))
        if not option_rows:
            raise ValueError(f"{lang} question has no options")
        first = option_rows[0][0]
        last = option_rows[-1][0]
        question[lang] = "\n".join(bullets[:first])
        explanation[lang] = "\n".join(bullets[last + 1 :])
        lang_options = []
        lang_correct = None
        for offset, (_, mark, text) in enumerate(option_rows):
            lang_options.append(text)
            if mark.lower() == "x":
                if lang_correct is not None:
                    raise ValueError(f"{lang} has more than one correct option")
                lang_correct = offset
        if lang_correct is None:
            raise ValueError(f"{lang} needs one [x] option")
        if options is None:
            options = [{lang: text} for text in lang_options]
            correct = lang_correct
        else:
            if len(lang_options) != len(options) or lang_correct != correct:
                raise ValueError(f"{lang} options do not match the other languages")
            for option, text in zip(options, lang_options):
                option[lang] = text
    return {
        "question": question,
        "options": options or [],
        "correct": correct,
        "explanation": [explanation],
    }


def load_note_dir(topic_dir: Path, level: str, category: str) -> dict:
    notes_meta, notes_text = parse_front_matter((topic_dir / "notes.md").read_text(encoding="utf-8"))
    note = {
        "id": notes_meta.get("id") or topic_dir.name,
        "slug": notes_meta.get("slug") or topic_dir.name,
        "category": (notes_meta.get("category") or category).upper(),
        "order": int(notes_meta.get("order") or 1),
        "titles": {},
        "shortDescriptions": {},
        "content": {"explanation": [], "rules": [], "examples": []},
    }
    for name, lines in split_sections(notes_text):
        if name == "title":
            note["titles"] = section_map(lines)
        elif name == "short":
            note["shortDescriptions"] = section_map(lines)
        elif name == "explanation":
            note["content"]["explanation"].append(section_map(lines))
        elif name == "rules":
            note["content"]["rules"] = zip_langs(section_lists(lines))
        elif name == "examples":
            note["content"]["examples"] = zip_langs(section_lists(lines))
        elif name == "links":
            links = []
            for bullet in as_bullets(lines):
                exercise_id, destination, link_level, exercise, source = bullet.split(" · ")
                links.append(
                    {
                        "exerciseId": exercise_id,
                        "destinationTitle": destination,
                        "level": link_level,
                        "exercise": exercise,
                        "source": source,
                    }
                )
            note["exerciseLinks"] = links

    _, reading_text = parse_front_matter((topic_dir / "reading.md").read_text(encoding="utf-8"))
    reading = {"titles": [], "sentences": []}
    for name, lines in split_sections(reading_text):
        if name == "title":
            reading["titles"].append(section_map(lines))
        elif name == "passage":
            reading["sentences"].append(section_map(lines))
    _, vocab_text = parse_front_matter((topic_dir / "vocabulary.md").read_text(encoding="utf-8"))
    reading["vocabulary"] = parse_vocab(section_lists(split_sections(vocab_text)[0][1]))
    note["reading"] = reading

    _, questions_text = parse_front_matter((topic_dir / "questions.md").read_text(encoding="utf-8"))
    questions = []
    for name, lines in split_sections(questions_text):
        if name.isdigit():
            questions.append(parse_question_block(section_lists(lines)))
    note["exercises"] = questions
    return note


def sentence_files(directory: Path) -> list[Path]:
    files = [path for path in directory.glob("*.md") if path.name != "README.md"]

    def sort_key(path: Path):
        meta, _ = parse_front_matter(path.read_text(encoding="utf-8"))
        return (int(meta.get("order") or 0), path.name)

    return sorted(files, key=sort_key)


def build_json(content_root: Path, out_root: Path) -> dict:
    out_root.mkdir(parents=True, exist_ok=True)
    counts = {"exercises": 0, "exercise_items": 0, "starter_items": 0, "notes": 0, "snippets": 0}

    exercise_root = content_root / "Exercise"
    for level in LEVELS:
        level_dir = exercise_root / level
        if not level_dir.is_dir():
            continue
        for type_dir in sorted(path for path in level_dir.iterdir() if path.is_dir()):
            lessons = sorted(
                (path for path in type_dir.iterdir() if path.is_dir() and path.name.startswith("lesson_")),
                key=lambda path: int(path.name.split("_", 1)[1]),
            )
            for lesson in lessons:
                set_no = int(lesson.name.split("_", 1)[1])
                items = []
                for path in sentence_files(lesson):
                    try:
                        items.append(load_sentence_file(path))
                    except Exception as exc:
                        raise RuntimeError(f"{path}: {exc}") from exc
                write_json(
                    out_root / "exercise" / level / type_dir.name / str(set_no) / f"{type_dir.name}-{level}-{set_no}.json",
                    items,
                )
                counts["exercises"] += 1
                counts["exercise_items"] += len(items)

    starter_root = content_root / "Starter-Kit"
    if starter_root.is_dir():
        chapters = []
        for path in starter_root.iterdir():
            match = re.match(r"^(\d+)_", path.name) if path.is_dir() else None
            if match:
                chapters.append((int(match.group(1)), path))
        for number, chapter_dir in sorted(chapters):
            items = []
            for path in sentence_files(chapter_dir):
                try:
                    items.append(load_sentence_file(path))
                except Exception as exc:
                    raise RuntimeError(f"{path}: {exc}") from exc
            write_json(out_root / "starter-kit" / str(number) / f"starter-kit-{number}.json", items)
            counts["starter_items"] += len(items)

    notes_root = content_root / "Notes"
    for level in LEVELS:
        level_dir = notes_root / level
        if not level_dir.is_dir():
            continue
        for category_dir in sorted(path for path in level_dir.iterdir() if path.is_dir()):
            for topic in sorted(path for path in category_dir.iterdir() if path.is_dir()):
                try:
                    note = load_note_dir(topic, level, category_dir.name)
                except Exception as exc:
                    raise RuntimeError(f"{topic}: {exc}") from exc
                write_json(out_root / "notes" / level / note["slug"] / "note.json", [note])
                counts["notes"] += 1

    snippets = []
    grammar_root = content_root / "Grammar-Snippets"
    for level in LEVELS:
        level_dir = grammar_root / level
        if not level_dir.is_dir():
            continue
        files = [path for path in level_dir.glob("*.md") if path.name != "README.md"]

        def grammar_key(path: Path):
            meta, _ = parse_front_matter(path.read_text(encoding="utf-8"))
            return (int(meta.get("index") or 0), path.name)

        for path in sorted(files, key=grammar_key):
            try:
                meta, _ = parse_front_matter(path.read_text(encoding="utf-8"))
                snippets.append((int(meta.get("index") or 0), load_grammar_file(path, level)))
            except Exception as exc:
                raise RuntimeError(f"{path}: {exc}") from exc
    snippets.sort(key=lambda pair: pair[0])
    write_json(out_root / "grammar-snippets.json", [snippet for _, snippet in snippets])
    counts["snippets"] = len(snippets)
    return counts


def _unique_name(directory: Path, stem: str) -> str:
    candidate = stem
    number = 2
    while (directory / f"{candidate}.md").exists():
        candidate = f"{stem}_{number}"
        number += 1
    return candidate


def export_from_studio(studio: Path, grammar_seed: Path, content_root: Path) -> dict:
    counts = {"exercise_items": 0, "starter_items": 0, "notes": 0, "snippets": 0}
    for level_dir in (studio / "exercise").iterdir() if (studio / "exercise").is_dir() else []:
        if not level_dir.is_dir():
            continue
        for type_dir in sorted(path for path in level_dir.iterdir() if path.is_dir()):
            for set_dir in sorted(
                (path for path in type_dir.iterdir() if path.is_dir() and path.name.isdigit()),
                key=lambda path: int(path.name),
            ):
                items = read_json(next(set_dir.glob("*.json")))
                dest = content_root / "Exercise" / level_dir.name / type_dir.name / f"lesson_{int(set_dir.name):02d}"
                dest.mkdir(parents=True, exist_ok=True)
                for index, item in enumerate(items, start=1):
                    stem = _unique_name(dest, f"{index:02d}_{slugify(item['titles']['en'], 'sentence')}")
                    (dest / f"{stem}.md").write_text(
                        render_file({"order": index}, sentence_body(item)),
                        encoding="utf-8",
                    )
                    counts["exercise_items"] += 1

    for number, name in CHAPTERS.items():
        src = studio / "starter-kit" / str(number) / f"starter-kit-{number}.json"
        if not src.is_file():
            continue
        dest = content_root / "Starter-Kit" / f"{number:02d}_{name}"
        dest.mkdir(parents=True, exist_ok=True)
        for index, item in enumerate(read_json(src), start=1):
            stem = _unique_name(dest, f"{index:02d}_{slugify(item['titles']['en'], 'sentence')}")
            (dest / f"{stem}.md").write_text(
                render_file({"order": index}, sentence_body(item)),
                encoding="utf-8",
            )
            counts["starter_items"] += 1

    for level_dir in sorted(path for path in (studio / "notes").iterdir() if path.is_dir()):
        for slug_dir in sorted(path for path in level_dir.iterdir() if path.is_dir()):
            note_path = slug_dir / "note.json"
            if not note_path.is_file():
                continue
            note = read_json(note_path)[0]
            topic = (
                content_root
                / "Notes"
                / level_dir.name
                / str(note["category"]).lower()
                / f"topic_{int(note.get('order') or 1):02d}_{slug_dir.name.replace('-', '_')}"
            )
            topic.mkdir(parents=True, exist_ok=True)
            reading = dict(note["reading"])
            vocabulary = reading.pop("vocabulary")
            (topic / "notes.md").write_text(
                render_file(
                    {
                        "id": note["id"],
                        "slug": note["slug"],
                        "category": note["category"],
                        "order": note["order"],
                    },
                    notes_body(note),
                ),
                encoding="utf-8",
            )
            (topic / "reading.md").write_text(render_file(None, reading_body(reading)), encoding="utf-8")
            (topic / "vocabulary.md").write_text(
                render_file(None, render_bullets(vocab_columns(vocabulary))),
                encoding="utf-8",
            )
            (topic / "questions.md").write_text(render_file(None, questions_body(note["exercises"])), encoding="utf-8")
            counts["notes"] += 1

    snippets = read_json(grammar_seed)
    grouped: dict[str, list[tuple[int, dict]]] = {level: [] for level in LEVELS}
    for index, snippet in enumerate(snippets):
        level = (snippet.get("levels") or ["A1"])[0]
        grouped.setdefault(level, []).append((index, snippet))
    for level, pairs in grouped.items():
        dest = content_root / "Grammar-Snippets" / level
        dest.mkdir(parents=True, exist_ok=True)
        running = 1
        for index, snippet in pairs:
            stem = _unique_name(dest, f"{running:02d}_{slugify(snippet['content']['en']['title'], 'snippet')}")
            running += 1
            tags = ", ".join(snippet.get("tags") or [])
            levels = ", ".join(snippet.get("levels") or [])
            (dest / f"{stem}.md").write_text(
                render_file(
                    {"id": snippet["id"], "index": index, "levels": levels, "tags": tags},
                    grammar_body(snippet),
                ),
                encoding="utf-8",
            )
            counts["snippets"] += 1
    return counts
