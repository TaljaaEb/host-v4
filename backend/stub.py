# Eben Taljaard
import hashlib
import os
import socket


def get_ip():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(('8.8.8.8', 80))
  IP = s.getsockname()[0]
  s.close()
  return IP


def get_username():
  try:
    USER = os.getlogin()
  except Exception:
    USER = os.getenv('USER') or os.getenv('USERNAME') or 'auth'
  return USER


def hashing(ctext):
  obj = hashlib.sha256()
  obj.update(bytes(ctext, 'utf-8'))
  return obj.hexdigest()