from __future__ import annotations


class GraphAPIError(Exception):
    """Raised when Microsoft Graph returns a non-2xx response.

    Carries the parsed error body so callers can act on the specific code
    rather than a raw HTTP status line.
    """

    def __init__(self, status_code: int, error_code: str, graph_message: str) -> None:
        super().__init__(f"[{status_code}] {error_code}: {graph_message}")
        self.status_code = status_code
        self.error_code = error_code
        self.graph_message = graph_message
