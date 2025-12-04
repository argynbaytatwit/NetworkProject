#!/usr/bin/env python3
# main.py — TCP version (UI chooses relay IP/port)

#!/usr/bin/env python3
# main.py — TCP version (UI chooses relay by nickname)


import sys
import json
import socket
import threading
from Dashboard import Ui_MainWindow
from login import Ui_loginWindow
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
import random
import requests
#userlist csv inplace of a long term more secure/permanent database

# userlist csv inplace of a long term more secure/permanent database
import csv

filepath = "https://raw.githubusercontent.com/aarcand3/userlist_COMP2100NetworkProgramming/main/users.json"

response = requests.get(filepath)
users = response.json()
users = {"username": ("IP", "port")}

for username, (ip, port) in users.items():
    print(f"{username} → IP: {ip}, Port: {port}")

# ---------------- TCP CLIENT CLASS ---------------- #
class TCPMailClient:
    def __init__(self, listen_port):
        self.listen_port = listen_port
        self.listener_thread = None
        self.running = False

    def _get_local_ip(self):
        """Return this machine’s local IP address."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't need to be reachable; just for routing lookup
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip  # [web:68][web:72]

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

    def stop_listener(self):
        self.running = False
        # listener thread will exit once next accept/loop completes

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
    def __init__(self, username, listen_port):
        super().__init__()
        self.username = username
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.logout_button.clicked.connect(self.logout)

        self.client = TCPMailClient(listen_port)
        self.client.start_listener(self.on_message_received)
        self.inbox = []

        local_ip = self.client._get_local_ip()
        self.update_graphics_view(
            f"User: {self.username}\nIP: {local_ip}\nListening on TCP port {listen_port}"
        )

        # Connect buttons
        self.ui.pushButton.clicked.connect(self.send_message)
        self.ui.pushButton_2.clicked.connect(self.refresh_inbox)

    def logout(self):
        """Remove user from list and close"""
        # if self.username in users:
        #    del users[self.username]
        self.client.stop_listener()
        self.window = Login()
        self.window.show()
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
        target = self.ui.sendtoEdit.text().strip()  # can be username OR ip:port
        body = self.ui.user_message.toPlainText().strip()

        if not target or not body:
            QtWidgets.QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        # -------------------------------------------------------
        # CASE 1: User entered ip:port directly
        # -------------------------------------------------------
        if ":" in target:
            try:
                relay_ip, relay_port = target.split(":")
                relay_port = int(relay_port)
                to_field = target
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Format must be username OR ip:port"
                )
                return

        # -------------------------------------------------------
        # CASE 2: User entered username → look up in dictionary
        # -------------------------------------------------------
        else:
            if target not in users:
                QtWidgets.QMessageBox.warning(self, "Error", f"Unknown user: {target}")
                return
            relay_ip, relay_port = users[target]
            to_field = target

        # -------------------------------------------------------
        # Prepare and send message
        # -------------------------------------------------------
        subject = f"Message from {self.username}"
        from_addr = (
            f"{self.username}@{self.client._get_local_ip()}:{self.client.listen_port}"
        )

        resp = self.client.send_via_relay(
            relay_ip=relay_ip,
            relay_port=relay_port,
            to=to_field,
            subject=subject,
            body=body,
            from_addr=from_addr,
        )

        self.ui.user_message.clear()
        self.update_graphics_view(
            f"Sent to {target} at {relay_ip}:{relay_port}\n{body}\n(Response: {resp})"
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
        username = self.ui.usernameEdit.text().strip()
        filepath = "userlist.csv"
        if not username:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter a username.")
            return

        if not self.ui.termsCheck.isChecked():
            QtWidgets.QMessageBox.warning(
                self, "Error", "You must accept the terms and conditions."
            )
            return

        # Choose a random free port in allowed range
        port = random.randint(1024, 65535)

        # Get this client's local IP automatically
        # (temporary TCPMailClient just to reuse _get_local_ip)
        temp_client = TCPMailClient(port)
        local_ip = temp_client._get_local_ip()

        # Register this user so others can reach them by nickname
        userdata = {username: (local_ip, port)}
        with open(filepath, mode="r") as data:
            csv_reader = csv.reader(data)
            for row in csv_reader:
                if row[0] == username:
                    QMessageBox.warning(
                        self, "Cannot Create User.", "User already exists."
                    )
                    return
                else:
                    with open(filepath, mode="a", newline="") as file:
                        writer = csv.writer(file)
                        writer.writerow(userdata)

        # Open main chat window
        self.mail_app = MailApp(username, port)
        self.mail_app.show()
        self.close()


def main():
    app = QtWidgets.QApplication(sys.argv)
    loginWindow = Login()
    loginWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
# ---------------- DASHBOARD.PY ---------------- #
