# 🟢 Uptime Kuma Scripts

A collection of Python scripts for automating and managing [Uptime Kuma](https://github.com/louislam/uptime-kuma) monitors via its API. Whether you're bulk-importing monitors from a spreadsheet or programmatically updating existing ones, these scripts are designed to save you time and reduce manual work.

---

## 📋 Scripts

| Script | Description |
|---|---|
| `uptime_kuma_csv_import.py` | Imports monitors into Uptime Kuma from a CSV file |
| `update_kuma_monitors.py` | Updates existing monitors in Uptime Kuma via the API |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- A running [Uptime Kuma](https://github.com/louislam/uptime-kuma) instance
- API access enabled on your Uptime Kuma instance

### Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/uptime-kuma-scripts.git
   cd uptime-kuma-scripts
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

The update_kuma_monitors.pw script requires credentials and connection details for your Uptime Kuma instance. These can be provided via environment variables or a `.env` file in the project root.

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `KUMA_URL` | Base URL of your Uptime Kuma instance | `http://localhost:3001` |
| `KUMA_USERNAME` | Your Uptime Kuma username | `admin` |
| `KUMA_PASSWORD` | Your Uptime Kuma password | `yourpassword` |
|---|---|---|
| `TARGET_INTERVAL` | How often to check (seconds). UI label: "Heartbeat Interval" | 60 |
| `TARGET_RETRY_INTERVAL` | How long to wait between retry attempts after a failure (seconds). UI label: "Heartbeat Retry Interval" | 60 |
| `TARGET_MAX_RETRIES` | How many consecutive failures before marking as DOWN and alerting. UI label: "Retries" | `yourpassword` |
| `TARGET_RESEND_INTERVAL` | How many times to re-send the DOWN alert while the monitor stays down. 0 is send once | 0 |
| `TARGET_METHOD` | HTTP method to use.  "HEAD" is faster (no body download). Options: "GET", "HEAD", "POST", "PUT", "PATCH", "DELETE" | HEAD |
| `TARGET_EXPIRY_NOTIFICATION` | Alert when the TLS/SSL certificate is about to expire. UI label: "Certificate Expiry Notification" | true |
| `TARGET_DOMAIN_EXPIRY_NOTIFICATION` | Alert when the domain name registration is about to expire. UI label: "Domain Name Expiry Notification" | true |
|---|---|---|
| `TARGET_MAX_REDIRECTS` | Maximum redirects to follow. 0 = disable redirect following. Leave unset or empty in .env to leave untouched on existing monitors. | 10 |
| `TARGET_TIMEOUT` | Request timeout in seconds. UI label: "Request Timeout" — leave unset or empty to leave untouched. | None |
| `TARGET_IGNORE_TLS` | Ignore TLS/SSL certificate errors (useful for self-signed certs). Leave unset or empty to leave untouched. | None |
| `TARGET_ACCEPTED_STATUSCODES` | Accepted HTTP status code ranges. Leave unset or empty to leave untouched. | None |

### Using a `.env` File

Create a `.env` file in the project root:

```env
     KUMA_URL=http://localhost:3001
     KUMA_USERNAME=admin
     KUMA_PASSWORD=your_password_here

     TARGET_INTERVAL=60
     TARGET_RETRY_INTERVAL=60
     TARGET_MAX_RETRIES=1
     TARGET_RESEND_INTERVAL=0
     TARGET_METHOD=HEAD
     TARGET_EXPIRY_NOTIFICATION=true
     TARGET_DOMAIN_EXPIRY_NOTIFICATION=true
     TARGET_MAX_REDIRECTS=10
     # Leave optional fields unset (or empty) to leave them untouched:
     # TARGET_TIMEOUT=
     # TARGET_IGNORE_TLS=
     # TARGET_ACCEPTED_STATUSCODES=

```
None tells the update monitor script to not update.

> ⚠️ **Never commit your `.env` file.** It is included in `.gitignore` by default.

---

## 📖 Usage

### `uptime_kuma_csv_import.py`

Imports monitors in bulk from a CSV file. Useful for initial setup or migrating monitors from another system.

**CSV Format:**

Your CSV should include a header row with at minimum the following columns:

```
url
example.com
api.example.com/health
```

**Usage:**

```bash
python uptime_kuma_csv_import.py --file monitors.csv
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `--file` | ✅ | Path to the CSV file containing monitor definitions |
| `--dry-run` | ❌ | Preview what would be imported without making changes |

---

### `update_kuma_monitors.py`

Updates the configuration of existing monitors via the Uptime Kuma API. Useful for making bulk changes without editing monitors one by one in the UI.

**Usage:**

```bash
python update_kuma_monitors.py
```

**Arguments:**

Currently there are no arguments as there are just defaults being set in the script.

---

## 🤝 Contributing

Contributions are welcome! If you have a script that extends Uptime Kuma's functionality, or improvements to existing ones, feel free to open a pull request.

### How to Contribute

1. **Fork** the repository
2. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and commit with a clear message:
   ```bash
   git commit -m "Add: script to export monitors to CSV"
   ```
4. **Push** to your fork and open a **Pull Request** against `main`

### Guidelines

- Keep scripts focused — one script, one purpose
- Include a docstring or comment block at the top of each script explaining what it does, required arguments, and any dependencies
- Update this README if you're adding a new script
- Be sure your script doesn't hardcode credentials — use environment variables

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

Built on top of the excellent [Uptime Kuma](https://github.com/louislam/uptime-kuma) project by [Louis Lam](https://github.com/louislam).
