# scripts/webhook_server.py
from flask import Flask, request, jsonify
import smtplib, ssl, os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

def send_email(subject, html_body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = os.getenv("SENDER_EMAIL")
    msg["To"]      = os.getenv("EMAIL_ADDRESS")
    msg.attach(MIMEText(html_body, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(
        os.getenv("EMAIL_SMTP_SERVER"),
        int(os.getenv("EMAIL_SMTP_PORT", 465)),
        context=context
    ) as server:
        server.login(os.getenv("EMAIL_ADDRESS"), os.getenv("EMAIL_PASSWORD"))
        server.sendmail(msg["From"], msg["To"], msg.as_string())

@app.route("/webhook/health-update", methods=["POST"])
def health_update():
    data = request.json
    score  = data.get("score", 100)
    artist = data.get("artist", "Unknown")

    if score < 40:
        status_label = "CRITICAL"
        color        = "#c0392b"
    elif score < 60:
        status_label = "AT RISK"
        color        = "#e67e22"
    else:
        return jsonify({"status": "healthy, no action"}), 200

    subject = f"[{status_label}] {artist} — Health Score {score}/100"

    html = f"""
    <h2 style='color:{color}'>{status_label} — Artist Health Alert</h2>
    <table style='border-collapse:collapse;width:100%'>
      <tr><td style='padding:8px;border:1px solid #ddd'><strong>Artist</strong></td>
          <td style='padding:8px;border:1px solid #ddd'>{artist}</td></tr>
      <tr><td style='padding:8px;border:1px solid #ddd'><strong>Score</strong></td>
          <td style='padding:8px;border:1px solid #ddd'>{score}/100 — {status_label}</td></tr>
      <tr><td style='padding:8px;border:1px solid #ddd'><strong>Days Since Contact</strong></td>
          <td style='padding:8px;border:1px solid #ddd'>{data.get('days_since_contact', 'N/A')}</td></tr>
      <tr><td style='padding:8px;border:1px solid #ddd'><strong>Trend</strong></td>
          <td style='padding:8px;border:1px solid #ddd'>{data.get('trend', 'N/A')}</td></tr>
      <tr><td style='padding:8px;border:1px solid #ddd'><strong>Top Action</strong></td>
          <td style='padding:8px;border:1px solid #ddd'>{data.get('top_action', 'N/A')}</td></tr>
      <tr><td style='padding:8px;border:1px solid #ddd'><strong>Suggested Check-in</strong></td>
          <td style='padding:8px;border:1px solid #ddd'>{data.get('check_in_message', 'N/A')}</td></tr>
    </table>
    <p style='color:#888;font-size:12px'>Sent by MAESTRO BRIDGE — {data.get('timestamp', '')}</p>
    """

    send_email(subject, html)
    return jsonify({"status": f"{status_label} alert sent"}), 200

if __name__ == "__main__":
    app.run(port=5678)