"""Auto-generate API reference pages for mkdocstrings.

This script is run by ``mkdocs-gen-files`` during the docs build. It walks
every Python module under ``src/oracle_paper`` and creates a corresponding
markdown stub under ``reference/`` so mkdocstrings can render the API docs.
"""

from pathlib import Path

import mkdocs_gen_files

# Files and folders that should not appear in the API reference.
SKIP_FILES = ["bilevel_model.jl"]
SKIP_FOLDERS = ["logging_tools"]

# Root of the oracle_paper package
src_dir = Path("src/oracle_paper")

for path in src_dir.rglob("*.py"):
    # --- Skip anything marked for exclusion ---
    if path.name in SKIP_FILES:
        continue

    if any(folder in path.parts for folder in SKIP_FOLDERS):
        continue

    # Skip private modules (e.g. ``_julia.py``) but keep ``__init__.py``
    if path.name.startswith("_") and path.name != "__init__.py":
        continue

    # --- Build the output path ---
    # Turn ``src/oracle_paper/models/ps_hlp.py`` into
    # ``reference/oracle_paper/models/ps_hlp.md``
    module_path = path.relative_to(".").with_suffix("")
    doc_path = path.relative_to(".").with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    # ``__init__.py`` files become ``index.md`` for that directory
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")

    # Write the mkdocstrings directive. The leading ``src.`` is stripped
    # because mkdocstrings resolves with ``paths: [src]`` in mkdocs.yml.
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        if ident.startswith("src."):
            ident = ident[len("src."):]
        fd.write(f"::: {ident}")
