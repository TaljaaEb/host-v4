# Eben Taljaard 
import hashlib
import logging
import socket
import os  # Added to read environment variables

# 1. Read the port dynamically from Railway, defaulting to 8443 for local testing
HOST = '0.0.0.0'
PORT = int(os.environ.get("PORT", 8443))

logging.basicConfig(
    format='%(asctime)s \n%(message)s', level=logging.DEBUG
)
logger = logging.getLogger()

clients = []
connection = []

def match(conn):
  print(f'Active clients logged: {len(clients)}')
  if len(connection) == 2:
    conn.sendall(b'CTRU')  # Changed to sendall for standard sockets
    connection[0].sendall(b'CTRU')
    return True
  return False

def handle(conn):
  bstring = conn.recv(1024)
  logger.debug(f'Received hash payload: {bstring.decode("utf-8")}')
  clients.append(bstring)

  matched = match(conn)
  if matched:
    logger.debug(f'Client 0 hash: {clients[0]}')
    logger.debug(f'Client 1 hash: {clients[1]}')
    clients.clear()
    connection.clear()

def main():
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  sock.bind((HOST, PORT))
  sock.listen(10)

  # 2. Removed the Python ssl.context configuration completely.
  # Railway's proxy layer accepts the incoming HTTPS/TLS traffic and forwards it 
  # as raw TCP to your app.

  logger.info(f'auth.py server running on {HOST}:{PORT}...')

  while True:
    conn, addr = sock.accept()  # Accept raw socket connections directly
    try:
      connection.append(conn)
      handle(conn)
    except Exception as e:
      logger.error(f'Error: {e}')

if __name__ == '__main__':
  main()
