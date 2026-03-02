# RapidOCR MCP Server

High-performance OCR MCP Server.

## Features

- **Multi-mode**: MCP stdio, FastAPI HTTP, streamable-http
- **Multi-input**: Path, Base64, URL, File upload
- **Batch OCR**: Process multiple images in one request
- **Output formats**: Plain, JSON, Markdown, Structured
- **Image preprocessing**: Auto-enhance, rotate, binarize
- **Security**: Path whitelist, API key, CORS, audit logging
- **Monitoring**: Prometheus metrics, OpenTelemetry tracing
- **Production-ready**: Docker, CI/CD, tests

## Quick Start

### Global Installation

```bash
# Install globally with uvx (recommended)
uvx rapidocr-mcp

# Or install globally with pip
pip install rapidocr-mcp
```

### Local Development

```bash
# Install dependencies
uv sync

# Run MCP server (stdio mode)
uv run rapidocr-mcp

# Run FastAPI server
uv run rapidocr-mcp --mode fastapi --port 8080
```

## Configuration

Set environment variables with `RAPIDOCR_` prefix:

```bash
export RAPIDOCR_LANG=ch
export RAPIDOCR_LOG_LEVEL=INFO
export RAPIDOCR_API_KEY=your-key
```

## MCP Configuration

### Available Tools

| Tool | Description |
|------|-------------|
| `ocr_by_path` | OCR for local image file by path |
| `ocr_by_content` | OCR for Base64 encoded image |
| `ocr_by_url` | OCR for image from HTTP/HTTPS URL |
| `ocr_batch` | Batch OCR for multiple images |

### Claude Desktop

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "rapidocr": {
      "command": "uvx",
      "args": ["rapidocr-mcp"]
    }
  }
}
```

Or with local installation:

```json
{
  "mcpServers": {
    "rapidocr": {
      "command": "uv",
      "args": ["--directory", "/path/to/rapidocr-mcp", "run", "rapidocr-mcp"]
    }
  }
}
```

### Other MCP Clients

For other MCP clients that support stdio mode, configure the command as:

```bash
uvx rapidocr-mcp
# or
rapidocr-mcp
```

## Docker

```bash
docker-compose -f docker/docker-compose.yml up
```

## API Endpoints

- `GET /health` - Health check
- `POST /ocr/path` - OCR by file path
- `POST /ocr/base64` - OCR by base64
- `POST /ocr/url` - OCR by URL
- `POST /ocr/upload` - OCR by file upload
- `GET /metrics` - Prometheus metrics

## License

MIT
