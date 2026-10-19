import sys
import subprocess

def main():
    print("Select Receiver Mode:")
    print("1. Tkinter GUI App (receiver_app.py)")
    print("2. Non-UI Socket Web Server (utility_receiver.py with search.html)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("Launching Tkinter Receiver Application...")
        subprocess.run([sys.executable, "receiver_app.py"])
    elif choice == "2":
        print("Launching Non-UI Socket Web Server on http://127.0.0.1:8888/search.html...")
        subprocess.run([sys.executable, "utility_receiver.py"])
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
