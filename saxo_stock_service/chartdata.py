from pprint import pprint
from body import ChartSubscriptionBody
from exchanges import Stockdescription
from saxo_apy import SaxoOpenAPIClient


class ChartData:
    def __init__(
        self, horizon: int, count: int, instruments: list[Stockdescription], exchange: str, client: SaxoOpenAPIClient
    ):
        self.horizon = horizon
        self.count = count
        self.instruments = instruments
        self.exchange = exchange
        self.client = client
        self.context_id = client.streaming_context_id
        self.body = ChartSubscriptionBody(self.horizon, self.count, self.context_id).body

    async def create_subscription(self) -> None:
        """Create subscription for EURUSD (uic 21) and GBPAUD (uic 22) prices."""
        sub = self.client.post(
            "/trade/v1/infoprices/subscriptions",
            data={
                "Arguments": {
                    "Uics": "21,22",
                    "AssetType": "FxSpot",
                },
                # this value is set when the streaming connection is initialized
                "ContextId": self.client.streaming_context_id,
                "ReferenceId": "my-fx-stream",
            },
        )
        pprint(sub)

    async def create_chart_subscription(self) -> None:
        count = 0
        for instrument in self.instruments:
            self.body.update({"ReferenceId": instrument.symbol.replace(f":{self.exchange}", "")})
            self.body["Arguments"]["Uic"] = instrument.identifier
            sub = self.client.post("chart/v1/charts/subscriptions", data=self.body)
            pprint(sub)
            count += 1
            print("subscribed so far: ", count)
