#!/usr/bin/env python3
# main.py — TCP version for mail_server.py

import sys
import json
import socket
import threading
from PyQt5 import QtWidgets, uic

# Configuration
RELAY_IP = "172.20.10.4"  # Relay (server) IP
RELAY_PORT = 9999         # Relay (server) port
LISTEN_PORT = 8000        # Each client must use a unique port


# ---------------- TCP CLIENT CLASS ---------------- #
class TCPMailClient:
    def __init__(self, listen_port=8000):
        self.listen_port = listen_port
        self.listener_thread = None
        self.running = False

    def _get_local_ip(self):
        """Return this machine’s local IP address."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    # ---------- LISTENER ---------- #
    def start_listener(self, on_message_callback):
        """Start a background TCP listener for incoming messages."""
        self.running = True

        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
                server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_sock.bind(("0.0.0.0", self.listen_port))
                server_sock.listen(5)
                print(f"Listening for incoming TCP mail on port {self.listen_port}...")
                while self.running:
                    try:
                        conn, addr = server_sock.accept()
                        data = conn.recv(8192)
                        if not data:
                            conn.close()
                            continue
                        try:
                            packet = json.loads(data.decode("utf-8"))
                            on_message_callback(packet, addr)
                        except json.JSONDecodeError:
                            print(f"[{addr}] Received invalid JSON")
                        conn.close()
                    except Exception as e:
                        if self.running:
                            print("Listener error:", e)

        self.listener_thread = threading.Thread(target=listen, daemon=True)
        self.listener_thread.start()

    def stop_listener(self):
        """Stop listening for incoming messages."""
        self.running = False

    # ---------- SENDER ---------- #
    def send_via_relay(self, relay_addr, to, subject, body, from_addr):
        """Send message to relay using TCP."""
        packet = {
            "from": from_addr,
            "to": to,
            "subject": subject,
            "body": body,
        }
        try:
            data = json.dumps(packet).encode("utf-8")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(relay_addr)
                s.sendall(data)
                s.settimeout(3.0)
                try:
                    response = s.recv(4096)
                    if response:
                        return response.decode("utf-8")
                except socket.timeout:
                    return "No response (timeout)"
            return "Message sent successfully."
        except Exception as e:
            return f"Send failed: {e}"


# ---------------- MAIN APP (PyQt5 UI) ---------------- #
class MailApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("NetworkProgramming.ui", self)

        # UI elements
        self.send_button = self.findChild(QtWidgets.QPushButton, "pushButton")
        self.refresh_button = self.findChild(QtWidgets.QPushButton, "pushButton_2")
        self.user_input = self.findChild(QtWidgets.QLineEdit, "lineEdit")
        self.message_box = self.findChild(QtWidgets.QPlainTextEdit, "plainTextEdit")
        self.graphics_view = self.findChild(QtWidgets.QGraphicsView, "graphicsView")

        # Connect buttons
        self.send_button.clicked.connect(self.send_message)
        self.refresh_button.clicked.connect(self.refresh_inbox)

        # Initialize TCP client
        self.client = TCPMailClient(listen_port=LISTEN_PORT)
        self.client.start_listener(self.on_message_received)

        self.inbox = []
        self.update_graphics_view(f"Listening for TCP mail on port {LISTEN_PORT}")

    def on_message_received(self, packet, addr):
        """Handle received TCP mail."""
        sender = packet.get("from", str(addr))
        subject = packet.get("subject", "(no subject)")
        body = packet.get("body", "")
        msg_text = f"From: {sender}\n{subject}\n{body}\n"
        print("Received:", msg_text)

        self.inbox.append(msg_text)
        self.update_graphics_view(msg_text)

    def send_message(self):
        """Send a message through the TCP relay."""
        target = self.user_input.text().strip()
        body = self.message_box.toPlainText().strip()

        if not target or not body:
            QtWidgets.QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return
        if ":" not in target:
            QtWidgets.QMessageBox.warning(self, "Error", "Target must be in ip:port format.")
            return

        subject = "Message from TCP Mail"
        resp = self.client.send_via_relay(
            relay_addr=(RELAY_IP, RELAY_PORT),
            to=target,
            subject=subject,
            body=body,
            from_addr=f"{self.client._get_local_ip()}:{self.client.listen_port}"
        )

        self.message_box.clear()
        self.update_graphics_view(f"Sent to {target}\n{body}\n(Response: {resp})")
        print("Relay response:", resp)

    def refresh_inbox(self):
        """Update inbox area."""
        self.update_graphics_view("\n\n".join(self.inbox))

    def update_graphics_view(self, text):
        """Display text in the inbox area."""
        scene = QtWidgets.QGraphicsScene()
        scene.addText(text)
        self.graphics_view.setScene(scene)


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MailApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
