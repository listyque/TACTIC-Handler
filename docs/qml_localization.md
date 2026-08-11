# QML interface localization

The modern interface uses English source text and Qt `qsTr()` bindings. The
active language is selected in **Configuration → Global → Language** and is
stored in the shared `TACTIC-Handler/modern-qml` settings under
`appearance/language`.

`modern_ui/localization.py` installs the selected source-text catalog and asks
the live QML engine to retranslate, so changing the language does not recreate
windows or discard their state. English is the source/fallback language.
Russian translations are stored in `modern_ui/translations/ru.json`.
Missing catalog entries always fall back to the English source text. A missing
translation must never produce an empty label, menu item, tooltip, or title.

Rules for new UI text:

- write the source string in English;
- wrap user-facing QML literals in `qsTr()`;
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
