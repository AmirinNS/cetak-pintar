"""Tests for the CetakPintar command-line interface (Milestone B2)."""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader

from cetak_pintar import limiter
from cli import main
from modules.render.pdf import render
from modules.spec import parse_spec

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("seed_args", [[], ["--seed", ""], ["--seed", " \t "]])
def test_blank_or_absent_seed_resolved_once_and_reproduces_web_pdf(
    seed_args, tmp_path, capsys, monkeypatch, client,
):
    calls = []

    def pick_seed(upper):
        calls.append(upper)
        return 1234567

    monkeypatch.setattr("cli.secrets.randbelow", pick_seed)
    output = tmp_path / "resolved.pdf"
    assert main(["--topics", "add", "--pages", "1", *seed_args, "-o", str(output)]) == 0
    query = capsys.readouterr().out.strip()
    assert "&seed=1234567&" in query
    assert calls == [2147483648]
    spec, errors = parse_spec(query)
    assert errors == []
    assert render(spec) == output.read_bytes()
    limiter.reset()
    response = client.get(f"/cetak?{query}")
    assert response.status_code == 200
    assert response.data == output.read_bytes()
    assert calls == [2147483648]


@pytest.mark.parametrize("pages", [1, 2, 4, 20])
@pytest.mark.parametrize("table_count", [1, 12])
def test_reference_only_cli_page_budget(pages, table_count, tmp_path, capsys):
    output = tmp_path / "reference.pdf"
    code = main([
        "--topics", "sifir_ref", "--pages", str(pages), "--seed", "42",
        "--sifir-tables", ",".join(str(n) for n in range(1, table_count + 1)),
        "-o", str(output),
    ])
    required_pages = (table_count + 5) // 6
    if pages == required_pages:
        assert code == 0
        assert len(PdfReader(output).pages) == required_pages
    else:
        assert code == 2
        expected = "below_minimum" if pages < required_pages else "reference_pages_mismatch"
        assert f"pages: {expected}" in capsys.readouterr().err
        assert not output.exists()


def test_layout_failure_exits_two(tmp_path, capsys, monkeypatch):
    def invalid_layout(spec):
        raise ValueError("invalid layout")

    monkeypatch.setattr("cli.render", invalid_layout)
    output = tmp_path / "invalid.pdf"
    assert main(["--topics", "add", "--seed", "1", "-o", str(output)]) == 2
    assert "error: invalid layout" in capsys.readouterr().err
    assert not output.exists()


def test_writes_pdf_and_prints_canonical_query(tmp_path, capsys) -> None:
    """A valid invocation writes a PDF and prints the canonical query on stdout."""
    output = tmp_path / "sheet.pdf"

    code = main(["--topics", "grid,add,sub", "--pages", "3", "--seed", "7", "-o", str(output)])

    assert code == 0
    assert output.read_bytes()[:5] == b"%PDF-"
    assert len(PdfReader(io.BytesIO(output.read_bytes())).pages) == 6

    query = capsys.readouterr().out.strip()
    assert query == (
        "t=grid,add,sub&pages=3&lang=ms&ans=1&seed=7"
        "&grid_start=1&grid_blanks=30&add_digits=1&add_regroup=0&sub_digits=1&sub_borrow=0"
    )


def test_missing_seed_is_resolved_and_printed(tmp_path, capsys) -> None:
    """A missing seed is picked once, lands in the spec, and is printed."""
    output = tmp_path / "seeded.pdf"

    code = main(["--topics", "grid", "-o", str(output)])

    assert code == 0
    spec, errors = parse_spec(capsys.readouterr().out.strip())
    assert errors == []
    assert spec is not None
    assert spec.seed is not None
    assert 0 <= spec.seed <= 2147483647


def test_preset_t1_renders_and_can_be_overridden(tmp_path, capsys) -> None:
    """Preset t1 renders, and an explicit --topics overrides the preset topics."""
    output = tmp_path / "preset.pdf"

    code = main(["--preset", "t1", "--seed", "123", "-o", str(output)])

    assert code == 0
    assert output.read_bytes()[:5] == b"%PDF-"
    assert capsys.readouterr().out.strip() == (
        "t=grid,count,add,sub&pages=4&lang=ms&ans=1&seed=123"
        "&grid_start=1&grid_blanks=30&count_max=10&count_shapes=star,circle,apple,fish,flower"
        "&add_digits=1&add_regroup=0&sub_digits=1&sub_borrow=0"
    )

    code = main(["--preset", "t1", "--topics", "add", "--seed", "4", "-o", str(output)])

    assert code == 0
    query = capsys.readouterr().out.strip()
    assert query == "t=add&pages=4&lang=ms&ans=1&seed=4&add_digits=1&add_regroup=0"


def test_no_answers_and_language_flags(tmp_path, capsys) -> None:
    """--no-answers drops the answer sheets and --lang reaches the spec."""
    output = tmp_path / "en.pdf"

    code = main(
        [
            "--topics",
            "add",
            "--pages",
            "1",
            "--lang",
            "en",
            "--no-answers",
            "--seed",
            "5",
            "-o",
            str(output),
        ]
    )

    assert code == 0
    query = capsys.readouterr().out.strip()
    assert "lang=en" in query
    assert "ans=0" in query
    assert len(PdfReader(io.BytesIO(output.read_bytes())).pages) == 1

    with_answers = tmp_path / "ms.pdf"
    assert main(["--topics", "add", "--pages", "1", "--seed", "5", "-o", str(with_answers)]) == 0
    assert len(PdfReader(io.BytesIO(with_answers.read_bytes())).pages) == 2


