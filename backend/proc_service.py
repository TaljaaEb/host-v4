# Eben Taljaard
import json
import socket
import ssl
import time
import urllib.request
import threading
import asyncio
import sys
import os

import win32serviceutil
import win32service
import win32event
import servicemanager

from stub import get_ip, get_username, hashing
from instance_worker import process_worker_task

AUTH_HOST, AUTH_PORT = '140.238.69.146', 8443
FLASK_HOST, FLASK_PORT = '192.168.101.107', 443

# Adjust certificate paths for Windows environment if necessary
CERT = 'C:\\path\\to\\host\\certs\\cert.pem'
KEY = 'C:\\path\\to\\host\\certs\\key.pem'

class ProcService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ProcBackgroundWorker"
    _svc_display_name_ = "Proc.py Background Automation Service"
    _svc_description_ = "Maintains mTLS connection with auth server, listens for webhook triggers, and coordinates itemline processing."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hStopEvent = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True

    def SvcStop(self):
        """Called when the Windows service is commanded to stop."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hStopEvent)
        self.is_running = False
        servicemanager.LogInfoMsg("ProcBackgroundWorker service stop signal received.")

    def SvcDoRun(self):
        """Main entry point when the Windows service starts."""
        servicemanager.LogInfoMsg("ProcBackgroundWorker service started.")
        try:
            self.main_workflow()
        except Exception as e:
            servicemanager.LogErrorMsg(f"ProcBackgroundWorker crashed with error: {e}")

    def background_worker_task(self, ip, itemlines):
        """Stalls in memory as a server listener, waits for webhook trigger, then streams itemlines."""
        servicemanager.LogInfoMsg("[*] Stalling in memory, waiting for incoming webhook connection on port 5555...")
        
        webhook_ip = "192.168.101.116"
        webhook_port = 5555
        
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind((webhook_ip, webhook_port))
        server_sock.listen(1)
        server_sock.settimeout(2.0)  # Allow periodic check of stop signal
        
        conn = None
        while self.is_running:
            try:
                s, addr = server_sock.accept()
                conn = s
                servicemanager.LogInfoMsg(f"[✓] Webhook triggered from {addr}!")
                conn.recv(1024)
                http_response = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
                conn.sendall(http_response)
                break
            except socket.timeout:
                continue
            except Exception as e:
                servicemanager.LogErrorMsg(f"[-] Error handling webhook: {e}")
                break
            finally:
                if conn:
                    conn.close()
                server_sock.close()

        if not self.is_running:
            return

        # Stream item lines to Tkinter Ingress Receiver app (port 8888)
        servicemanager.LogInfoMsg("[*] Connecting to Tkinter Receiver on port 8888...")
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
            servicemanager.LogInfoMsg("[✓] Stream completed successfully to Tkinter receiver.")
        except Exception as e:
            servicemanager.LogErrorMsg(f"[-] Error streaming to Tkinter app: {e}")

        # Run async worker task
        try:
            asyncio.run(process_worker_task("Instance-A", ip, itemlines))
        except Exception as e:
            servicemanager.LogErrorMsg(f"[-] Error in process_worker_task: {e}")

    def run_processing_flow(self, md4_hash):
        itemlines = self.fetch_itemlines(md4_hash)
        ip = "192.168.101.116"
        
        worker_thread = threading.Thread(target=self.background_worker_task, args=(ip, itemlines,))
        worker_thread.daemon = True
        worker_thread.start()
        
        return itemlines

    def wait_for_trigger(self):
        _flask_ssl_context = ssl._create_unverified_context()
        _flask_ssl_context.load_cert_chain(keyfile=KEY, certfile=CERT)
        _flask_ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        flask_opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_flask_ssl_context))
        
        url = f'https://{FLASK_HOST}:{FLASK_PORT}/check-trigger'
        servicemanager.LogInfoMsg('[*] Waiting for execution trigger from Flask web interface...')

        while self.is_running:
            try:
                with flask_opener.open(url, timeout=5) as response:
                    data = json.loads(response.read().decode('utf-8'))
                    if data.get('triggered'):
                        servicemanager.LogInfoMsg('[✓] Trigger detected!')
                        return True
            except Exception:
                pass
            time.sleep(3)
        return False

    def get_md4_from_flask(self) -> str:
        _flask_ssl_context = ssl._create_unverified_context()
        _flask_ssl_context.load_cert_chain(keyfile=KEY, certfile=CERT)
        _flask_ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        flask_opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_flask_ssl_context))
        
        url = f'https://{FLASK_HOST}:{FLASK_PORT}/get-hash'
        servicemanager.LogInfoMsg(f'[*] Requesting MD4 hash from {url}...')

        with flask_opener.open(url) as response:
            md4_hash = response.read().decode('utf-8').strip()
            servicemanager.LogInfoMsg(f'[+] Received MD4 Hash: {md4_hash}')
            return md4_hash

    def fetch_itemlines(self, md4_hash: str):
        _flask_ssl_context = ssl._create_unverified_context()
        _flask_ssl_context.load_cert_chain(keyfile=KEY, certfile=CERT)
        _flask_ssl_context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
        flask_opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_flask_ssl_context))
        
        url = f'https://{FLASK_HOST}:{FLASK_PORT}/itemlines/{md4_hash}'
        servicemanager.LogInfoMsg(f'[*] Hitting dynamic endpoint: {url}')

        with flask_opener.open(url) as response:
            content = response.read().decode('utf-8')
            servicemanager.LogInfoMsg(f'[+] --- RECEIVED ITEMLINES ---\n{content}\n[+] ---------------------------')
            return content

    def main_workflow(self):
        ip = "192.168.101.116"
        user = get_username()
        payload_hash = hashing(ip + user)
        
        context = ssl._create_unverified_context()
        context.load_cert_chain(keyfile=KEY, certfile=CERT)
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

        servicemanager.LogInfoMsg(f'[*] Connecting to auth server at {AUTH_HOST}:{AUTH_PORT}...')
        try:
            with socket.create_connection((AUTH_HOST, AUTH_PORT)) as raw_sock:
                with context.wrap_socket(raw_sock, server_hostname=AUTH_HOST) as tls_sock:
                    tls_sock.sendall(payload_hash.encode('utf-8'))
                    servicemanager.LogInfoMsg('[*] Registration hash sent. Waiting for CTRU...')

                    response = tls_sock.recv(1024).decode('utf-8')
                    servicemanager.LogInfoMsg(f'[+] Auth Response: {response}')

                    if 'CTRU' in response:
                        servicemanager.LogInfoMsg('[✓] CTRU confirmed by auth.py!')

                        if self.wait_for_trigger():
                            md4_hash = self.get_md4_from_flask()
                            self.run_processing_flow(md4_hash)

                            # Keep service alive
                            while self.is_running:
                                time.sleep(1)

        except Exception as e:
            servicemanager.LogErrorMsg(f'[-] Error in main workflow: {e}')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ProcService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ProcService)
