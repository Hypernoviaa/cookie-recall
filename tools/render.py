"""Render a local HTML file to PNG with QtWebEngine (same engine as Anki).

usage: python3 tools/render.py page.html out.png [width] [height] [wait_ms] [js_to_run_before_grab]
"""

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", "--no-sandbox --disable-gpu --disable-dev-shm-usage")

from PyQt6.QtCore import QTimer, QUrl  # noqa: E402
from PyQt6.QtWebEngineWidgets import QWebEngineView  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402


def main():
    src, out = sys.argv[1], sys.argv[2]
    w = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
    h = int(sys.argv[4]) if len(sys.argv) > 4 else 800
    wait = int(sys.argv[5]) if len(sys.argv) > 5 else 1500
    js = sys.argv[6] if len(sys.argv) > 6 else ""
    app = QApplication(sys.argv[:1])
    view = QWebEngineView()
    view.resize(w, h)
    page = view.page()
    page.javaScriptConsoleMessage = lambda lvl, msg, line, srcid: print(f"[js] {msg} ({srcid}:{line})")
    view.load(QUrl.fromLocalFile(os.path.abspath(src)))
    view.show()

    def grab():
        view.grab().save(out)
        print("saved", out)
        app.quit()

    def loaded(ok):
        if js:
            QTimer.singleShot(wait // 2, lambda: page.runJavaScript(js))
        QTimer.singleShot(wait, grab)

    view.loadFinished.connect(loaded)
    app.exec()


if __name__ == "__main__":
    main()
