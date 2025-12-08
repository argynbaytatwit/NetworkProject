# Network Programming Project

Here’s a nicely formatted **README.md** draft that you can include directly in your GitHub repository. It’s structured for clarity, professionalism, and visual readability, matching typical open-source standards.  

***

# TCP Mail Relay App (PyQt5)

A simple **TCP-based mail/chat application** built using **Python 3**, **PyQt5**, and **sockets**.  
It lets users send and receive text messages over a local network by **username** or **IP:port**, simulating a minimal peer-to-peer mailing system.

***

## 🚀 Features

- GUI built with **PyQt5**
- **TCP relay** for sending and receiving messages  
- Local IP and port detection  
- Background listener using threads  
- **User registration** via a local CSV file  
- Message inbox and sent logs
- Lightweight — no centralized server needed!

***

## 🛠️ Requirements

Before running, make sure you have:

- **Python 3.8+**
- **PyQt5** installed:
  ```bash
  pip install PyQt5
  ```
- Supporting files:
  - `Dashboard.py` – main GUI layout
  - `login.py` – login screen interface
  - `userlist.csv` – local record of registered users

📝 The `userlist.csv` file should exist before first run. It can be empty or have initial users:

```
username,IP,port
```

***

## 💻 How to Run

1. Clone this repository  
   ```bash
   git clone https://github.com/<your-username>/tcp-mail-relay.git
   cd tcp-mail-relay
   ```
2. Run the main program  
   ```bash
   python3 main.py
   ```
3. The **Login Window** appears. Enter:
   - A **username** (unique)
   - Check the **terms and conditions** box  
   Click **Login** to continue.

4. A random port is assigned, and your details are automatically added to `userlist.csv`.

***

## ✉️ Using the App

### Sending Messages
You can send messages in **two ways**:

#### 1. By Username  
Type the username in the *"To"* field.
- The app looks up that user in `userlist.csv`.

#### 2. By IP:Port  
Type a direct address like:
```
192.168.1.15:5000
```

Then:
1. Write your message in the main text box.  
2. Click **Send**.  
3. The message is sent via TCP and acknowledged in the inbox area.

***

### Receiving Messages

The app launches a **background listener** thread on your port.  
When a message arrives, it automatically appears in your inbox area with:

```
From: sender_name@ip:port
Subject: Message from sender
Body: message text
```

Click **Refresh Inbox** to display all received messages again during the session.

***

### Logging Out

- Click **Logout** to stop the listener and return to the login screen.  
- Currently, `userlist.csv` is not cleared on logout, so you may see existing usernames if you reopen the app.

***

## 🧑‍💻 Local Testing Setup

You can test with multiple clients on the same machine:

1. Open two terminals.  
2. In both, run:
   ```bash
   python3 main.py
   ```
3. Log in as two different users (e.g., `alice` and `bob`).  
4. Use each window to send messages to the other via username or `127.0.0.1:<port>`.

***

## 🔧 Troubleshooting

- **`Address already in use`** → Restart app to get a new random port.  
- **No message received** → Check firewall or that both clients are on the same network.  
- **Invalid JSON** → Usually caused by corrupted message transmission.  
- **User already exists** → Remove that username’s line from `userlist.csv` or use a new name.

***

## 🧩 File Structure

```
tcp-mail-relay/
│
├── main.py             # Main application (listener + UI logic)
├── Dashboard.py        # Main dashboard design (PyQt5)
├── login.py            # Login window GUI (PyQt5)
├── userlist.csv        # Local CSV database (username, IP, port)
└── README.md           # You are here
```

***

## 📡 How It Works (Simplified Diagram)

```
+------------+         TCP Socket         +------------+
|  Client A  |  ----------------------->  |  Client B  |
| (Listener) |  <-----------------------  | (Listener) |
+------------+                            +------------+
       ↑                                         ↑
   sends message                           background
   via IP:Port or username                  listener
```

Each client runs its own **TCP listener** and can directly connect to others using their registered IP and port.

***

## 🧠 Future Improvements

- Replace CSV with a small SQLite database.  
- Add encryption or authentication layers.  
- Implement persistent inbox history.  
- Improve UI elements (chat-like display, timestamps).

***

Would you like this README to include example screenshots (mockups or placeholders) for the login and dashboard sections?
