import requests
from flask import Flask, request, Response, stream_with_context

app = Flask(__name__)

UA = "Mozilla/5.0 (QtEmbedded; Linux) MAG250 stbapp ver:2 Safari/533.3"
PORTAL = {
    "url": "http://tv.maxx4k.cc/stalker_portal/server/load.php",
    "mac": "00:1A:79:17:1E:AA",
    "sn": "797995C29B984",
    "did": "797995c29b984c9b0f4cd869c93cd610"
}

def get_auth_token():
    headers = {
        "User-Agent": UA,
        "Cookie": f"mac={PORTAL['mac']}; stb_lang=en; timezone=GMT",
        "Referer": "http://tv.maxx4k.cc/stalker_portal/c/"
    }
    try:
        # Handshake
        r = requests.get(f"{PORTAL['url']}?type=stb&action=handshake&JsHttpRequest=1-xml", headers=headers, timeout=10)
        token = r.json().get('js', {}).get('token')
        if not token: return None
        
        # Get Profile
        requests.get(f"{PORTAL['url']}?type=stb&action=get_profile&stb_type=MAG250&sn={PORTAL['sn']}&device_id={PORTAL['did']}&device_id2={PORTAL['did']}&JsHttpRequest=1-xml", 
                     headers={**headers, "Authorization": f"Bearer {token}"}, timeout=10)
        return token
    except:
        return None

@app.route('/play')
def play():
    ch_name = request.args.get('ch')
    if not ch_name:
        return "Channel name required", 400

    token = get_auth_token()
    if not token:
        return "Login Failed", 403

    headers = {"User-Agent": UA, "Authorization": f"Bearer {token}"}
    
    # Get All Channels
    r = requests.get(f"{PORTAL['url']}?type=itv&action=get_all_channels&JsHttpRequest=1-xml", headers=headers)
    channels = r.json().get('js', {}).get('data', [])
    
    # Find Match
    target = next((c for c in channels if ch_name.upper() in c['name'].upper()), None)
    if not target:
        return "Channel Not Found", 404

    # Create Link
    r_link = requests.get(f"{PORTAL['url']}?type=itv&action=create_link&cmd={target['cmds'][0]['url']}&JsHttpRequest=1-xml", headers=headers)
    raw_url = r_link.json().get('js', {}).get('cmd', "").split(" ")[-1]

    # --- Video Proxy Streaming Logic ---
    req = requests.get(raw_url, headers={"User-Agent": UA}, stream=True)
    
    def generate():
        for chunk in req.iter_content(chunk_size=1024*1024): # 1MB chunks
            yield chunk

    return Response(stream_with_context(generate()), content_type=req.headers.get('Content-Type'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
