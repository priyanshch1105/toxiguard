# SentinelGuard Chrome Extension

Highlights toxic comments on YouTube, LinkedIn, and WhatsApp Web using the SentinelGuard API.

## Load in Chrome / Edge

1. Start the Flask app (`python run.py`) or use your Render URL.
2. Open `chrome://extensions` (Edge: `edge://extensions`).
3. Turn on Developer mode.
4. Click Load unpacked and select this `extension` folder.
5. Pin SentinelGuard, open the popup, and set API URL:
   - Local: `http://127.0.0.1:5000`
   - Render: `https://your-app.onrender.com`
6. Open YouTube comments, LinkedIn feed, or WhatsApp Web and click Scan visible messages.

## Notes

- Works in the browser only, not in native mobile apps.
- WhatsApp Web DOM changes often; scan again if badges do not appear.
- Messages are sent to your API for classification.
