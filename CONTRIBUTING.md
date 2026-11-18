# Contributing

Suggest tools with a clear use case and a public official website or repository. Include what the tool helps people do. Link directly to the official page and keep descriptions to one sentence.

## Add or update a tool

1. Edit `data/catalog.json` with the tool's stable ID, name, category ID, and official HTTPS URL.
2. Add or update the description under that ID in every `data/locales/*.json` file. Keep the meaning consistent and write naturally for each language.
3. Run the commands below, then include both the data and the updated Markdown pages in your pull request.

## Add a language

Register a lowercase language tag and its display name in `data/catalog.json`. Copy the structure of `data/locales/en.json` to a file named for that tag. Translate the page labels, category names, and every tool description while keeping the keys intact. Regenerate the pages to add the new language to the navigation.

Use Python 3.10 or later.

```sh
python3 scripts/build_catalog.py
python3 scripts/build_catalog.py --check
python3 -B -m unittest discover -s tests
```
