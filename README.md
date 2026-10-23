<div align="center">

# LIONLINGO

<img src="docs/lion.png" alt="LionLingo" width="180">

# Curriculum

---

**Open curriculum for the LionLingo course, written as plain markdown.**

Eight languages, from first greetings through C2. Exercises, notes, the starter kit, and grammar notes live in this repository.

*By the LionLingo team.*

<img alt="Written in Markdown" src="https://img.shields.io/badge/written_in-Markdown-444444">
<img alt="Languages" src="https://img.shields.io/badge/languages-en_%C2%B7_fr_%C2%B7_de_%C2%B7_am_%C2%B7_ar_%C2%B7_es_%C2%B7_ja_%C2%B7_zh-2ea043">
<img alt="Levels A1 to C2" src="https://img.shields.io/badge/levels-A1_–_C2-2ea043">
<img alt="CC BY 4.0" src="https://img.shields.io/badge/license-CC_BY_4.0-444444">

<br>

<a href="https://discord.gg/H5tMtJwyGV"><img alt="Join us on Discord" src="https://img.shields.io/badge/Join_us_on_Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white"></a>

<br>

[lionlingo.me](https://lionlingo.me) · [Discord](https://discord.gg/H5tMtJwyGV) · [YouTube](https://www.youtube.com/@lionlingo) · [License](LICENSE)

</div>

## Catalogue

| | |
|---|---|
| Languages | English, French, German, Amharic, Arabic, Spanish, Japanese, Simplified Chinese |
| Levels | A1, A2, B1, B2, C1, C2 |
| Exercise sentences | 690, in 75 lessons |
| Starter-kit sentences | 242, in 12 chapters |
| Note lessons | 89 |
| Grammar snippets | 89 |

## Repository

```text
Exercise/A1/vocabulary/lesson_01/01_morning.md
Notes/A1/vocabulary/topic_01_greetings_and_introductions/
Starter-Kit/essentials_01/01_hi_how_are_you.md
Grammar-Snippets/A1/01_subject_be.md
```

| Path | Unit of authorship |
|---|---|
| `Exercise/` | One practice sentence |
| `Starter-Kit/` | One practice sentence |
| `Notes/` | One lesson, in four files: `reading.md`, `notes.md`, `vocabulary.md`, `questions.md` |
| `Grammar-Snippets/` | One grammar note, linked from exercises by snippet id |

Exercise types are `vocabulary`, `grammar`, `letters`, `sentences`, and `verbs`. Note categories are `grammar`, `vocabulary`, `culture`, and `conversation`.

## Authoring

A language label introduces that language. For a practice sentence, the first bullet is the prompt and the second is the sentence to practice.

```markdown
en:
- I'm buying a coffee.
- I buy a coffee.

fr:
- J'achète un café.
- J'achète un café.
```

`## vocabulary` lists `word · pronunciation` under each language. `## grammar` lists `snippet-id · label`.

A note follows the same arrangement. `notes.md` carries the title, short description, explanation, rules, and examples. `reading.md` carries the passages. `questions.md` marks the correct option with `[x]`.

A reading passage or a grammar description is indented beneath its language label. The front matter of a note records its id, slug, category, and order. The front matter of a grammar snippet records its id, levels, and tags.

## Contributing

Open a branch and a pull request. `main` accepts pull requests only.

A pull request checks that the markdown converts to JSON. Merging does not send lessons to the content service. Maintainers publish the changed lessons afterward.

## License

[Creative Commons Attribution 4.0 International](LICENSE).
