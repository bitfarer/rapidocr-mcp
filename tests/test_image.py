"""Test image utilities."""

import base64
import io

from PIL import Image


class TestImageUtils:
    """Tests for image utilities."""

    def test_base64_to_pil(self):
        """Test base64 to PIL conversion."""
        from rapidocr_mcp.utils.image import base64_to_pil

        img = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode()

        result = base64_to_pil(b64)
        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)

    def test_base64_to_pil_with_prefix(self):
        """Test base64 with data:image prefix."""
        from rapidocr_mcp.utils.image import base64_to_pil

        img = Image.new("RGB", (100, 100), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

        result = base64_to_pil(b64)
        assert isinstance(result, Image.Image)

    def test_validate_image_format(self):
        """Test image format validation."""
        from rapidocr_mcp.utils.image import validate_image_format

        assert validate_image_format("test.jpg", ["jpg", "png"])
        assert validate_image_format("test.PNG", ["jpg", "png"])
        assert not validate_image_format("test.gif", ["jpg", "png"])

    def test_bytes_to_pil(self):
        """Test bytes to PIL conversion."""
        from rapidocr_mcp.utils.image import bytes_to_pil

        img = Image.new("RGB", (50, 50), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()

        result = bytes_to_pil(data)
        assert isinstance(result, Image.Image)
        assert result.size == (50, 50)
