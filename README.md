# DarkLab

DarkLab is a free, open-source desktop photo application for photographers who already work the Lightroom Classic way: import a shoot, cull it, develop the selects, and hand the result off. The seven modules are Library, Develop, Map, Book, Slideshow, Print, and Web.

The promise is that workflow, on a local catalog, without a subscription. It is not a promise to open an Adobe catalog or to match Adobe's rendering pixel for pixel.

## Status

`main` can create and reopen a `.darklab` catalog. The window has an import dialog, a Library browser, and a Develop panel shell. Map, Book, Slideshow, Print, and Web are empty modules.

| | |
| --- | --- |
| Brief | [`brief.md`](_bmad-output/planning-artifacts/briefs/brief-DarkLab-2026-10-10/brief.md) |
| PRD | [`prd.md`](_bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/prd.md) |
| Architecture | [`architecture.md`](_bmad-output/planning-artifacts/architecture.md) |
| Epics | [`epics.md`](_bmad-output/planning-artifacts/epics.md) |
| Process | [`docs/pdlc.md`](docs/pdlc.md) |
| Board | [DarkLab project](https://github.com/users/fgalyasz/projects/11) |

The first milestone is one shoot: import, cull, basic develop, export, with original files left unchanged. Collections, the rest of Develop, Map, Book, Slideshow, Print, Web, and people tags are specified and come after that.

## Run

CPython 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Development

Features and user-visible fixes follow [`docs/pdlc.md`](docs/pdlc.md). Domain code belongs in `src/catalog`, `src/importing`, `src/develop`, `src/exporting`, and `src/imaging`. Widgets stay in `src/ui` and do not own catalog rules.

```bash
python -m unittest discover -s tests
```

## License

MIT. See [LICENSE](LICENSE).
