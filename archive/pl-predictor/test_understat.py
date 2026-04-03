import requests
from bs4 import BeautifulSoup
import re
import json

url = 'https://understat.com/league/EPL/2023'
html = requests.get(url).text
soup = BeautifulSoup(html, 'html.parser')
scripts = soup.find_all('script')
for script in scripts:
    if script.string and 'datesData' in script.string:
        match = re.search(r"datesData\s+=\s+JSON\.parse\('(.*?)'\);", script.string)
        if match:
            data = json.loads(match.group(1).encode('utf-8').decode('unicode_escape'))
            print("Successfully extracted datesData!", len(data), "matches.")
            print(data[0])
            break
