"""The desktop application: the local service, shown in a native window."""

from __future__ import annotations

import argparse
import sys
import time
import webbrowser
from pathlib import Path

from freewill.server.app import App, serve


def self_test(app: App, url: str) -> int:
    """Used on the packaged application: every part must be present and answer."""
    import json
    import urllib.request

    from freewill.core.kernel.guard import kernel_fingerprint
    from freewill.server.app import UI_DIR

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never through a proxy

    def get(path: str) -> bytes:
        request = urllib.request.Request(url + path, headers={"X-Freewill-Token": app.token})
        with opener.open(request, timeout=10) as response:
            return response.read()

    for name in ("index.html", "app.css", "app.js", "brain.js", "i18n.js"):
        assert get(name), f"missing interface file: {name}"
    assert "lives" in json.loads(get("api/lives"))
    kernel_sources = list((UI_DIR.parent / "core" / "kernel").glob("*.py"))
    assert kernel_sources, "the kernel sources are missing: its fingerprint would mean nothing"
    if getattr(sys, "frozen", False):  # the packaged application must carry its optional parts
        import anthropic, keyring, pypdf, webview  # noqa: F401,E401
    app.accept({"terms": True, "licence": True})
    born = app.birth({"name": "Selftest", "engine": {"kind": "simulated"}})
    assert born["kernel"] == kernel_fingerprint()[:12]
    app.rest()
    print("self-test passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="freewill-app", description=__doc__)
    parser.add_argument("--browser", action="store_true",
                        help="open in the default browser instead of a native window")
    parser.add_argument("--port", type=int, default=0, help="port to listen on (default: a free one)")
    parser.add_argument("--lives", help="folder in which life files are kept")
    parser.add_argument("--self-test", action="store_true",
                        help="check that the service and the interface are complete, then exit")
    args = parser.parse_args(argv)

    app = App(Path(args.lives) if args.lives else None)
    server = serve(app, args.port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    if args.self_test:
        try:
            return self_test(app, url)
        finally:
            server.shutdown()

    try:
        webview = None
        if not args.browser:
            try:
                import webview
            except ImportError:
                print("pywebview is not installed; opening in the browser instead.")
        if webview is not None:
            webview.create_window("Freewill (experimental)", url, width=1240, height=800, min_size=(940, 620),
                                  background_color="#0e1016")
            webview.start()
        else:
            print(f"Freewill is running at {url}\nPress Ctrl+C to stop.")
            webbrowser.open(url)
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        app.rest()
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
