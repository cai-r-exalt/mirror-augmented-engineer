class StockInsuffisantException(Exception):
    def __init__(self, item_name: str):
        self.item_name = item_name
        super().__init__(f"Insufficient stock for {item_name}")


class ArticleInconnuException(Exception):
    def __init__(self, item_name: str):
        self.item_name = item_name
        super().__init__(f"Unknown article: {item_name}")
