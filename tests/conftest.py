import sys

import pytest

import namegen


@pytest.fixture
def project(tmp_path):
    return tmp_path


@pytest.fixture
def cli(project, monkeypatch, capsys):
    """Runs `namegen --project <tmp> ...` in-process; returns (exit code, stdout + stderr)."""

    def run(*args):
        monkeypatch.setattr(sys, "argv", ["namegen", "--project", str(project), *args])
        code = 0
        try:
            namegen.main()
        except SystemExit as e:
            code = e.code if isinstance(e.code, int) else 1
            if isinstance(e.code, str):
                print(e.code, file=sys.stderr)
        out = capsys.readouterr()
        return code, out.out + out.err

    return run
