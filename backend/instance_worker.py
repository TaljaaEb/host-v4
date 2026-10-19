import asyncio
import sys

try:
    import servicemanager
except ModuleNotFoundError:
    class MockServiceManager:
        def LogMsg(self, *args, **kwargs): pass
        def LogInfoMsg(self, *args, **kwargs): pass
        def LogErrorMsg(self, *args, **kwargs): pass
        def LogWarningMsg(self, *args, **kwargs): pass
    
    servicemanager = MockServiceManager()

def run_worker(itemlines=None):
    pass

async def stream_to_tkinter(instance_name, itemlines):
  print(f"[{instance_name}] Webhook triggered! Connecting to Tkinter on port 8888...")
  try:
    # Corrected port from 888 to 8888 to match receiver_app.py
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888)
    if itemlines:
      lines = itemlines.strip().split("\n")
      for item in lines:
        payload = f"[{instance_name}] -> {item}\n"
        writer.write(payload.encode("utf-8"))
        await writer.drain()
        await asyncio.sleep(0.5)

    writer.close()
    await writer.wait_closed()
    print(f"[{instance_name}] Stream completed.")
  except Exception as e:
    print(f"[{instance_name}] Connection error: {e}")

async def handle_webhook(reader, writer, instance_name, itemlines):
  _ = await reader.readline()
  response = "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
  writer.write(response.encode("utf-8"))
  await writer.drain()
  writer.close()
  await writer.wait_closed()

  asyncio.create_task(stream_to_tkinter(instance_name, itemlines))

async def process_worker_task(nm, ip, itemlines):
  instance_name = nm
  webhook_ip = ip
  fixed_port = 5555

  server = await asyncio.start_server(
      lambda r, w: handle_webhook(r, w, instance_name, itemlines), webhook_ip, fixed_port
  )
  if nm == 'Instance-A':
    print(f"[{instance_name}] Webhook server listening on {webhook_ip}:{fixed_port}")
  if nm == 'Instance-B':
    servicemanager.LogInfoMsg(
      f"[{instance_name}] Webhook server listening on {webhook_ip}:{fixed_port}"  
    )
  async with server:
    await server.serve_forever()

if __name__ == "__main__":
    run_worker()