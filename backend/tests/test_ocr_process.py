"""Exercise bounded subprocess I/O with real pipes on the current platform."""

import subprocess
import sys

import pytest
from brandproof import ocr


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_pipe_output_limits_kill_child(monkeypatch, stream):
    original = subprocess.Popen
    children = []

    def launch(*args, **kwargs):
        child = original(
            [
                sys.executable,
                "-c",
                f"import sys,time; sys.{stream}.buffer.write(b'x'*131072); sys.{stream}.flush(); time.sleep(10)",
            ],
            **kwargs,
        )
        children.append(child)
        return child

    monkeypatch.setattr(ocr.subprocess, "Popen", launch)
    monkeypatch.setattr(ocr, "MAX_OCR_OUTPUT_BYTES", 1024)
    monkeypatch.setattr(ocr, "MAX_OCR_ERROR_BYTES", 1024)
    with pytest.raises(ValueError, match="OCR output limit"):
        ocr._run_tesseract(b"")
    assert children[0].poll() is not None


def test_blocked_input_timeout_kills_child(monkeypatch):
    original = subprocess.Popen
    children = []

    def launch(*args, **kwargs):
        child = original([sys.executable, "-c", "import time; time.sleep(10)"], **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(ocr.subprocess, "Popen", launch)
    monkeypatch.setattr(ocr, "OCR_TIMEOUT_SECONDS", 0.2)
    with pytest.raises(subprocess.TimeoutExpired):
        ocr._run_tesseract(b"x" * (1024 * 1024))
    assert children[0].poll() is not None
