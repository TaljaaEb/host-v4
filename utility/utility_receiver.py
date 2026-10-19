import io
import socket
import threading
import ssl  # Import SSL to use HTTPS

left_buffer = io.StringIO()
right_buffer = io.StringIO()

client_counter = 0
buffer_lock = threading.Lock()

# HTML template (No search.html file required on disk)
SEARCH_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dual-Sided Search List</title>
  <style>
    body { font-family: Arial, sans-serif; background: white; color: black; }
    .container { display: flex; gap: 20px; }
    .left, .right { border: 1px solid #ccc; padding: 10px; }
  </style>
</head>
<body>
  <h1>Dual-Sided Dynamic Search</h1>
  <input type="text" id="search" placeholder="Search items..." onkeyup="filterList()">
  <div class="container">
    <div class="left" id="leftList"></div>
    <div class="right" id="rightList"></div>
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
        left_html = '<div class="item">Waiting for Instance A stream...</div>'
    if not right_html:
        right_html = '<div class="item">Waiting for Instance B stream...</div>'

    # Inject dynamic lines into template placeholders in memory
    html = SEARCH_HTML_TEMPLATE.replace("<!--LEFT_ITEMS_PLACEHOLDER-->", left_html.strip())
    html = html.replace("<!--RIGHT_ITEMS_PLACEHOLDER-->", right_html.strip())
    return html

def handle_connection(conn, addr):
    global client_counter
    try:
        conn.settimeout(3.0)
        initial_data = conn.recv(4096)

        if not initial_data:
            return
        
        # Handle incoming HTTP requests
        if initial_data.startswith(b"GET "):
            first_line = initial_data.split(b"\n")[0].decode("utf-8", errors="ignore")
            parts = first_line.split(" ")
            path = parts[1] if len(parts) > 1 else "/"

            if "/favicon.ico" in path:
                response = "HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
            else:
                html_content = get_rendered_html()
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n" + html_content

            conn.sendall(response.encode("utf-8"))
            conn.close()
            return

        # Handle incoming raw worker socket stream line by line
        with buffer_lock:
            client_counter += 1
            client_id = 1 if client_counter % 2 != 0 else 2
            target_buffer = left_buffer if client_id == 1 else right_buffer

        stream_data = initial_data
        while True:
            if not stream_data:
                stream_data = conn.recv(1024)
                if not stream_data:
                    break
            
            lines = stream_data.split(b"\n")
            for line_bytes in lines[:-1]:
                line = line_bytes.decode("utf-8", errors="ignore").strip()
                if line:
                    target_buffer.write(line + "\n")
            stream_data = lines[-1]

    except Exception as e:
        print(f"[Utility Receiver] Error: {e}")
    finally:
        conn.close()

def run_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("127.0.0.1", 8888))
    server_socket.listen(5)
    
    # Wrap the socket with SSL
    server_socket = ssl.wrap_socket(server_socket,
                                     certfile='/home/user/Desktop/host/certs/cert.pem',
                                     keyfile='/home/user/Desktop/host/certs/key.pem',
                                     server_side=True)

    print("Embedded Socket Server running. Access UI at: https://127.0.0.1:8888")

    try:
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=handle_connection, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down server.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    run_server()