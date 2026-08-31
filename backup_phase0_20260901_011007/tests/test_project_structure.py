"""Smoke tests for the official SpeechScribe application structure."""
from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_python(relative_path: str) -> ast.Module:
    path = PROJECT_ROOT / relative_path
    assert path.is_file(), f"Missing required file: {relative_path}"
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_required_packages_have_valid_initializers():
    for package in ("src", "gui", "tests"):
        initializer = PROJECT_ROOT / package / "__init__.py"
        assert initializer.is_file(), f"Missing package initializer: {initializer}"


def test_primary_ui_defines_application_class():
    module = parse_python("speechscribe_pro_ui.py")
    class_names = {node.name for node in ast.walk(module) if isinstance(node, ast.ClassDef)}
    assert "SpeechScribeUI" in class_names


def test_official_launcher_targets_professional_ui():
    module = parse_python("run_app.py")
    source = (PROJECT_ROOT / "run_app.py").read_text(encoding="utf-8")
    assert "speechscribe_pro_ui.py" in source
    assert "SpeechScribeUI" in source
    assert any(isinstance(node, ast.If) for node in ast.walk(module))


def test_core_modules_are_syntax_valid():
    for relative_path in (
        "src/audio_processor.py",
        "src/clusterer.py",
        "src/text_generator.py",
        "src/transcriber.py",
        "src/utils.py",
    ):
        parse_python(relative_path)
