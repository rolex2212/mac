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
    return "MSC Proxy Server is Active. Use /play?ch=NAME"

def get_auth_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Cookie": f"mac={MAC}; stb_lang=en; timezone=GMT",
        "Referer": "http://tv.maxx4k.cc/stalker_portal/c/"
    })
    try:
        # Handshake
        h_res = s.get(f"{PORTAL_URL}?type=stb&action=handshake&JsHttpRequest=1-xml", timeout=10)
        h_data = h_res.json()
        token = h_data.get('js', {}).get('token')
        
        if not token: return None, "Handshake failed - No Token"

        s.headers.update({"Authorization": f"Bearer {token}"})
        # Profile Authorization
        p_res = s.get(f"{PORTAL_URL}?type=stb&action=get_profile&stb_type=MAG250&sn={SN}&device_id={DID}&device_id2={DID}&JsHttpRequest=1-xml", timeout=10)
        
        return s, token
    except Exception as e:
        return None, str(e)

@app.route('/play')
def play():
    ch_name = request.args.get('ch')
    if not ch_name: return "Channel name missing", 400

    session, error = get_auth_session()
    if not session: return f"Login Failed: {error}", 403

    try:
        # Fetch Channels
        r = session.get(f"{PORTAL_URL}?type=itv&action=get_all_channels&JsHttpRequest=1-xml")
        channels = r.json().get('js', {}).get('data', [])
        
        target = next((c for c in channels if ch_name.upper() in c['name'].upper()), None)
        if not target: return "Channel Not Found", 404

        # Create Link
        cmd = target['cmds'][0]['url']
        l_res = session.get(f"{PORTAL_URL}?type=itv&action=create_link&cmd={cmd}&JsHttpRequest=1-xml")
        raw_url = l_res.json().get('js', {}).get('cmd', "").split(" ")[-1]

        # Video Proxying
        req = requests.get(raw_url, headers={"User-Agent": UA}, stream=True, timeout=15)
        return Response(stream_with_context(req.iter_content(chunk_size=1024*512)), content_type=req.headers.get('Content-Type'))
    except Exception as e:
        return f"Streaming Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
