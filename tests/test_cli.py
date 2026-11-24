# smoke test on a tiny generated image
"""End-to-end smoke test: generate a tiny image, run the CLI, check the outputs."""
from PIL import Image, ImageDraw

from cli_ascii_portrait import Settings, generate
from cli_ascii_portrait.cli import main


def make_test_image(path):
    """A 64x64 image: white background with a black square in the middle."""
    im = Image.new("RGB", (64, 64), "white")
    ImageDraw.Draw(im).rectangle((16, 16, 48, 48), fill="black")
    im.save(path)


def test_generate_returns_rectangular_text(tmp_path):
    img = tmp_path / "square.png"
    make_test_image(img)
    result = generate(str(img), Settings(cols=30))
    assert len(result.lines) > 0
    assert all(len(line) == len(result.lines[0]) for line in result.lines)


def test_cli_writes_all_outputs(tmp_path):
    img = tmp_path / "square.png"
    make_test_image(img)
    out = tmp_path / "out"
    main([str(img), "-o", str(out), "--cols", "30"])
    for suffix in [".txt", "_mono.png", "_color.png", ".html"]:
        assert (tmp_path / f"out{suffix}").exists()
