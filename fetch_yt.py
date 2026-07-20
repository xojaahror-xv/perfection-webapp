import urllib.request
import re
import json

url = 'https://www.youtube.com/results?search_query=english+focus+zamonlar'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')

video_ids = re.findall(r'"videoId":"(.*?)"', html)
titles = re.findall(r'"title":\{"runs":\[\{"text":"(.*?)"\}\]', html)

videos = []
seen = set()
for i, vid in enumerate(video_ids):
    if vid not in seen and len(videos) < 6:
        seen.add(vid)
        # title extraction might be slightly misaligned, let's just try to get some text
        print(f'{vid}')
