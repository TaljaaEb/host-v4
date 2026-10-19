import asyncio
import io
import socket
import ssl
import threading

left_buffer = io.StringIO()
right_buffer = io.StringIO()

client_counter = 0
buffer_lock = threading.Lock()

# HTML template with placeholder support
SEARCH_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dual-Sided Search List</title>
  <style>
    body { font-family: Arial, sans-serif; background: white; color: black; padding: 20px; }
    .container { display: flex; gap: 20px; }
    .left, .right { border: 1px solid #ccc; padding: 15px; width: 50%; min-height: 200px; border-radius: 6px; background: #f9f9f9; }
    h2 { margin-top: 0; }
    input[type="text"] { width: 100%; padding: 8px; margin-bottom: 15px; box-sizing: border-box; font-size: 14px; }
    .item { padding: 6px 0; border-bottom: 1px solid #eee; font-family: Consolas, monospace; }
  </style>
</head>
<body>
  <h1>Dual-Sided Dynamic Search</h1>
  <input type="text" id="search" placeholder="Search items..." onkeyup="filterList()">
  <div class="container">
    <div class="left" id="leftList">
      <h2>Instance A Ingress</h2>
      <!--LEFT_ITEMS_PLACEHOLDER-->
    </div>
    <div class="right" id="rightList">
      <h2>Instance B Ingress</h2>
      <!--RIGHT_ITEMS_PLACEHOLDER-->
    </div>
  </div>
  <script>
    function filterList() {
      const input = document.getElementById('search').value.toLowerCase();
      const leftItems = document.querySelectorAll('#leftList .item');
      const rightItems = document.querySelectorAll('#rightList .item');
      [...leftItems, ...rightItems].forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(input) ? '' : 'none';
      });
    }
  </script>
</body>
</html>
"""

def get_rendered_html():
    """Generates the final HTML page in memory using io.StringIO buffers."""
    with buffer_lock:
        left_lines = [line.strip() for line in left_buffer.getvalue().splitlines() if line.strip()]
        right_lines = [line.strip() for line in right_buffer.getvalue().splitlines() if line.strip()]

    left_html = "".join(f'<div class="item">{line}</div>' for line in left_lines)
    right_html = "".join(f'<div class="item">{line}</div>' for line in right_lines)

    if not left_html:
        left_html = '<div class="item" style="color: #888;">Waiting for Instance A stream...</div>'
    if not right_html:
        right_html = '<div class="item" style="color: #888;">Waiting for Instance B stream...</div>'

    html = SEARCH_HTML_TEMPLATE.replace("<!--LEFT_ITEMS_PLACEHOLDER-->", left_html)
    html = html.replace("<!--RIGHT_ITEMS_PLACEHOLDER-->", right_html)
    return html

async def handle_client(reader, writer):
    global client_counter
    try:
        # Read the initial payload or request line
        data = await asyncio.wait_for(reader.read(4096), timeout=3.0)
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        # Handle HTTP GET requests to serve the web interface
        if data.startswith(b"GET "):
            first_line = data.split(b"\n")[0].decode("utf-8", errors="ignore")
            parts = first_line.split(" ")
            path = parts[1] if len(parts) > 1 else "/"

            if "/favicon.ico" in path:
                response = b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            else:
                # html_content = get_rendered_html()
                # body = html_content.encode("utf-8")
                # response = (
                #     b"HTTP/1.1 200 OK\r\n"
                #     b"Content-Type: text/html; charset=utf-8\r\n"
                #     f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
                # )
                html_content = get_rendered_html()
                body = html_content.encode("utf-8")
                response = (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: text/html; charset=utf-8\r\n"
                    + f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
                    + body
                )

            writer.write(response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        # Handle incoming raw worker stream line-by-line (matching receiver_app.py architecture)
        with buffer_lock:
            client_counter += 1
            client_id = 1 if client_counter % 2 != 0 else 2
            target_buffer = left_buffer if client_id == 1 else right_buffer

        # Process first chunk if it contained stream data
        lines = data.split(b"\n")
        for line_bytes in lines:
            line = line_bytes.decode("utf-8", errors="ignore").strip()
            if line:
                with buffer_lock:
                    target_buffer.write(line + "\n")

        # Continue reading remaining lines from the worker stream
        while True:
            chunk = await reader.readline()
            if not chunk:
                break
            line = chunk.decode("utf-8", errors="ignore").strip()
            if line:
                with buffer_lock:
                    target_buffer.write(line + "\n")

    except asyncio.TimeoutError:
        pass
    except Exception as e:
        print(f"[Utility Receiver] Connection Error: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except (ConnectionResetError, OSError):
            pass

async def main_server():
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(
        certfile='/home/user/Desktop/host/certs/cert.pem',
        keyfile='/home/user/Desktop/host/certs/key.pem'
    )

    server = await asyncio.start_server(
        handle_client, "0.0.0.0", 8888, ssl=ssl_context
    )
    print("Embedded Async Ingress Server running. Access UI at: https://127.0.0.1:8888")

    async with server:
        await server.serve_forever()

def run_server_thread():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_server())

if __name__ == "__main__":
    # Run the asyncio server in a background thread or main loop thread
    run_server_thread()