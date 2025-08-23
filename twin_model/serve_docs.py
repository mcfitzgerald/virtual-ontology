#!/usr/bin/env python3
"""Serve the Twin Model documentation locally."""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path


def serve_docs(port=8080):
    """Serve the documentation on a local web server."""

    # Change to docs directory
    docs_dir = Path(__file__).parent / "docs" / "_build" / "html"

    if not docs_dir.exists():
        print("❌ Documentation not built yet!")
        print("Run: cd twin_model/docs && make html")
        return

    os.chdir(docs_dir)

    # Create server
    Handler = http.server.SimpleHTTPRequestHandler

    with socketserver.TCPServer(("", port), Handler) as httpd:
        url = f"http://localhost:{port}"
        print("=" * 60)
        print("TWIN MODEL DOCUMENTATION SERVER")
        print("=" * 60)
        print(f"\n📚 Serving documentation at: {url}")
        print(f"📁 From: {docs_dir}")
        print("\nPress Ctrl+C to stop the server\n")
        print("=" * 60)

        # Open browser
        webbrowser.open(url)

        # Serve forever
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Documentation server stopped")


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    serve_docs(port)
