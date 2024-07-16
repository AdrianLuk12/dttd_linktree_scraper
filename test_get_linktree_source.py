import requests
from bs4 import BeautifulSoup
import json

res = requests.get("https://linktr.ee/cktc")

if res.status_code == 200:
    print(res.status_code)
    """
    with open("data.html", "wb") as output:
        output.write(res.content)
    print("data saved")
    """

source = res.content
soup = BeautifulSoup(source, 'html.parser')
attributes = {"id":"__NEXT_DATA__"}
user_info = soup.find('script', attrs=attributes)
user_data = json.loads(user_info.contents[0])["props"]["pageProps"]

with open("source.json", "w") as output:
    json.dump(user_data, output, indent=4)