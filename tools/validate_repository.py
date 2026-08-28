#!/usr/bin/env python3
"""Validate repository structure, notebooks, paths, and publishable content."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_SIZE = 10 * 1024 * 1024

REQUIRED_PATHS = (
    Path("README.md"),
    Path(".gitignore"),
    Path("requirements.txt"),
    Path("data/README.md"),
    Path("models/README.md"),
    Path("notebooks/01_arat5_128.ipynb"),
    Path("notebooks/02_arat5_256.ipynb"),
    Path("outputs/recorded_training_metrics.csv"),
    Path("outputs/recorded_evaluation.csv"),
    Path("tools/validate_repository.py"),
    Path(".github/workflows/validate.yml"),
)

FORBIDDEN_DIRECTORY_NAMES = {
    ".git",
    ".ipynb_checkpoints",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "env",
    "mlruns",
    "runs",
    "venv",
    "wandb",
}

FORBIDDEN_FILE_NAMES = {
    ".DS_Store",
    ".env",
    "Thumbs.db",
    "kaggle.json",
}

FORBIDDEN_SUFFIXES = {
    ".7z",
    ".bin",
    ".ckpt",
    ".h5",
    ".keras",
    ".onnx",
    ".parquet",
    ".pt",
    ".pth",
    ".rar",
    ".safetensors",
    ".tar",
    ".tgz",
    ".tflite",
    ".xlsx",
    ".xls",
    ".zip",
}

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "Hugging Face token": re.compile(r"\bhf_[A-Za-z0-9]{20,}\b"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b"),
    "assigned secret": re.compile(
        r"(?i)\b(?:api[_-]?key|client[_-]?secret|access[_-]?token|password)"
        r"\b\s*[:=]\s*[\"'][^\"']{8,}[\"']"
    ),
}

LOCAL_PATH_PATTERNS = {
    "Windows user path": re.compile(r"(?i)\b[A-Z]:[\\/](?:Users|Documents and Settings)[\\/]"),
    "Colab path": re.compile(r"(?<![A-Za-z0-9_])/content/"),
    "Kaggle path": re.compile(r"(?<![A-Za-z0-9_])/kaggle/"),
    "Unix home path": re.compile(r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s]+/"),
}

TEXT_SUFFIXES = {
    ".csv",
    ".ipynb",
    ".md",
    ".py",
    ".txt",
    ".yml",
    ".yaml",
}


def repository_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    )


def add_error(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def validate_required_paths(errors: list[str]) -> None:
    for relative in REQUIRED_PATHS:
        if not (ROOT / relative).is_file():
            errors.append(f"Missing required file: {relative}")


def validate_file_inventory(files: list[Path], errors: list[str]) -> None:
    for path in files:
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            add_error(errors, path, "symbolic links are not allowed")
        if any(part in FORBIDDEN_DIRECTORY_NAMES for part in relative.parts[:-1]):
            add_error(errors, path, "file is inside a generated or machine-specific directory")
        if path.name in FORBIDDEN_FILE_NAMES:
            add_error(errors, path, "forbidden local or credential filename")
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            add_error(errors, path, "forbidden archive, dataset, or checkpoint type")
        if path.suffix.lower() == ".csv" and relative.parts[0] != "outputs":
            add_error(errors, path, "CSV datasets must remain outside Git")
        if path.stat().st_size > MAX_FILE_SIZE:
            add_error(errors, path, f"file exceeds {MAX_FILE_SIZE // (1024 * 1024)} MB")


def validate_text(path: Path, text: str, errors: list[str]) -> None:
    if "\u2014" in text:
        add_error(errors, path, "contains an em dash character")
    for label, pattern in SECRET_PATTERNS.items():
        if pattern.search(text):
            add_error(errors, path, f"possible {label}")


def validate_notebook(path: Path, errors: list[str]) -> None:
    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        add_error(errors, path, f"invalid notebook JSON: {exc}")
        return

    if notebook.get("nbformat") != 4 or not isinstance(notebook.get("cells"), list):
        add_error(errors, path, "unexpected notebook structure")
        return

    for index, cell in enumerate(notebook["cells"]):
        source = "".join(cell.get("source", []))
        for label, pattern in LOCAL_PATH_PATTERNS.items():
            if pattern.search(source):
                add_error(errors, path, f"cell {index} contains a {label}")
        if cell.get("cell_type") == "code":
            try:
                ast.parse(source or "\n")
            except SyntaxError as exc:
                add_error(errors, path, f"cell {index} has invalid Python syntax: {exc.msg}")

        output_text = json.dumps(cell.get("outputs", []), ensure_ascii=False)
        for label, pattern in LOCAL_PATH_PATTERNS.items():
            if pattern.search(output_text):
                add_error(errors, path, f"cell {index} output contains a {label}")


def validate_python(path: Path, errors: list[str]) -> None:
    try:
        ast.parse(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, SyntaxError) as exc:
        add_error(errors, path, f"invalid Python syntax: {exc}")


def validate_readme_images(errors: list[str]) -> None:
    readme = ROOT / "README.md"
    if not readme.is_file():
        return
    text = readme.read_text(encoding="utf-8")
    for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
        clean_target = target.split()[0].strip("<>")
        if re.match(r"^(?:https?|data):", clean_target):
            continue
        if not (ROOT / clean_target).is_file():
            errors.append(f"README.md: missing image target {clean_target}")


def validate_dataset(errors: list[str]) -> None:
    configured = os.environ.get(
        "ARABIC_PARAPHRASE_DATA",
        str(ROOT / "data" / "paraphrase_data.csv"),
    )
    dataset_path = Path(configured).expanduser()
    if not dataset_path.is_absolute():
        dataset_path = (ROOT / dataset_path).resolve()
    if not dataset_path.is_file():
        errors.append(f"Dataset file not found: {dataset_path}")
        return

    try:
        with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or [])
            missing = {"source", "destination"}.difference(columns)
            if missing:
                errors.append(
                    "Dataset is missing required columns: " + ", ".join(sorted(missing))
                )
            if next(reader, None) is None:
                errors.append("Dataset contains no rows")
    except (OSError, UnicodeError, csv.Error) as exc:
        errors.append(f"Dataset could not be read: {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-dataset",
        action="store_true",
        help="also verify the external CSV and its required columns",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    files = repository_files()

    validate_required_paths(errors)
    validate_file_inventory(files, errors)

    for path in files:
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {".gitignore"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                add_error(errors, path, f"expected UTF-8 text: {exc}")
                continue
            validate_text(path, text, errors)
        if path.suffix.lower() == ".ipynb":
            validate_notebook(path, errors)
        elif path.suffix.lower() == ".py":
            validate_python(path, errors)

    validate_readme_images(errors)
    if args.check_dataset:
        validate_dataset(errors)

    if errors:
        print("Repository validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Repository validation passed for {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
