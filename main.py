#!/usr/bin/env python3
# main.py

import sys
import json
from PyQt5 import QtWidgets, uic
from udp_mail_client import UDPMailClient

RELAY_IP = "127.0.0.1"   # change this to your relay or friend's public IP if needed
RELAY_PORT = 9999
LISTEN_PORT = 5555        # must be unique per user

class MailApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("NetworkProgramming.ui", self)  # your .ui file name

        # UI Elements
        self.send_button = self.findChild(QtWidgets.QPushButton, "pushButton")
        self.refresh_button = self.findChild(QtWidgets.QPushButton, "pushButton_2")
        self.user_input = self.findChild(QtWidgets.QLineEdit, "lineEdit")
        self.message_box = self.findChild(QtWidgets.QPlainTextEdit, "plainTextEdit")
        self.graphics_view = self.findChild(QtWidgets.QGraphicsView, "graphicsView")

        # Connect buttons
        self.send_button.clicked.connect(self.send_message)
        self.refresh_button.clicked.connect(self.refresh_inbox)

        # Initialize UDP client
        self.client = UDPMailClient(listen_port=LISTEN_PORT)
        self.client.start_listener(self.on_message_received)

        self.inbox = []  # store messages
        self.update_graphics_view("Listening on port " + str(LISTEN_PORT))

    def on_message_received(self, packet, addr):
        """Called when a UDP message arrives."""
        sender = packet.get("from", str(addr))
        subject = packet.get("subject", "(no subject)")
        body = packet.get("body", "")
        msg_text = f"From: {sender}\n{subject}\n{body}\n"
        print("Received:", msg_text)

        self.inbox.append(msg_text)
        self.update_graphics_view(msg_text)

    def send_message(self):
        """Send a message using the relay."""
        target = self.user_input.text().strip()
        body = self.message_box.toPlainText().strip()

        if not target or not body:
            QtWidgets.QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        # target format: "ip:port"
        if ":" not in target:
            QtWidgets.QMessageBox.warning(self, "Error", "Target must be in ip:port format.")
            return

        subject = "Message from UDP Mail"
        resp = self.client.send_via_relay(
            relay_addr=(RELAY_IP, RELAY_PORT),
            to=target,
            subject=subject,
            body=body,
            from_addr=f"{self.client._get_local_ip()}:{self.client.listen_port}"
        )

        self.message_box.clear()
        self.update_graphics_view(f"Sent to {target}\n{body}")
        print("Relay response:", resp)

    def refresh_inbox(self):
        """Update the inbox display."""
        self.update_graphics_view("\n\n".join(self.inbox))

    def update_graphics_view(self, text):
        """Display text in the inbox area (graphicsView)."""
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
