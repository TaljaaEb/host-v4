# Eben Taljaard 
import hashlib
import logging
import socket
import ssl

HOST, PORT = '0.0.0.0', 8443
CERT, KEY = '/home/opc/host/certs/cert.pem', '/home/opc/host/certs/key.pem'

logging.basicConfig(
    format='%(asctime)s \n%(message)s', level=logging.DEBUG
)
logger = logging.getLogger()

clients = []
connection = []


def match(conn):
  print(f'Active clients logged: {len(clients)}')
  if len(connection) == 2:
    conn.write(b'CTRU')
    connection[0].write(b'CTRU')
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
  sock.listen(5)

  context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
  context.load_cert_chain(certfile=CERT, keyfile=KEY, password='auth')
  context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

  logger.info(f'auth.py server running on {HOST}:{PORT}...')

  while True:
    ssock, addr = sock.accept()
    try:
      conn = context.wrap_socket(ssock, server_side=True)
      connection.append(conn)
      handle(conn)
    except ssl.SSLError as e:
      logger.error(f'SSL Error: {e}')


if __name__ == '__main__':
  main()
