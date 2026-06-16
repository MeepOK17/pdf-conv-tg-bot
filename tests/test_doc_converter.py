import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.doc_converter import DocToPdfConverter, SUPPORTED_FORMATS


@pytest.fixture
def converter():
    with patch("core.doc_converter.shutil.which", return_value="/usr/bin/libreoffice"):
        return DocToPdfConverter()


def _make_file(tmp_path: Path, name: str) -> Path:
    p = tmp_path / name
    p.write_bytes(b"dummy content")
    return p



class TestInit:
    def test_finds_libreoffice(self):
        with patch("core.doc_converter.shutil.which", return_value="/usr/bin/libreoffice"):
            c = DocToPdfConverter()
        assert c._libreoffice == "/usr/bin/libreoffice"

    def test_finds_soffice_fallback(self):
        def which_side_effect(cmd):
            return "/usr/bin/soffice" if cmd == "soffice" else None

        with patch("core.doc_converter.shutil.which", side_effect=which_side_effect):
            c = DocToPdfConverter()
        assert c._libreoffice == "/usr/bin/soffice"

    def test_raises_when_libreoffice_missing(self):
        with patch("core.doc_converter.shutil.which", return_value=None):
            with pytest.raises(EnvironmentError, match="LibreOffice not found"):
                DocToPdfConverter()



class TestInputValidation:
    def test_raises_on_missing_file(self, converter, tmp_path):
        with pytest.raises(FileNotFoundError):
            converter.convert(str(tmp_path / "ghost.docx"), str(tmp_path))

    def test_raises_on_unsupported_format(self, converter, tmp_path):
        src = _make_file(tmp_path, "file.mp3")
        with pytest.raises(ValueError, match="Unsupported format"):
            converter.convert(str(src), str(tmp_path))

    @pytest.mark.parametrize("ext", sorted(SUPPORTED_FORMATS))
    def test_all_supported_formats_accepted(self, converter, tmp_path, ext):
        src = _make_file(tmp_path, f"file{ext}")
        out_pdf = tmp_path / "file.pdf"
        out_pdf.write_bytes(b"%PDF")

        completed = MagicMock(returncode=0)
        with patch("core.doc_converter.subprocess.run", return_value=completed):
            result = converter.convert(str(src), str(tmp_path))

        assert result == str(out_pdf)



class TestConvert:
    def test_returns_pdf_path(self, converter, tmp_path):
        src = _make_file(tmp_path, "report.docx")
        out_pdf = tmp_path / "report.pdf"
        out_pdf.write_bytes(b"%PDF")

        completed = MagicMock(returncode=0)
        with patch("core.doc_converter.subprocess.run", return_value=completed) as mock_run:
            result = converter.convert(str(src), str(tmp_path))

        assert result == str(out_pdf)
        mock_run.assert_called_once()

    def test_creates_output_dir_if_missing(self, converter, tmp_path):
        src = _make_file(tmp_path, "doc.docx")
        out_dir = tmp_path / "nested" / "output"
        out_pdf = out_dir / "doc.pdf"

        def fake_run(*args, **kwargs):
            out_pdf.parent.mkdir(parents=True, exist_ok=True)
            out_pdf.write_bytes(b"%PDF")
            return MagicMock(returncode=0)

        with patch("core.doc_converter.subprocess.run", side_effect=fake_run):
            result = converter.convert(str(src), str(out_dir))

        assert out_dir.exists()
        assert result == str(out_pdf)

    def test_passes_correct_args_to_libreoffice(self, converter, tmp_path):
        src = _make_file(tmp_path, "slide.pptx")
        out_pdf = tmp_path / "slide.pdf"
        out_pdf.write_bytes(b"%PDF")

        completed = MagicMock(returncode=0)
        with patch("core.doc_converter.subprocess.run", return_value=completed) as mock_run:
            converter.convert(str(src), str(tmp_path))

        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "/usr/bin/libreoffice"
        assert "--headless" in call_args
        assert "--convert-to" in call_args
        assert "pdf" in call_args
        assert "--outdir" in call_args



class TestConvertFailures:
    def test_raises_on_nonzero_returncode(self, converter, tmp_path):
        src = _make_file(tmp_path, "bad.docx")
        completed = MagicMock(returncode=1, stderr="something went wrong", stdout="")
        with patch("core.doc_converter.subprocess.run", return_value=completed):
            with pytest.raises(RuntimeError, match="LibreOffice conversion failed"):
                converter.convert(str(src), str(tmp_path))

    def test_raises_when_output_pdf_missing_after_success(self, converter, tmp_path):
        src = _make_file(tmp_path, "doc.docx")
        completed = MagicMock(returncode=0)
        with patch("core.doc_converter.subprocess.run", return_value=completed):
            with pytest.raises(RuntimeError, match="output file not found"):
                converter.convert(str(src), str(tmp_path))

    def test_raises_on_timeout(self, converter, tmp_path):
        src = _make_file(tmp_path, "heavy.docx")
        with patch(
            "core.doc_converter.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="libreoffice", timeout=60),
        ):
            with pytest.raises(subprocess.TimeoutExpired):
                converter.convert(str(src), str(tmp_path))
