"""Main entry point for RapidOCR MCP Server."""

import sys
import argparse
from loguru import logger

from .config import settings


def setup_logging():
    """Setup logging configuration."""
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    if settings.log_file:
        logger.add(
            settings.log_file,
            rotation="100 MB",
            retention="10 days",
            level=settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RapidOCR MCP Server")
    parser.add_argument(
        "--mode",
        choices=["mcp", "fastapi", "stdio"],
        default="stdio",
        help="Server mode: mcp (MCP protocol), fastapi (HTTP), stdio (stdio transport)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Server host (for FastAPI mode)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Server port (for FastAPI mode)",
    )
    args = parser.parse_args()

    setup_logging()
    logger.info(f"Starting RapidOCR MCP Server in {args.mode} mode")

    if args.mode in ("mcp", "stdio"):
        from .mcp.server import main as mcp_main

        mcp_main()
    elif args.mode == "fastapi":
        from .server.fastapi_server import run_server

        host = args.host or settings.server_host
        port = args.port or settings.server_port
        logger.info(f"Starting FastAPI server on {host}:{port}")
        run_server()


if __name__ == "__main__":
    main()
