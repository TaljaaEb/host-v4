import asyncio
import threading
import tkinter as tk
from tkinter import scrolledtext
import ssl  # Import SSL to use HTTPS

class TkinterReceiverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dual Instance Single-Port Ingress Receiver")
        self.root.geometry("900x450")

        frame = tk.Frame(root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Text Area (Instance A Stream)
        left_frame = tk.LabelFrame(
            frame, text="Instance A Ingress", font=("Arial", 10, "bold")
        )
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        self.text1 = scrolledtext.ScrolledText(
            left_frame, wrap=tk.WORD, width=45, font=("Consolas", 10)
        )
        self.text1.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right Text Area (Instance B Stream)
        right_frame = tk.LabelFrame(
            frame, text="Instance B Ingress", font=("Arial", 10, "bold")
        )
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.text2 = scrolledtext.ScrolledText(
            right_frame, wrap=tk.WORD, width=45, font=("Consolas", 10)
        )
        self.text2.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.client_counter = 0

    def append_text(self, text_widget, message):
        text_widget.insert(tk.END, message + "\n")
        text_widget.see(tk.END)

# async def handle_client(reader, writer, app):
#     app.client_counter += 1
#     client_id = 1 if app.client_counter % 2 != 0 else 2
#     target_text = app.text1 if client_id == 1 else app.text2

#     app.append_text(
#         target_text, f"--- Ingress Connected: Instance {client_id} ---"
#     )

#     try:
#         while True:
#             data = await reader.readline()
#             if not data:
#                 break
#             line = data.decode("utf-8").strip()
#             app.append_text(target_text, line)
#     except Exception as e:
#         app.append_text(target_text, f"Error: {e}")
#     finally:
#         writer.close()
#         await writer.wait_closed()
#         app.append_text(
#             target_text, f"--- Ingress Disconnected: Instance {client_id} ---"
#         )

async def handle_client(reader, writer, app):
    app.client_counter += 1
    client_id = 1 if app.client_counter % 2 != 0 else 2
    target_text = app.text1 if client_id == 1 else app.text2

    app.append_text(
        target_text, f"--- Ingress Connected: Instance {client_id} ---"
    )

    try:
        while True:
            data = await reader.readline()
            if not data:
                break
            line = data.decode("utf-8").strip()
            app.append_text(target_text, line)
    except Exception as e:
        app.append_text(target_text, f"Read Error: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except (ConnectionResetError, OSError):
            # Ignore peer resets during close teardown
            pass
        
        app.append_text(
            target_text, f"--- Ingress Disconnected: Instance {client_id} ---"
        )

async def main_server(app):
    # Create SSL context
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile='/home/user/Desktop/host/certs/cert.pem', keyfile='/home/user/Desktop/host/certs/key.pem')

    # Single port 8888 used for all ingress connections
    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, app), "0.0.0.0", 8888, ssl=ssl_context
    )
    print("Tkinter Ingress Server listening on port 8888...")
    async with server:
        await server.serve_forever()

def run_server_thread(app):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main_server(app))

if __name__ == "__main__":
    root = tk.Tk()
    app = TkinterReceiverApp(root)
    threading.Thread(target=run_server_thread, args=(app,), daemon=True).start()
    root.mainloop()
