#!/usr/bin/env python3
"""
udp_mail_client.py
Client library for sending/receiving "mail" over UDP.

Example:
  client = UDPMailClient(listen_ip='0.0.0.0', listen_port=5555)
  client.start_listener(on_message_callback)   # runs a background thread
  client.send_via_relay(relay_addr=('relay.example', 9999), to='10.0.0.5:6666', subject='Hi', body='Hello')

Callback signature:
  def on_msg(packet_dict, source_addr):
      # packet_dict is the parsed JSON message
"""

import socket
import threading
import json
import time
from PyQt5 import QtWidgets
import sys
from Dashboard import Ui_MainWindow

BUFFER_SIZE = 8192

class UDPMailClient:
    def __init__(self, listen_ip='0.0.0.0', listen_port=0, recv_buffer=BUFFER_SIZE):
        """
        listen_port: the local UDP port your UI wants to receive mail on.
        If listen_port is 0, the OS selects a free port; get it with client.listen_port after start.
        """
        self.listen_ip = listen_ip
        self.listen_port = int(listen_port)
        self.recv_buffer = recv_buffer
        self._sock = None
        self._listener_thread = None
        self._running = False
        self.on_message = None  # set to callback(packet_dict, addr)

    def start_listener(self, on_message_callback=None):
        """Start a background thread that listens for incoming UDP messages."""
        if self._running:
            raise RuntimeError("Listener already running")
        self.on_message = on_message_callback
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind((self.listen_ip, self.listen_port))
        # update port if OS chose one
        self.listen_port = self._sock.getsockname()[1]
        self._running = True
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()
        return self.listen_port

    def _listen_loop(self):
        while self._running:
            try:
                data, addr = self._sock.recvfrom(self.recv_buffer)
                try:
                    packet = json.loads(data.decode('utf-8'))
                except Exception:
                    # If it's not JSON, wrap it
                    packet = {"from_raw": data.decode('utf-8', errors='replace')}
                # call callback if set
                if self.on_message:
                    try:
                        self.on_message(packet, addr)
                    except Exception as cb_e:
                        print("Error in on_message callback:", cb_e)
                else:
                    print("Received message (no callback):", packet, "from", addr)
            except OSError:
                break
            except Exception as e:
                print("Listener error:", e)
                time.sleep(0.05)

    def stop_listener(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except:
                pass
            self._sock = None
        if self._listener_thread:
            self._listener_thread.join(timeout=0.5)
            self._listener_thread = None

    def send_via_relay(self, relay_addr, to, subject="", body="", metadata=None, from_addr=None, timeout=2.0):
        """
        Send a message to relay_addr (host, port). The relay will forward to the `to` ip:port.
        relay_addr: (host, port)
        to: "ip:port" string
        from_addr: optional "ip:port" string to include; if omitted, the relay may attach sender info
        """
        msg = {
            "to": to,
            "subject": subject,
            "body": body,
            "metadata": metadata or {}
        }
        if from_addr:
            msg["from"] = from_addr
        data = json.dumps(msg).encode('utf-8')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            try:
                s.sendto(data, relay_addr)
                # Optionally read an immediate response (e.g. error packet) from relay
                try:
                    resp, _ = s.recvfrom(BUFFER_SIZE)
                    try:
                        resp_json = json.loads(resp.decode('utf-8'))
                        return resp_json
                    except Exception:
                        return {"raw_response": resp.decode('utf-8', errors='replace')}
                except socket.timeout:
                    # No reply from relay (common); treat as success
                    return {"status": "sent_no_reply"}
            except Exception as e:
                return {"error": str(e)}

    def send_direct(self, to_addr, subject="", body="", metadata=None, timeout=2.0):
        """
        Send directly to a destination (skips relay).
        to_addr: tuple (ip, port)
        """
        msg = {
            "from": f"{self._get_local_ip()}:{self.listen_port if self.listen_port else 0}",
            "to": f"{to_addr[0]}:{to_addr[1]}",
            "subject": subject,
            "body": body,
            "metadata": metadata or {}
        }
        data = json.dumps(msg).encode('utf-8')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            try:
                s.sendto(data, to_addr)
                return {"status": "direct_sent"}
            except Exception as e:
                return {"error": str(e)}

    def _get_local_ip(self):
        # heuristic: connect to a public DNS and read the local socket's name (doesn't actually send)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'

if __name__ == "__main__":
    # quick demo when run as a script
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    def demo_cb(packet, addr):
        print("Demo received:", packet, "from", addr)

    client = UDPMailClient(listen_port=5555)
    port = client.start_listener(demo_cb)
    print("Listening on port", port)
    print("Send a message to this client using the relay or direct UDP.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping client.")
        client.stop_listener()
