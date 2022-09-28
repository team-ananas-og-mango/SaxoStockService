from typing import List
from saxo_apy import SaxoOpenAPIClient


class Exchange:
    def __init__(self, mic: str):
        self.mic = mic

    def __repr__(self):
        return self.mic


class Stockdescription:
    def __init__(self, identifier: str, symbol: str, description: str):
        self.identifier = identifier
        self.symbol = symbol
        self.description = description

    def __repr__(self):
        return f"{self.symbol} ({self.identifier})"


class ExchangeReceiver:
    def __init__(self, client: SaxoOpenAPIClient):
        self.client = client

    async def list_of_exchanges(self) -> List[Exchange]:
        result = self.client.get("ref/v1/exchanges")["Data"]
        return [Exchange(exchange["Mic"]) for exchange in result]

    async def get_stocks_from_exchange(
        self, exchange: str = "xcse", asset_types: str = "Stock", skip: int = 0, top: int = 1000
    ) -> List[Stockdescription]:
        params = {"AssetTypes": asset_types, "Keywords": exchange, "$top": top, "$skip": skip}
        results = self.client.get("/ref/v1/instruments", params=params)["Data"]
        print(f"Found {len(results)} instruments")

        return [Stockdescription(value["Identifier"], value["Symbol"], value["Description"]) for value in results]
