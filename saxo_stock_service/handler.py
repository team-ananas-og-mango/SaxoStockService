import json
import os

from kafka import KafkaProducer
from saxo_apy import SaxoOpenAPIClient
from saxo_apy.utils import decode_streaming_message

from confluent_kafka import Producer

from loggingservice import LoggingService


class Handler:
    def __init__(self, client: SaxoOpenAPIClient, logger: LoggingService):
        self.client = client
        self.producer = KafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BROKERS", ""),
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self.logger = logger

    async def message_handler(self) -> None:
        """Handle each received message by printing it to the terminal."""
        self.logger.logger.info("handler initialized")
        async with self.client.streaming_connection as stream:
            async for message in stream:
                response = decode_streaming_message(message)
                if response.ref_id != "_heartbeat":
                    for item in response.data:
                        item["Symbol"] = response.ref_id
                        # stock = Stock(open=item['Open'], high=item['High'], low=item['Low'], close=item['Close'], interest=item['Interest'], timestamp=item['Time'], symbol=item['Symbol'], volume=item['Volume'])
                        # print(stock)
                        await self.send_msg(topic=os.getenv('EXCHANGE', "xcse"), msg=item, key=item["Symbol"])

    async def send_msg(self, topic="xcse", msg=None, key=None):
        if msg is not None:
            self.producer.send(topic=topic, value=msg, key=key.encode("utf-8"))
