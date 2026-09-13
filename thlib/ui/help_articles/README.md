# Help articles

Built-in Help reads these UTF-8 Markdown files directly. Each topic uses the
filename `<topic>.<language>.md`, for example `checkin.en.md` and
`checkin.ru.md`. If a translation is missing, the English file is shown.

An article starts with optional metadata and one level-one title:

```markdown
---
group: Workflows
icon: publish
order: 15
---
# Check-in

Write normal **Markdown** here. Lists, links, tables, quotes, and fenced code
blocks are supported. Relative image and link paths resolve from the article
file.
```

`group` labels the topic list, `icon` is a Handler icon name, and `order`
controls navigation order. The Help window can open the active source file in
the system editor and reload edits without restarting TACTIC Handler.
