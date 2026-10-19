import asyncio
import urllib.request
import ssl

#async def fire(ip, port):
#    try:
#        reader, writer = await asyncio.open_connection(ip, port)
#        writer.write(b"POST /webhook HTTP/1.1\r\nHost: localhost\r\n\r\n")
#        await writer.drain()
#        await reader.read(100)
#        writer.close()
#        await writer.wait_closed()
#    except Exception as e:
#        print(f"Failed to hit {ip}:{port}: {e}")

#async def fire(ip, port):
#    try:
#        # Create an SSL context to handle the receivers' HTTPS/SSL requirement
#        ssl_context = ssl.create_default_context()
#        ssl_context.check_hostname = False
#        ssl_context.verify_mode = ssl.CERT_NONE
#
#        reader, writer = await asyncio.open_connection(ip, port, ssl=ssl_context)
#        
#        # Include 'CTRU' in the headers or body stream as required
#        request_data = (
#            b"POST /webhook HTTP/1.1\r\n"
#            b"Host: localhost\r\n"
#            b"X-Worker-Token: CTRU\r\n"
#            b"Content-Length: 4\r\n\r\n"
#            b"CTRU"
#        )
#        #writer.write(request_data)
#        writer.write(b"POST /webhook HTTP/1.1\r\nHost: localhost\r\n\r\n")
#        await writer.drain()
#        await reader.read(100)
#        writer.close()
#        await writer.wait_closed()
#        print(f"Successfully fired webhook to {ip}:{port} with CTRU")
#    except Exception as e:
#        print(f"Failed to hit {ip}:{port}: {e}")

async def fire(ip, port):
    try:
        # Plain TCP connection matching test.py
        reader, writer = await asyncio.open_connection(ip, port)
        writer.write(b"POST /webhook HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()
        await reader.read(100)
        writer.close()
        await writer.wait_closed()
        print(f"Successfully fired webhook to {ip}:{port}")
    except Exception as e:
        print(f"Failed to hit {ip}:{port}: {e}")

async def main():
    print("Simultaneously firing webhooks to different worker IPs on the same port...")
    port = 5555  # Should match your server config
    await asyncio.gather(
#        fire("197.168.101.107", port), #Temp
         fire("192.168.101.107", port),
#        fire("172.30.0.2", port)  # Adjust IPs as needed
#        fire("localhost", port)  # Adjust IPs as needed
#        fire("127.0.0.1", 5005),
         fire("192.168.101.116", port),
#        fire("127.0.0.1", 5010)  # Adjust IPs as needed

    )

if __name__ == "__main__":
    asyncio.run(main())

# trigger_webhooks.py
#import asyncio
#import ssl
#
#async def fire(ip, port):
#    try:
#        # Create an SSL context to handle the receivers' HTTPS/SSL requirement
#        ssl_context = ssl.create_default_context()
#        ssl_context.check_hostname = False
#        ssl_context.verify_mode = ssl.CERT_NONE
#
#        reader, writer = await asyncio.open_connection(ip, port, ssl=ssl_context)
#        
#        # Include 'CTRU' in the headers or body stream as required
#        request_data = (
#            b"POST /webhook HTTP/1.1\r\n"
#            b"Host: localhost\r\n"
#            b"X-Worker-Token: CTRU\r\n"
#            b"Content-Length: 4\r\n\r\n"
#            b"CTRU"
#        )
#        writer.write(request_data)
#        await writer.drain()
#        await reader.read(100)
#        writer.close()
#        await writer.wait_closed()
#        print(f"Successfully fired webhook to {ip}:{port} with CTRU")
#    except Exception as e:
#        print(f"Failed to hit {ip}:{port}: {e}")
#
#async def main():
#    print("Simultaneously firing webhooks to worker IPs on port 8888...")
#    port = 8888  # Updated from 5000 to match receiver_app.py and utility_receiver.py
#    await asyncio.gather(
#        fire("127.0.0.1", port),
#        fire("127.0.0.1", port)
#    )
#
#if __name__ == "__main__":
#    asyncio.run(main())
