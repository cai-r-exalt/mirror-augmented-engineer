from typing import Any, Dict, Optional


class CreerCommandeRequest:
    def __init__(self, festivalierId: Optional[str], articles: Optional[Any]):
        self.festivalierId = festivalierId
        self.articles = articles


class CreerCommandeResponse:
    def __init__(self, status_code: int, body: Dict[str, Any]):
        self.status_code = status_code
        self._body = body

    def json(self) -> Dict[str, Any]:
        return self._body
