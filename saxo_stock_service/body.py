class ChartSubscriptionBody:
    def __init__(self, horizon: int, count: int, context_id: str):
        self.horizon = horizon
        self.count = count
        self.context_id = context_id
        self.body = {
            "Arguments": {
                "assettype": "Stock",
                "Horizon": self.horizon,
                "Count": self.count,
                "Uic": "",
            },
            "ContextId": self.context_id,
            "ReferenceId": "",
            "Format": "application/json",
            "RefreshRate": 100
        }
