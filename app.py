import requests
from flask import Flask, request, Response, stream_with_context
import os

app = Flask(__name__)

UA = "Mozilla/5.0 (QtEmbedded; Linux) MAG250 stbapp ver:2 Safari/533.3"
PORTAL_URL = "http://tv.maxx4k.cc/stalker_portal/server/load.php"
MAC = "00:1A:79:17:1E:AA"
SN = "797995C29B984"
DID = "797995c29b984c9b0f4cd869c93cd610"

@app.route('/')
def home():
    return "Server is Running! Use: /play?ch=ChannelName"

def get_session():
    s = requests.Session()
    headers = {
        "User-Agent": UA,
        "Cookie": f"mac={MAC}; stb_lang=en; timezone=GMT",
        "Referer": "http://tv.maxx4k.cc/stalker_portal/c/"
    }
    s.headers.update(headers)
    
    try:
        # 1. Handshake
        res = s.get(f"{PORTAL_URL}?type=stb&action=handshake&JsHttpRequest=1-xml", timeout=10)
        token = res.json().get('js', {}).get('token')
        if not token: return None, None
        
        s.headers.update({"Authorization": f"Bearer {token}"})
        
        # 2. Get Profile (இதுதான் லாகின் ஆக மிக முக்கியம்)
        profile_url = f"{PORTAL_URL}?type=stb&action=get_profile&stb_type=MAG250&sn={SN}&device_id={DID}&device_id2={DID}&JsHttpRequest=1-xml"
        s.get(profile_url, timeout=10)
        
        return s, token
    except:
        return None, None

@app.route('/play')
def play():
    ch_name = request.args.get('ch')
    if not ch_name: return "Error: No Channel Name", 400

    session, token = get_session()
    if not session: return "Login Failed - Check MAC/Portal Status", 403

    try:
        # 3. Get Channels
        ch_res = session.get(f"{PORTAL_URL}?type=itv&action=get_all_channels&JsHttpRequest=1-xml")
        channels = ch_res.json().get('js', {}).get('data', [])
        
        target = next((c for c in channels if ch_name.upper() in c['name'].upper()), None)
        if not target: return f"Channel '{ch_name}' Not Found", 404

        # 4. Create Link
        cmd = target['cmds'][0]['url']
        link_res = session.get(f"{PORTAL_URL}?type=itv&action=create_link&cmd={cmd}&JsHttpRequest=1-xml")
        raw_url = link_res.json().get('js', {}).get('cmd', "").split(" ")[-1]

        # 5. Proxy Stream (Cloudflare-ல் வராத IP bypass இங்க வேலை செய்யும்)
        req = requests.get(raw_url, headers={"User-Agent": UA}, stream=True, timeout=15)
        
        return Response(stream_with_context(req.iter_content(chunk_size=1024*512)), 
                        content_type=req.headers.get('Content-Type'))
    except Exception as e:
        return f"Stream Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
