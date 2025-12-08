# Network Programming Project

# NetworkProject – TCP Mail Relay (PyQt5)

NetworkProject is a simple **TCP-based mail/chat application** built with **Python 3**, **PyQt5**, and **sockets**.  
It lets users on the same network send and receive text messages using **direct IP:port addresses**, and it includes a work-in-progress system for sending by **username** via a CSV-based user list.

***

## Features

- GUI built with **PyQt5** for login and messaging windows.  
- Peer-to-peer style messaging over **TCP sockets** with each client listening on its own port.  
- Background listener thread for incoming messages on a chosen port.  
- Simple user “directory” concept stored in `userlist.csv` for mapping usernames to IP/port (not fully functional yet).  
- Ability to address recipients by **direct IP:port**.  
- **Planned**: fully working “send by username” (nickname lookup) based on `userlist.csv`.

***

## Requirements

- **Python 3.8+**
- **PyQt5** installed:
  ```bash
  pip install PyQt5
  ```
- Project files in a folder named **`NetworkProject`**:
  - `main.py` – main application logic (login, mail UI, TCP client)
  - `Dashboard.py` – dashboard (main window) UI class `Ui_MainWindow`
  - `login.py` – login window UI class `Ui_loginWindow`
  - `userlist.csv` – CSV file conceptually storing usernames and their last-known IP/port

The `userlist.csv` file should exist before first run (it can be empty).

Use a simple comma-separated format like:

```text
username,IP,port
```

This is intended to act as a minimal, file-based registry so users can eventually be contacted by nickname instead of manually entering IP and port.

***

## How to Run

### From the terminal

From the `NetworkProject` folder:

```bash
cd NetworkProject
python3 main.py
```

1. The **Login** window opens.  
2. Enter a **username**.  
3. Check the **terms and conditions** box.  
4. Click **Login**.

On successful login:

- A random TCP port is chosen for this client.  
- The app detects your local IP address.  
- The app attempts to register your username, IP, and port in `userlist.csv` (this registration logic is part of the work-in-progress username feature).  
- The **Dashboard** window opens and starts listening for incoming TCP messages on your assigned port.

### From Visual Studio Code

You can also run the app directly from **VS Code**:

1. Open the `NetworkProject` folder in VS Code.  
2. Open `main.py`.  
3. Ensure the correct Python interpreter is selected in the status bar.  
4. Click the **Run** (▶) button at the top-right of the editor (or use “Run > Start Debugging”) to start the application.

***

## Using the App

### Sending Messages

Right now, the reliably supported way to address a recipient is **by IP:port**:

- Type an explicit address like `192.168.1.23:5050` into the “To” field.

Then:

1. Type your message text in the message box.  
2. Click **Send**.  
3. The application builds a JSON-like packet containing `from`, `to`, `subject`, and `body`, opens a TCP connection to the target `(IP, port)`, and sends the data.  
4. A log entry appears in the dashboard, indicating the destination, message body, and any response (for example, “Message sent” or an error string).

#### Username sending (not working yet)

The code and CSV setup include an intended feature to send messages by **username** (nickname):

- The idea is that you would type a username (stored in `userlist.csv`) into the “To” field, and the application would look up that username’s IP and port and send the message there.  
- **However, this username-based sending is not working yet and is considered a work-in-progress feature.**  
- Future versions are planned to improve the CSV handling and lookup logic so that username addressing works reliably.

For now, use **direct IP:port** to ensure messages are delivered.

***

### Receiving Messages

Each running client starts a background TCP listener on its assigned port.

- When a message arrives, the listener:
  - Accepts the incoming connection.  
  - Reads the JSON payload.  
  - Extracts sender, subject, and body.  
  - Stores a formatted string in an in-memory `inbox` list.

- The latest message is displayed in the dashboard’s graphics view.  
- Clicking **Refresh Inbox** re-renders all messages received during the current session.

Messages are not persisted to disk; they exist only in memory for that run.

***

### Logging Out

- Click **Logout** in the dashboard.  
- The listener is stopped, the main window closes, and the login window is shown again.

The CSV record for that username is **not** automatically removed on logout, so `userlist.csv` effectively acts as a simple, accumulating address book of known users (though nickname sending is not yet fully wired up).

***

## Local Testing Example

To test with two local clients on a single machine:

1. Open two terminals and in each run:

   ```bash
   cd NetworkProject
   python3 main.py
   ```

2. In each window, log in as a different user, for example:
   - Terminal 1 → username: `alice`  
   - Terminal 2 → username: `bob`

3. Once both dashboards are open:
   - From Alice’s window, send a message to Bob using `127.0.0.1:<bob_port>`.  
   - From Bob’s window, send a message to Alice using `127.0.0.1:<alice_port>`.

The username field and `userlist.csv` are present but should be treated as experimental until the nickname lookup path is fully implemented.

***

## Project Structure

```text
NetworkProject/
├── main.py          # Main app: TCPMailClient, MailApp, Login, entry point
├── Dashboard.py     # PyQt5 UI for main mail dashboard (Ui_MainWindow)
├── login.py         # PyQt5 UI for login window (Ui_loginWindow)
├── userlist.csv     # CSV-based user directory (username, IP, port; used by WIP nickname feature)
└── README.md        # Project documentation
```

This structure can be extended with tests, configuration files, or packaging metadata as the project grows.

***

## Possible Improvements

Some ideas for extending the project:

- Fix and complete the username-based sending path (robust CSV read/write, safe lookups, and clear error handling).  
- Replace `userlist.csv` with a more robust storage option (for example, SQLite) once the nickname feature stabilizes.  
- Add authentication and/or basic encryption for message payloads.  
- Persist inbox messages to disk for history across sessions.  
- Enhance the UI with timestamps, message bubbles, separate “Sent” and “Received” panes, and better error dialogs.