def test_printed_query_regenerates_identical_pdf(tmp_path, capsys) -> None:
    """Reparsing the printed query renders byte-identical PDF bytes."""
    first = tmp_path / "first.pdf"
    argv = ["--topics", "grid,add,sub", "--pages", "5", "--seed", "98765"]

    assert main([*argv, "-o", str(first)]) == 0
    query = capsys.readouterr().out.strip()

    spec, errors = parse_spec(query)
    assert errors == []
    assert spec is not None
    assert render(spec) == first.read_bytes()

    second = tmp_path / "second.pdf"
    assert main([*argv, "-o", str(second)]) == 0
    assert second.read_bytes() == first.read_bytes()


def test_out_of_range_option_reports_field_message(tmp_path, capsys) -> None:
    """A bad option exits 2 with the field and message key on stderr, and writes nothing."""
    output = tmp_path / "bad.pdf"

    code = main(["--topics", "add", "--add-digits", "5", "-o", str(output)])

    assert code == 2
    assert "add_digits: out_of_range" in capsys.readouterr().err
    assert not output.exists()


def test_impossible_combination_reports_field_message(tmp_path, capsys) -> None:
    """Borrowing with one digit is rejected at parse time, not during generation."""
    output = tmp_path / "bad.pdf"

    code = main(["--topics", "sub", "--sub-borrow", "--sub-digits", "1", "-o", str(output)])

    assert code == 2
    assert "sub_borrow: borrow_requires_two_digits" in capsys.readouterr().err
    assert not output.exists()


def test_pages_below_minimum_reports_field_message(tmp_path, capsys) -> None:
    """Fewer pages than the selected topics need is a field error."""
    output = tmp_path / "bad.pdf"

    code = main(["--topics", "grid,add,sub", "--pages", "2", "-o", str(output)])

    assert code == 2
    assert "pages: below_minimum" in capsys.readouterr().err


def test_invalid_seed_reports_field_message(tmp_path, capsys) -> None:
    """A non-integer seed is reported by the spec layer, not by argparse."""
    output = tmp_path / "bad.pdf"

    code = main(["--topics", "grid", "--seed", "abc", "-o", str(output)])

    assert code == 2
    assert "seed: invalid_integer" in capsys.readouterr().err


def test_all_topics_render_in_single_cli_call(tmp_path, capsys) -> None:
    """Every topic renders in a single CLI call without errors."""
    output = tmp_path / "all_topics.pdf"

    code = main(
        [
            "--topics",
            "grid,count,add,sub,sifir_ref,sifir,div",
            "--pages",
            "7",
            "--seed",
            "42",
            "-o",
            str(output),
        ]
    )

    assert code == 0
    assert output.exists()
    assert output.read_bytes()[:5] == b"%PDF-"
    # 7 content sheets (1 per topic: 6 practice + 1 sifir_ref) + 6 answer sheets = 13 pages
    reader = PdfReader(io.BytesIO(output.read_bytes()))
    assert len(reader.pages) == 13


def test_unwritable_output_path_exits_with_message(tmp_path, capsys) -> None:
    """An output path that cannot be written reports the error instead of crashing."""
    code = main(["--topics", "grid", "--seed", "1", "-o", str(tmp_path / "missing" / "x.pdf")])

    assert code == 2
    assert "cannot write" in capsys.readouterr().err


def test_module_entrypoint_exit_code(tmp_path) -> None:
    """`python cli.py` propagates the exit code of main()."""
    proc = subprocess.run(
        [
            sys.executable,
            "cli.py",
            "--topics",
            "add",
            "--add-digits",
            "9",
            "-o",
            str(tmp_path / "x.pdf"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 2
    assert "add_digits: out_of_range" in proc.stderr


def test_cli_alphabet_topics_with_abc_case(tmp_path, capsys) -> None:
    """CLI writes a PDF with --abc-case lower --topics trace,missing."""
    output = tmp_path / "abc_sheet.pdf"
    code = main([
        "--topics", "trace,missing",
        "--abc-case", "lower",
        "--missing-blanks", "2",
        "--pages", "2",
        "--seed", "1",
        "-o", str(output),
    ])
    assert code == 0
    assert output.exists()
    assert output.read_bytes()[:5] == b"%PDF-"
    query = capsys.readouterr().out.strip()
    assert "t=trace,missing" in query
    assert "abc_case=lower" in query
    assert "missing_blanks=2" in query


def test_cli_invalid_abc_case_reports_error(tmp_path, capsys) -> None:
    """CLI reports field error for invalid abc-case."""
    output = tmp_path / "bad.pdf"
    code = main([
        "--topics", "trace",
        "--abc-case", "invalid",
        "-o", str(output),
    ])
    assert code == 2
    assert "abc_case: invalid_choice" in capsys.readouterr().err
    assert not output.exists()
