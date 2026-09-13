# QML interface localization

The application interface uses English source text and Qt `qsTr()` bindings. The
active language is selected in **Configuration → Global → Language** and is
stored through `env_read_config` / `env_write_config` in `ui_main/ui_settings` under
`appearance/language`.

`thlib/ui/localization.py` installs the selected source-text catalog and asks
the live QML engine to retranslate, so changing the language does not recreate
windows or discard their state. English is the source/fallback language.
Russian translations are stored in `thlib/ui/translations/ru.json`.
Missing catalog entries always fall back to the English source text. A missing
translation must never produce an empty label, menu item, tooltip, or title.

Built-in Help article content is intentionally separate from this catalog.
`thlib/ui/help_articles/<topic>.<language>.md` contains editable Markdown for
each language, and Help falls back to the English article when a localized file
is absent. Only the Help viewer's buttons, search field, and empty states use
`qsTr()`.

Rules for new UI text:

- write the source string in English;
- wrap user-facing QML literals in `qsTr()`;
- wrap controller-backed application messages in `qsTr()` at the QML
  presentation boundary as well; raw server data and diagnostic details still
  fall back unchanged when they are not catalog keys;
- add the exact source string to every shipped language catalog;
- do not translate server data, project names, user names, paths, codes, or
  script contents;
- use placeholders in the source text instead of concatenating translated
  sentence fragments;
- keep language-independent values (`en`, `ru`, enum keys) separate from their
  translated labels.

`tests/test_localization.py` validates literal `qsTr()` sources and dynamic
labels supplied by the action registry, sObject context menus, window registry,
dock defaults, and QML action models. A new language therefore requires a
catalog file, a `LANGUAGES` entry, and its locale mapping.

The signed-out path is covered by a real QML creation test. Authentication
guidance and normalized login failures must be translated even though their
source text comes from the connection controller rather than a QML literal.
