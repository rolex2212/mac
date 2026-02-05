import requests
import json
import base64
from colorama import Fore, Style, init

# வண்ணங்களை அமைத்தல்
init(autoreset=True)
GREEN, YELLOW, BLUE, RED = Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.RED

# சாதனத் தகவல்கள் (Configuration)
UA = "Mozilla/5.0 (QtEmbedded; Linux) MAG250 stbapp ver:2 Safari/533.3"
PORTAL = {
    "NAME": "Maxx4K",
    "BASE_URL": "http://tv.maxx4k.cc/stalker_portal",
    "MAC": "00:1A:79:17:1E:AA",
    "DID": "797995c29b984c9b0f4cd869c93cd610",
    "SN": "797995C29B984"
}

class PortalFetcher:
    def __init__(self, portal_config):
        self.config = portal_config
        self.api_url = f"{portal_config['BASE_URL']}/server/load.php"
        self.session = requests.Session()
        self.token = None
        
        # Headers அமைத்தல்
        self.session.headers.update({
            "User-Agent": UA,
            "X-User-Agent": "Model: MAG250",
            "Cookie": f"mac={self.config['MAC']}; stb_lang=en; timezone=GMT",
            "Referer": f"{self.config['BASE_URL']}/c/"
        })

    def login(self):
        """படி 1: Handshake மற்றும் லாகின் செய்தல்"""
        print(f"{YELLOW}[1/4] லாகின் செய்யப்படுகிறது: {self.config['NAME']}...{Style.RESET_ALL}")
        try:
            # Handshake
            r = self.session.get(f"{self.api_url}?type=stb&action=handshake&JsHttpRequest=1-xml", timeout=10)
            self.token = r.json().get("js", {}).get("token")
            
            if not self.token:
                print(f"{RED}Error: Token கிடைக்கவில்லை!{Style.RESET_ALL}")
                return False

            # Get Profile (அங்கீகாரத்தை உறுதி செய்ய)
            profile_params = (
                f"&sn={self.config['SN']}&device_id={self.config['DID']}"
                f"&device_id2={self.config['DID']}&JsHttpRequest=1-xml"
            )
            self.session.get(
                f"{self.api_url}?type=stb&action=get_profile&stb_type=MAG250{profile_params}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            print(f"{GREEN}லாகின் வெற்றி!{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{RED}Login Error: {e}{Style.RESET_ALL}")
            return False

    def get_genre_id(self, search_title="TAMIL"):
        """படி 2: குறிப்பிட்ட கேட்டகிரி ஐடியை கண்டறிதல்"""
        print(f"{YELLOW}[2/4] கேட்டகிரி தேடப்படுகிறது: {search_title}...{Style.RESET_ALL}")
        try:
            r = self.session.get(
                f"{self.api_url}?type=itv&action=get_genres&JsHttpRequest=1-xml",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            genres = r.json().get("js", [])
            for g in genres:
                if search_title.upper() in g.get("title", "").upper():
                    return g.get("id")
        except: pass
        return "0"

    def fetch_channels(self, genre_id):
        """படி 3: அனைத்து சேனல் தகவல்களையும் எடுத்தல்"""
        print(f"{YELLOW}[3/4] சேனல்கள் பட்டியலிடப்படுகின்றன...{Style.RESET_ALL}")
        try:
            url = f"{self.api_url}?type=itv&action=get_all_channels&genre={genre_id}&JsHttpRequest=1-xml"
            r = self.session.get(url, headers={"Authorization": f"Bearer {token}"})
            return r.json().get("js", {}).get("data", [])
        except:
            return []

    def get_stream_link(self, cmd):
        """படி 4: வீடியோ பிளே ஆகும் லிங்க் உருவாக்குதல்"""
        try:
            url = f"{self.api_url}?type=itv&action=create_link&cmd={cmd}&JsHttpRequest=1-xml"
            r = self.session.get(url, headers={"Authorization": f"Bearer {self.token}"})
            real_link = r.json().get("js", {}).get("cmd", "")
            # கூடுதல் தேவையற்ற வார்த்தைகளை நீக்குதல்
            return real_link.replace("ffrt ", "").replace("ffmpeg ", "").split(" ")[-1]
        except:
            return None

# செயல்படுத்தும் முறை (Main Execution)
if __name__ == "__main__":
    fetcher = PortalFetcher(PORTAL)
    
    if fetcher.login():
        # தமிழ் சேனல்களை மட்டும் எடுக்க
        tamil_id = fetcher.get_genre_id("TAMIL")
        channels = fetcher.fetch_channels(tamil_id)
        
        print(f"\n{BLUE}மொத்தம் கண்டறியப்பட்ட சேனல்கள்: {len(channels)}{Style.RESET_ALL}")
        print("-" * 50)
        
        for ch in channels[:10]: # உதாரணத்திற்கு முதல் 10 சேனல்கள்
            name = ch.get("name")
            cmd = ch.get("cmds", [{}])[0].get("url", "")
            
            if cmd:
                link = fetcher.get_stream_link(cmd)
                print(f"{Fore.CYAN}சேனல்: {name}")
                print(f"{Fore.WHITE}லிங்க்: {link}\n")
