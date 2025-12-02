#!/usr/bin/env python3
# main.py — TCP version (UI chooses relay IP/port)

import sys
import json
import socket
import threading
from Dashboard import Ui_MainWindow
from login import Ui_loginWindow
from PyQt5 import QtWidgets, uic
import random

users = {}  # to hold dictionary of users and port number


# ---------------- TCP CLIENT CLASS ---------------- #
class TCPMailClient:
    def __init__(self, listen_port):
        self.listen_port = listen_port
        self.listener_thread = None
        self.running = False

    def _get_local_ip(self):  # is this still needed?
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
        """Start background thread to listen for incoming TCP mail."""
        self.running = True

        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
                server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_sock.bind(("0.0.0.0", self.listen_port))
                server_sock.listen(5)
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
                            print(f"[{addr}] Invalid JSON received")
                        conn.close()
                    except Exception as e:
                        if self.running:
                            print("Listener error:", e)

        self.listener_thread = threading.Thread(target=listen, daemon=True)
        self.listener_thread.start()

    # ---------- SENDER ---------- #
    def send_via_relay(self, relay_ip, relay_port, to, subject, body, from_addr):
        """Send message via relay (TCP)."""
        packet = {
            "from": from_addr,
            "to": to,
            "subject": subject,
            "body": body,
        }
        try:
            data = json.dumps(packet).encode("utf-8")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((relay_ip, relay_port))
                s.sendall(data)
                s.settimeout(3.0)
                try:
                    response = s.recv(4096)
                    if response:
                        return response.decode("utf-8")
                except socket.timeout:
                    return "No response (timeout)"
            return "Message sent."
        except Exception as e:
            return f"Send failed: {e}"


# ---------------- MAIN APP ---------------- #
class MailApp(QtWidgets.QMainWindow):
    def __init__(self, listen_port):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.logout_button.clicked.connect(self.logout)

        self.client = TCPMailClient(listen_port)
        self.client.start_listener(self.on_message_received)
        self.inbox = []

        self.update_graphics_view(f"Listening on TCP port {listen_port}")

        # Connect buttons
        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.pushButton_2.clicked.connect(self.refresh_inbox)

    def logout(self):
        for i in users:
            if users[i] == self.client.listen_port:
                del users[i]
                break
        self.client.stop_listener()
        self.close()

    def on_message_received(self, packet, addr):
        sender = packet.get("from", str(addr))
        subject = packet.get("subject", "(no subject)")
        body = packet.get("body", "")
        msg_text = f"From: {sender}\n{subject}\n{body}\n"
        print("Received:", msg_text)
        self.inbox.append(msg_text)
        self.update_graphics_view(msg_text)

    def send_message(self):
        """Send a message using user input in UI."""
        relay_info = self.ui.sendtoEdit.text().strip()  # e.g. ally or hunter
        body = self.ui.user_message.toPlainText().strip()

        if not relay_info or not body:
            QtWidgets.QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return
        # Lookup relay IP and port from users dictionary
        if relay_info in users:
            ip, port = users[relay_info]

        else:
            QtWidgets.QMessageBox.warning(self, "Error", f"Unknown user: {relay_info}")
            return
        # Parse relay ip:port no longer needed?
        # if ":" not in relay_info:
        #   QtWidgets.QMessageBox.warning(self, "Error", "Relay must be in ip:port format.")
        #    return
        # relay_ip, relay_port = relay_info.split(":")
        # relay_port = int(relay_port)

        subject = "Message from TCP Mail Client"
        from_addr = f"{self.client._get_local_ip()}:{self.client.listen_port}"

        resp = self.client.send_via_relay(
            relay_ip=ip,
            relay_port=port,
            to="relay",  # handled by the server logic
            subject=subject,
            body=body,
            from_addr=from_addr,
        )

        self.message_box.clear()
        self.update_graphics_view(
            f"Sent to relay {relay_ip}:{relay_port}\n{body}\n(Response: {resp})"
        )
        print("Relay response:", resp)

    def refresh_inbox(self):
        self.update_graphics_view("\n\n".join(self.inbox))

    def update_graphics_view(self, text):
        scene = QtWidgets.QGraphicsScene()
        scene.addText(text)
        self.ui.graphicsView.setScene(scene)


# ---------------- LOGIN WINDOW ---------------- #


class Login(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_loginWindow()
        self.ui.setupUi(self)
        self.ui.loginButton.clicked.connect(self.validateLogin)

    def validateLogin(self):
        username = self.ui.usernameEdit.text()
        port_str = self.ui.portNum.text()
        port = int(port_str) if port_str.isdigit() else None

        if port == 0 or port is None:
            port = random.randint(1024, 65535)  # assign random port if none
        if port < 1024 or port > 65535:  # check port range if one provided
            QtWidgets.QMessageBox.warning(
                self, "Error", "Port number must be between 1024 and 65535."
            )
            return

        if username != None and self.ui.termsCheck.isChecked():
            users[username] = port  # store user info then proceed to chat
            self.mail_app = MailApp(port)
            self.mail_app.show()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Invalid Login Details or Terms not accepted."
            )


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    loginWindow = Login()
    loginWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
