import asyncio
from nats.aio.client import Client as NATS

async def main():
    nats_client = NATS()
    await nats_client.connect("nats://10.0.0.71:4222") # change this address

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data.decode()
        print(f"Received message on '{subject}': {data}")

    await nats_client.subscribe("macbook.channel", cb=message_handler)
    print("Subscribed to 'macbook.channel'. Waiting for messages...")

    while True:
        await asyncio.sleep(1)

asyncio.run(main())
~                    