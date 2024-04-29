import asyncio
import aioconsole
import os

user = os.path.expanduser('~').split('/')[-1]
reader, writer = None, None
listening, sending = True, True
tasks = []

async def listen():
    global reader, writer, listening, sending
    while listening:
        data = await reader.read(100)
        if data and data != 'close':
            print(data.decode())
        else:
            print('Closing connection')
            listening = False
            sending = False
            writer.close()
            await writer.wait_closed()
            print('Connection closed')
            tasks[0].cancel()
            tasks[1].cancel()
            break

async def send():
    global reader, writer
    while sending:
        message = await aioconsole.ainput()
        message = f"{user}:{message}"

        if writer is not None:
            writer.write(message.encode())
            try:
                await writer.drain()
            except ConnectionResetError as e:
                print('No connection')
                break
        else:
            break

async def connect():
    global reader, writer
    reader, writer = await asyncio.open_connection(
    '127.0.0.1', 8888)
    message = f"{user}:connect"
    writer.write(message.encode())
    await writer.drain()
    data = await reader.read(100)  
    print(data.decode())  

async def client():
    global tasks

    await connect()
    tasks.append(asyncio.create_task(listen()))
    tasks.append(asyncio.create_task(send()))

    try:
        await asyncio.gather(tasks[0], tasks[1])
    except asyncio.CancelledError:
        pass
    
asyncio.run(client())