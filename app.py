import requests
from flask import Flask, request, Response, stream_with_context
import os

app = Flask(__name__)

# சாதன விவரங்கள்
UA = "Mozilla/5.0 (QtEmbedded; Linux) MAG250 stbapp ver:2 Safari/533.3"
PORTAL_URL = "http://tv.maxx4k.cc/stalker_portal/server/load.php"
MAC = "00:1A:79:17:1E:AA"
SN = "797995C29B984"
DID = "797995c29b984c9b0f4cd869c93cd610"

def get_auth():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "Cookie": f"mac={MAC}; stb_lang=en; timezone=GMT",
        "Referer": "http://tv.maxx4k.cc/stalker_portal/c/"
    })
    try:
        # Handshake - இங்க்தான் 403 எர்ரர் வர வாய்ப்புள்ளது
        res = s.get(f"{PORTAL_URL}?type=stb&action=handshake&JsHttpRequest=1-xml", timeout=10)
        data = res.json()
        token = data.get('js', {}).get('token')
        if not token: return None, "No Token Found"
        
        s.headers.update({"Authorization": f"Bearer {token}"})
        # Profile Auth
        s.get(f"{PORTAL_URL}?type=stb&action=get_profile&stb_type=MAG250&sn={SN}&device_id={DID}&device_id2={DID}&JsHttpRequest=1-xml", timeout=10)
        return s, token
    except Exception as e:
        return None, str(e)

@app.route('/')
def home():
    return "MSC Proxy Server Running. Use /play?ch=NAME"

@app.route('/play')
def play():
    ch_name = request.args.get('ch')
    if not ch_name: return "Channel Name Required", 400

    session, error_msg = get_auth()
    if not session: return f"Login Failed: {error_msg}", 403

    try:
        # Get Channels
        r = session.get(f"{PORTAL_URL}?type=itv&action=get_all_channels&JsHttpRequest=1-xml")
        channels = r.json().get('js', {}).get('data', [])
        
        target = next((c for c in channels if ch_name.upper() in c['name'].upper()), None)
        if not target: return "Channel Not Found", 404

        # Create Link
        cmd = target['cmds'][0]['url']
        l_res = session.get(f"{PORTAL_URL}?type=itv&action=create_link&cmd={cmd}&JsHttpRequest=1-xml")
        raw_url = l_res.json().get('js', {}).get('cmd', "").split(" ")[-1]

        # Video Streaming
        v_res = requests.get(raw_url, headers={"User-Agent": UA}, stream=True, timeout=20)
        return Response(stream_with_context(v_res.iter_content(chunk_size=1024*512)), content_type=v_res.headers.get('Content-Type'))
    except Exception as e:
        return f"Streaming Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
