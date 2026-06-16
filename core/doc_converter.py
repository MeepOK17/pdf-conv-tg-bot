import subprocess
import shutil
from pathlib import Path
from .converter import Converter


SUPPORTED_FORMATS = {
    ".doc",
    ".docx",
    ".odt",
    ".rtf",
    ".ppt",
    ".pptx",
    ".odp",
    ".xls",
    ".xlsx",
    ".ods",
}


class DocToPdfConverter(Converter):
    """Converts Office documents to PDF using LibreOffice headless."""

    def __init__(self):
        super().__init__()
        self._libreoffice = self._find_libreoffice()

    def _find_libreoffice(self) -> str:
        for cmd in ("libreoffice", "soffice"):
            path = shutil.which(cmd)
            if path:
                return path
        raise EnvironmentError(
            "LibreOffice not found. Install it with: sudo apt install libreoffice"
        )

    def convert(self, input_path: str, output_dir: str) -> str:
        src = Path(input_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Input file not found: {src}")
        if src.suffix.lower() not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {src.suffix}. "
                f"Supported: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )

        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        result = subprocess.run(
            [
                self._libreoffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(src),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice conversion failed:\n{result.stderr or result.stdout}"
            )

        output_path = out_dir / (src.stem + ".pdf")
        if not output_path.exists():
            raise RuntimeError(
                f"Conversion finished but output file not found: {output_path}"
            )

        return str(output_path)
