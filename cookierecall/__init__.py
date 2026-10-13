"""Cookie Recall: a Cookie Clicker-style bakery that only bakes when you review.

The game engine (game.py, content.py) is pure Python and imports nothing from
Anki, so it can be tested and simulated on its own. The Anki glue lives in
integration.py and is only loaded when this package is imported by Anki.
"""

import sys

if "aqt" in sys.modules:
    from aqt import mw

    if mw is not None:
        from . import integration

        integration.setup()
