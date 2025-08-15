import logging
from typing import Optional


class SafeConsoleHandler(logging.StreamHandler):
    """
    Stream handler that safely writes unicode messages to consoles with limited encodings
    (e.g., Windows cp1252). Characters not supported by the console encoding are
    replaced instead of raising UnicodeEncodeError.

    File logging should be configured separately with UTF-8 encoding to preserve
    original characters.
    """

    def __init__(self, stream: Optional[object] = None) -> None:
        # Use default StreamHandler behavior (stderr) to match Django's console handler semantics
        super().__init__(stream)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            stream = self.stream
            encoding = getattr(stream, 'encoding', None) or 'utf-8'
            try:
                safe_msg = msg.encode(encoding, errors='replace').decode(encoding, errors='replace')
            except Exception:
                safe_msg = msg
            stream.write(safe_msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)