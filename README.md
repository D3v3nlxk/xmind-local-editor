# Xmind Local Editor

An agent skill for reading and improving saved Xmind mind maps with local Python tools. The assistant handles inspection, planning, editing, and validation from natural-language requests.

## Features

- Inspect sheets, topics, hierarchy, and notes.
- Search topic titles and read individual subtrees.
- Rename topics and sheets.
- Add child topics or complete nested branches.
- Preview batch edits before writing, with stable generated IDs and numbered operations.
- Detect source-file changes using SHA-256.
- Save edits to a new file and record changes in a companion JSON file.

## Requirements

Python 3 with its standard library. No Xmind cloud connection or third-party Python packages are required by the editing tools.

## Usage

Install this directory as a skill in your assistant's supported skill location. The entry point is [SKILL.md](SKILL.md).

Example request:

> Read my project.xmind, expand the testing branch with a release checklist, and save an edited copy.

The assistant invokes the bundled tools; you do not need to prepare commands or operation JSON manually.

For direct command-line use:

```sh
python3 scripts/xmind.py inspect /path/to/map.xmind
python3 scripts/xmind.py inspect /path/to/map.xmind --query testing
python3 scripts/xmind.py plan /path/to/map.xmind --request request.json
python3 scripts/xmind.py edit /path/to/map.xmind --request request.json --output /path/to/map-edited.xmind
```

See [SKILL.md](SKILL.md) for the request format and supported operations.

## Preservation and recovery

Edits preserve the source file and write a new archive. Successful edits also attempt to create `<output>.changes.json`, recording the source identity and applied changes. Recovery uses the retained original file; per-operation undo is not implemented. If writing the change record fails, the tool reports that the edited map was still saved.

## Limitations

- Supports modern ZIP-based `.xmind` files containing `content.json`.
- Does not control the live Xmind window or read unsaved changes.
- Does not support moving or deleting topics, editing relationships or styles, or rich-note editing.
- XML-only and encrypted documents are unsupported.
- Preserved thumbnails may be stale; archive validation does not establish visual rendering compatibility.
- The tool does not provide Xmind subscription features or access to its hosted AI services.

Static research on the shipped assistant protocol is documented in [references/protocol.md](references/protocol.md). Those observations do not constitute a supported local Xmind API.

This is an independent project, not an official Xmind product.
