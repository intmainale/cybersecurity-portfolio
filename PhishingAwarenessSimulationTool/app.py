from flask import Flask, render_template, request, Response
from tracking.track_events import tracking_events
from tracking.generate_links import generate_tracking_links
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

@app.route("/")
def init():
    send_emails("user1@test.com")
    return render_template('training_page.html')

@app.route("/track")
def tracking():
    user_id = request.args.get('id')
    action = request.args.get('action')
    email_id = request.args.get('email')

    try:
        tracking_events(user_id, action, email_id)
    except Exception as e:
        print("TRACK ERROR:", e)

    # 1. If it's the hidden tracking pixel loading, return the invisible GIF
    if action == "mail_opened":
        pixel = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        return Response(pixel, mimetype="image/gif")

    # 2. If they clicked 'report' or 'no_report', send them to the educational page
    elif action in ["report", "no_report"]:
        # You can pass variables to the template if you want to customize it
        # based on which email they clicked from, or if they got it right/wrong!
        return render_template('training_page.html')
        
    # Fallback for unexpected actions
    return "Invalid action", 400

def send_emails(user_email):
    info = {
        "email1": ("Security Alert", "security-training@company.local")
    }
    #for i in range(1, 6):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = info["email1"][0]
    msg["From"] = info["email1"][1]
    msg["To"] = user_email
    links = generate_tracking_links()[user_email]
    html = render_template(
        f"email_templates/email1.html",
        user="Employee",
        tracking_link1 = links[0]+"&email=1",
        tracking_link2 = links[1]+"&email=1",
        tracking_link3 = links[2]+"&email=1"
    )
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP("mailhog", 1025) as server:
        server.sendmail(msg["From"], msg["To"], msg.as_string())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)