import asyncio
import os
import sys
from typing import List

from chartdata import ChartData
from exchanges import ExchangeReceiver, Stockdescription
from handler import Handler
from loggingservice import LoggingService
from loginservice import SaxoLoginClient

path = os.path.dirname(os.path.abspath(__file__))
logging_service = LoggingService("main logger")

client = SaxoLoginClient(app_config=f"{path}/app_config.json", log_level="DEBUG")
client.login(launch_browser=False, catch_redirect=True, redirect_url=client.available_redirect_urls[0])


async def create_connection(instruments: List[Stockdescription], exchange: str = "xcse"):
    client.setup_streaming_connection()

    # ensure refresh() is called so the websocket connection is re-authorized automatically
    # this keeps the streaming connection alive - else it is closed when token expires
    asyncio.ensure_future(client.async_refresh())
    logging_service.logger.info(f"pulling stock from {exchange}")
    await ChartData(
        client=client, horizon=1, count=1, exchange=exchange, instruments=instruments
    ).create_chart_subscription()
    logging_service.logger.info(f"done pulling stocks from {exchange}")
    # this call will run forever, receiving messages until interrupted by user
    await Handler(client, logging_service).message_handler()


async def main(client) -> None:
    """Execute main application logic."""
    exchange: str = os.getenv("EXCHANGE", "xcse")
    top: int = os.getenv('TOP', 50)
    instruments: List[Stockdescription] = await ExchangeReceiver(client).get_stocks_from_exchange(
        exchange=exchange, top=top, skip=0
    )

    await create_connection(instruments, exchange)


if __name__ == "__main__":
    
    try:
        logging_service.logger.info("starting main loop")
        asyncio.run(main(client))

    except KeyboardInterrupt:
        logging_service.logger.info("User interrupted the interpreter - closing connection.")
        sys.exit()
