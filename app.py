from flask import Flask, render_template, request, jsonify
import asyncio
import threading
import time
import re
import requests
from bs4 import BeautifulSoup
import user_agent
import uuid
import random
import json
from datetime import datetime
from faker import Faker
import string
import os
import urllib.request
import hmac
import hashlib

app = Flask(__name__)

fake = Faker("ar_SA")
MOHMAL_BASE_URL = "https://www.mohmal.com"
MOHMAL_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Google Chrome\";v=\"138\"",
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": "\"Android\"",
    "upgrade-insecure-requests": "1",
    "sec-fetch-site": "same-origin",
    "sec-fetch-mode": "navigate",
    "sec-fetch-user": "?1",
    "sec-fetch-dest": "document",
    "accept-language": "ar-EG,ar;q=0.9,en-US;q=0.8,en;q=0.7",
    "priority": "u=0, i"
}

# ────────────────────────────────────────────────
# Classes (same as before – short rakha hai, pura original logic yahan paste kar sakte ho)
class TempEmailService:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(MOHMAL_HEADERS)
        self.temp_email = None

    def create_temp_email(self):
        try:
            r = self.session.get(MOHMAL_BASE_URL + "/ar/create/random", timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            div = soup.find("div", class_="email")
            if div and "data-email" in div.attrs:
                self.temp_email = div["data-email"]
                return self.temp_email, "Temp email created"
        except Exception as e:
            return None, f"Temp email error: {str(e)}"
        return None, "Temp email create failed"

    def poll_for_message(self, poll_interval=4, max_attempts=60):
        for _ in range(max_attempts):
            try:
                r = self.session.get(MOHMAL_BASE_URL + "/ar/inbox", timeout=12)
                soup = BeautifulSoup(r.text, "html.parser")
                row = soup.select_one("#inbox-table tbody tr.unseen[data-msg-id]")
                if row:
                    return row["data-msg-id"], "Message received"
                time.sleep(poll_interval)
            except:
                time.sleep(poll_interval)
        return None, "No message received (timeout)"

    def fetch_full_message(self, msg_id):
        try:
            r = self.session.get(f"{MOHMAL_BASE_URL}/ar/message/{msg_id}", timeout=12)
            return r.text, "Message fetched"
        except Exception as e:
            return None, f"Fetch error: {str(e)}"

    def parse_confirmation_code(self, html):
        if not html:
            return None, "No content"
        soup = BeautifulSoup(html, "html.parser")
        td = soup.select_one("td[style*='font-size:32px']")
        if td:
            code = td.get_text(strip=True)
            if code.isdigit():
                return code, "Code parsed"
        return None, "Code not found"

# InstagramCreator simplified for web
class InstagramCreator:
    def __init__(self):
        self.session = requests.Session()
        self.time = str(time.time()).split('.')[1]
        self.user_agent = user_agent.generate_user_agent()

    def get_headers(self):
        return {
            'User-Agent': self.user_agent,
            'x-csrftoken': "8D26VZbnpmxsokorogKvshOiKojeTii5",
            'x-instagram-ajax': '1021370996',
            'x-ig-app-id': '1217981644879628',
            'Referer': 'https://www.instagram.com/accounts/emailsignup/',
        }

    async def create_temp_account(self):
        yield "Starting account creation...\n"

        email_service = TempEmailService()
        email, msg = email_service.create_temp_email()
        if not email:
            yield f"❌ {msg}\n"
            return
        yield f"📧 {msg}: {email}\n"

        if not self.check_email_availability(email):
            yield "❌ Email not available\n"
            return
        yield "Email available ✅\n"

        if not self.send_verification_email(email):
            yield "❌ Verification email send failed\n"
            return
        yield "Verification email sent ✅\n"

        msg_id, msg = email_service.poll_for_message()
        if not msg_id:
            yield f"❌ {msg}\n"
            return
        yield f"📩 {msg}\n"

        html, msg = email_service.fetch_full_message(msg_id)
        if not html:
            yield f"❌ {msg}\n"
            return
        yield f"{msg}\n"

        code, msg = email_service.parse_confirmation_code(html)
        if not code:
            yield f"❌ {msg}\n"
            return
        yield f"🔑 Code found: {code}\n"

        signup_code = self.verify_code(email, code)
        if not signup_code:
            yield "❌ Code verification failed\n"
            return
        yield "Code verified successfully ✅\n"

        success, acc = self.create_account(email, signup_code)
        if success:
            yield "🎉 ACCOUNT CREATED SUCCESSFULLY!\n"
            yield f"Email: {acc['email']}\n"
            yield f"Username: {acc['username']}\n"
            yield f"Password: {acc['password']}\n"
            yield f"DOB: {acc['birth_date']}\n"
            yield "Saved in created_accounts.json\n"
        else:
            yield "❌ Final creation failed (likely challenge or block)\n"

    def check_email_availability(self, email):
        time.sleep(random.uniform(1, 3))
        url = "https://www.instagram.com/api/v1/web/accounts/check_email/"
        try:
            r = self.session.post(url, data={'email': email}, headers=self.get_headers(), timeout=12)
            return '"available":true' in r.text
        except:
            return False

    def send_verification_email(self, email):
        time.sleep(random.uniform(1, 3))
        url = "https://www.instagram.com/api/v1/accounts/send_verify_email/"
        payload = {'device_id': "Z8-eMwABAAH5f09r6VWab1y0iA86", 'email': email}
        try:
            r = self.session.post(url, data=payload, headers=self.get_headers(), timeout=12)
            return '"email_sent":true' in r.text
        except:
            return False

    def verify_code(self, email, code):
        time.sleep(random.uniform(1, 3))
        url = "https://www.instagram.com/api/v1/accounts/check_confirmation_code/"
        payload = {'code': code, 'device_id': "Z8-eMwABAAH5f09r6VWab1y0iA86", 'email': email}
        try:
            r = self.session.post(url, data=payload, headers=self.get_headers(), timeout=12)
            return r.json().get('signup_code')
        except:
            return None

    def create_account(self, email, signup_code):
        time.sleep(random.uniform(2, 5))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=14))
        username = f"{fake.user_name()}_{random.randint(100,999)}"
        first_name = fake.first_name()
        day, month, year = random.randint(1,28), random.randint(1,12), random.randint(1990,2005)
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/"
        payload = {
            'enc_password': f"#PWD_INSTAGRAM_BROWSER:0:{self.time}:{password}",
            'day': str(day),
            'month': str(month),
            'year': str(year),
            'email': email,
            'first_name': first_name,
            'username': username,
            'client_id': "Z8-eMwABAAH5f09r6VWab1y0iA86",
            'seamless_login_enabled': "1",
            'tos_version': "row",
            'force_sign_up_code': signup_code,
        }
        try:
            r = self.session.post(url, data=payload, headers=self.get_headers(), timeout=20)
            if '"account_created":true' in r.text:
                acc = {
                    'email': email,
                    'username': username,
                    'password': password,
                    'first_name': first_name,
                    'birth_date': f"{year}/{month:02d}/{day:02d}",
                    'created_at': datetime.now().isoformat()
                }
                # Save to file
                accounts = []
                if os.path.exists("created_accounts.json"):
                    try:
                        with open("created_accounts.json", "r") as f:
                            accounts = json.load(f)
                    except:
                        pass
                accounts.append(acc)
                with open("created_accounts.json", "w") as f:
                    json.dump(accounts, f, indent=2)
                return True, acc
            return False, None
        except:
            return False, None

# ────────────────────────────────────────────────
# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    def generate_stream():
        creator = InstagramCreator()
        for status in creator.create_temp_account():
            yield f"data: {status}\n\n"
            time.sleep(0.1)  # smooth streaming

    return app.response_class(generate_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)