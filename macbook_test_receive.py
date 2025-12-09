import asyncio
from nats.aio.client import Client as NATS

async def main():
	nats_client = NATS()
	await nats_client.connect("nats://127.0.0.1:4222")	# nats server on my macbook

	async def message_handler(msg):
		subject = msg.subject
		data = msg.data.decode()
		print(f"Received from LattePanda on '{subject}': {data}")

	await nats_client.subscribe("lattepanda.channel", cb=message_handler)
	print("Subscribed to 'lattepanda.channel'. Waiting for messages...")

	while True:
		await asyncio.sleep(1)

asyncio.run(main())
