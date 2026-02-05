from flask import Flask, redirect, Response, request, stream_with_context
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# போர்ட்டல் விவரங்கள்
BASE_URL = "http://tv.maxx4k.cc/stalker_portal"
MAC = "00:1A:79:17:1E:AA"
SN = "797995C29B984"
DID = "797995c29b984c9b0f4cd869c93cd610"
UA = "Mozilla/5.0 (QtEmbedded; U; Linux; C) AppleWebKit/533.3 (KHTML, like Gecko) MAG200 stbapp ver: 2 rev: 250 Safari/533.3"

TARGET_CHANNELS = {
    "7S MUSIC": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/7S-Music.png",
    "AATHAVAN": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Athavan-TV.png",
    "ADITHYA": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Adithya-TV.png",
    "COLORS TAMIL": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Colors-Tamil-HD.png",
    "DD TAMIL": "https://yt3.googleusercontent.com/gOPDl0p0Ssungy3AfKG9MNHeW1QEwRmoFw0_dwDsUulDPE5Hv9nicA3MCjYyzYInzw8kbd5C=s900-c-k-c0x00ffffff-no-rj",
    "J MOVIE": "https://jiotvimages.cdn.jio.com/dare_images/images/J_Movies.png",
    "JAYA TV": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Jaya-TV-HD.png",
    "JAYA MAX": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Jaya-Max.png",
    "ISAI ARUVI": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Isaiaruvi.png",
    "MURASU": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Murasu-TV.png",
    "SIRIPPOLI": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Sirippoli-1.png",
    "KALAIGNAR": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Kalaignar-TV-1.png",
    "KTV": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/KTV-HD.png",
    "NDTV LANKA": "https://i0.wp.com/tamilultra.icu/wp-content/uploads/2025/10/NDTV_LANKA.png",
    "MOON TV": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Moon.png",
    "POLIMER TV": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Polimer.png",
    "PUTHUYUGAM": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Puthiya-Yugam.png",
    "RAJ TV": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Raj-TV.png",
    "RAJ DIGITAL": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Raj-Digital-Plus.png",
    "RAJ MUSIX": "https://jiotvimages.cdn.jio.com/dare_images/images/Raj_Musix.png",
    "SUN TV": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Sun-TV-HD.png",
    "SUN MUSIC": "https://jiotvimages.cdn.jio.com/dare_images/images/Sun_Music_HD.png",
    "SUN LIFE": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Sun-Life.png",
    "STAR VIJAY": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Star-Vijay-HD.png",
    "TVI": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/TVi.png",
    "TAMILAN TV": "https://jiotv.catchup.cdn.jio.com/dare_images/images/Tamilan_Television.png",
    "TUNES 6": "https://jiotvimages.cdn.jio.com/dare_images/images/Tunes_6.png",
    "VASANTH": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Vasanth-TV.png",
    "VENDHAR": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Vendhar.png",
    "VASANTHAM": "https://i0.wp.com/tamilultra.icu/wp-content/uploads/2023/06/Vasantham_TV.png",
    "VIJAY TAKKAR": "https://jiotv.catchup.cdn.jio.com/dare_images/images/Vijay_Takkar.png",
    "VIJAY SUPER": "https://jiotv.catchup.cdn.jio.com/dare_images/images/Vijay_Super_HD.png",
    "ZEE TAMIL": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Zee-Tamil-HD.png",
    "ZEE THIRAI": "http://b1gchlogos.xyz/wp-content/uploads/2023/08/Zee-Thirai.png"
}

def get_auth_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA,
        "X-User-Agent": "Model: MAG250; Link: WiFi",
        "Cookie": f"mac={MAC}; stb_lang=en; timezone=GMT",
        "Referer": f"{BASE_URL}/c/"
    })
    try:
        api = f"{BASE_URL}/server/load.php"
        r = s.get(f"{api}?type=stb&action=handshake&JsHttpRequest=1-xml", timeout=10).json()
        token = r.get("js", {}).get("token")
        if not token: return None, None
        s.get(f"{api}?type=stb&action=get_profile&stb_type=MAG250&sn={SN}&device_id={DID}&JsHttpRequest=1-xml", 
              headers={"Authorization": f"Bearer {token}"})
        return s, token
    except:
        return None, None

@app.route('/')
def home():
    return "IPTV Playlist Server is Running. Get your M3U at /tamil.m3u"

@app.route('/tamil.m3u')
def generate_m3u():
    s, token = get_auth_session()
    if not token: return "Portal Connection Error", 500
    
    api = f"{BASE_URL}/server/load.php"
    try:
        c_res = s.get(f"{api}?type=itv&action=get_all_channels&JsHttpRequest=1-xml", 
                      headers={"Authorization": f"Bearer {token}"}).json()
        channels = c_res.get("js", {}).get("data", [])
    except:
        return "Fetch Error", 500

    m3u = "#EXTM3U\n"
    # Koyeb-ல் https தானாக வரும் என்பதால் host-ஐ சரியாக எடுக்கிறோம்
    host = request.host_url.rstrip('/')
    
    for ch in channels:
        name = ch.get("name", "")
        name_up = name.upper()
        
        matched_logo = None
        for key, url in TARGET_CHANNELS.items():
            if key in name_up:
                matched_logo = url
                break
        
        if matched_logo:
            cmd_url = ch.get("cmds", [{}])[0].get("url", "")
            # Play URL-ல் cmd-ஐ encode செய்து அனுப்புகிறோம்
            import urllib.parse
            safe_cmd = urllib.parse.quote(cmd_url)
            m3u += f'#EXTINF:-1 tvg-logo="{matched_logo}" group-title="Tamil",{name}\n{host}/play?cmd={safe_cmd}\n'
            
    return Response(m3u, mimetype='text/plain')

@app.route('/play')
def play():
    cmd = request.args.get('cmd')
    s, token = get_auth_session()
    if not token or not cmd: return "Stream Error", 500
    api = f"{BASE_URL}/server/load.php"
    try:
        res = s.get(f"{api}?type=itv&action=create_link&cmd={cmd}&JsHttpRequest=1-xml", 
                    headers={"Authorization": f"Bearer {token}"}).json()
        real_url = res.get("js", {}).get("cmd", "").split(" ")[-1]
        
        # Proxy Streaming: வீடியோவை சர்வர் வழியாக அனுப்புகிறது
        v_res = requests.get(real_url, headers={"User-Agent": UA}, stream=True, timeout=15)
        return Response(stream_with_context(v_res.iter_content(chunk_size=1024*256)), 
                        content_type=v_res.headers.get('Content-Type'))
    except:
        return "Link Generation Error", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
