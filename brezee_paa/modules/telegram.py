import requests

API_KEY = "6842267895:AAGxMOazbjg5Jxf6r3E2cjED9gRRvEvMPak"
CHAT_ID = "-600274878"

class TG:

    def __init__(self) -> None:
        self.url = f"https://api.telegram.org/bot{API_KEY}"

    def _send(self, message):
        url = f"{self.url}/sendMessage?chat_id={CHAT_ID}&text={message}"
        x = requests.get(url)

        if x.status_code == 200:
            print("Message sent successfully !!!")