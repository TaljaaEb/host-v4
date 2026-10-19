# Eben Taljaard[cite: 2]
import json
import socket
import ssl
import time
import urllib.request
import asyncio
import threading

from stub import get_ip, get_username, hashing
from instance_worker import process_worker_task  # Renamed from 'unused()'[cite: 2, 8]

AUTH_HOST, AUTH_PORT = '140.238.69.146', 8443
FLASK_HOST, FLASK_PORT = '192.168.101.107', 443

CERT = '/home/user/Desktop/host/certs/cert.pem'
KEY = '/home/user/Desktop/host/certs/key.pem'

# Configure an HTTPS opener with client certificate chain (mTLS) and unverified context
_flask_ssl_context = ssl._create_unverified_context()
_flask_ssl_context.load_cert_chain(keyfile=KEY, certfile=CERT)
_flask_ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

_flask_handler = urllib.request.HTTPSHandler(context=_flask_ssl_context)
flask_opener = urllib.request.build_opener(_flask_handler)

def background_worker_task(ip, itemlines):
    """Stalls in memory as a server listener, waits for webhook trigger, then streams to Tkinter receiver."""
    print("[*] Stalling in memory, waiting for incoming webhook connection on port 5555...")
    
    webhook_ip = "192.168.101.107"
    webhook_port = 5555
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((webhook_ip, webhook_port))
    server_sock.listen(1)
    
    try:
        conn, addr = server_sock.accept()
        print(f"[✓] Webhook triggered from {addr}!")
        
        # Read the incoming trigger request to clear the socket buffer
        conn.recv(1024)
        
        # Respond back with HTTP OK so the webhook caller closes cleanly without broken pipe
        http_response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
        conn.sendall(http_response)
        conn.close()
    except Exception as e:
        print(f"[-] Error handling webhook: {e}")
    finally:
        server_sock.close()

    # Now stream item lines to the Tkinter Ingress Receiver app (port 8888)
    print("[*] Connecting to Tkinter Receiver on port 8888...")
    receiver_host = "127.0.0.1"
    receiver_port = 8888
    
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    try:
        s = socket.create_connection((receiver_host, receiver_port), timeout=3)
        stream_conn = context.wrap_socket(s, server_hostname=receiver_host)
        
        if itemlines:
            lines = itemlines.strip().split("\n")
            for line in lines:
                payload = f"[Instance-A] -> {line}\n".encode("utf-8")
                stream_conn.sendall(payload)
                time.sleep(0.5)
        stream_conn.close()
        print("[✓] Stream completed successfully to Tkinter receiver.")
    except Exception as e:
        print(f"[-] Error streaming to Tkinter app: {e}")

    # Properly run the async worker task to eliminate the RuntimeWarning
    try:
        asyncio.run(process_worker_task("Instance-A", ip, itemlines))
    except Exception as e:
        print(f"[-] Error in process_worker_task: {e}")

def run_processing_flow(md4_hash):
    itemlines = fetch_itemlines(md4_hash)
    ip = "192.168.101.107"
    
    worker_thread = threading.Thread(target=background_worker_task, args=(ip, itemlines,))
    worker_thread.daemon = True
    worker_thread.start()
    
    return itemlines

def wait_for_trigger():
  url = f'https://{FLASK_HOST}:{FLASK_PORT}/check-trigger'
  print('[*] Waiting for execution trigger from Flask web interface...')

  while True:
    try:
      with flask_opener.open(url, timeout=5) as response:
        data = json.loads(response.read().decode('utf-8'))
        if data.get('triggered'):
          print('[✓] Trigger detected!')
          return
    except Exception as e:
      pass
    time.sleep(3)

def get_md4_from_flask() -> str:
  url = f'https://{FLASK_HOST}:{FLASK_PORT}/get-hash'
  print(f'[*] Requesting MD4 hash from {url}...')

  with flask_opener.open(url) as response:
    md4_hash = response.read().decode('utf-8').strip()
    print(f'[+] Received MD4 Hash: {md4_hash}')
    return md4_hash

def fetch_itemlines(md4_hash: str):
  url = f'https://{FLASK_HOST}:{FLASK_PORT}/itemlines/{md4_hash}'
  print(f'[*] Hitting dynamic endpoint: {url}')

  with flask_opener.open(url) as response:
    content = response.read().decode('utf-8')
    print('\n[+] --- RECEIVED ITEMLINES ---')
    print(content)
    print('[+] ---------------------------\n')
    return content

def main():
  ip = "192.168.101.107"
  user = get_username()
  payload_hash = hashing(ip + user)
  context = ssl._create_unverified_context()
  context.load_cert_chain(keyfile=KEY, certfile=CERT)
  context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

  print(f'[*] Connecting to auth server at {AUTH_HOST}:{AUTH_PORT}...')
  try:
    with socket.create_connection((AUTH_HOST, AUTH_PORT)) as raw_sock:
      with context.wrap_socket(raw_sock, server_hostname=AUTH_HOST) as tls_sock:
        tls_sock.sendall(payload_hash.encode('utf-8'))
        print('[*] Registration hash sent. Waiting for CTRU...')

        response = tls_sock.recv(1024).decode('utf-8')
        print(f'[+] Auth Response: {response}')

        if 'CTRU' in response:
          print('[✓] CTRU confirmed by auth.py!')

          wait_for_trigger()
          md4_hash = get_md4_from_flask()
          run_processing_flow(md4_hash)

          while True:
              time.sleep(1)

  except Exception as e:
    print(f'[-] Error: {e}')

if __name__ == '__main__':
  main()