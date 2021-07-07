import os
import time
import requests
from tqdm import tqdm
from datetime import datetime

s = requests.Session()

# User configuration
GCP_API_KEY = 'YOUR_API_KEY' # https://developers.google.com/youtube/v3/getting-started

# Script configuration
VIDEO_IDS_FILE = 'videos.txt'
UNAVAILABLE_IDS_FILE = 'unavailable.txt'
PUBLIC_IDS_FILE = 'public.txt'
UNLISTED_IDS_FILE = 'unlisted.txt'
UNLISTED_IDS_BEFORE_2017_FILE = 'unlisted-before-17.txt'
STATE_FILE = 'state.txt'
VIDEOS_PER_REQUEST = 50

# Read YouTube video IDs from file
with open(VIDEO_IDS_FILE) as f:
    ids = f.read().splitlines()

# Check state
try:
    with open(STATE_FILE) as f:
        index = int(f.read())
except FileNotFoundError:
    index = 0
    pass

# Chunk video ids to reduce API requests
videoIdChunks = [','.join(ids[i:i + VIDEOS_PER_REQUEST]) for i in range(0, len(ids), VIDEOS_PER_REQUEST)]
videoIdChunks = videoIdChunks[index:]

for videoIdChunk in tqdm(videoIdChunks):
    url = f'https://www.googleapis.com/youtube/v3/videos?key={GCP_API_KEY}&part=snippet,status&id={videoIdChunk}'
    res = requests.get(url)

    if res.status_code != 200:
        print('API returned non-200 status code, sleeping 3600 seconds')
        print(res.status_code)
        print(res.text)
        time.sleep(3600)

    data = res.json()

    requestedVideoIds = videoIdChunk.split(',')
    returnedVideoIds = [item['id'] for item in data['items']]
    unavailableVideoIds = [item for item in requestedVideoIds if item not in returnedVideoIds]

    if len(unavailableVideoIds) > 0:
        with open(UNAVAILABLE_IDS_FILE, 'a+') as f:
            f.write('\n'.join(unavailableVideoIds).strip() + '\n')

    for item in data['items']:
        id = item['id']
        privacyStatus = item['status']['privacyStatus']
        videoDate = datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%SZ')

        if privacyStatus == 'public':
            with open(PUBLIC_IDS_FILE, 'a+') as f:
                f.write('{}\n'.format(id))
        elif privacyStatus == 'unlisted':
            with open(UNLISTED_IDS_FILE, 'a+') as f:
                f.write('{}\n'.format(id))
            if videoDate.year < 2017:
                with open(UNLISTED_IDS_BEFORE_2017_FILE, 'a+') as f:
                    f.write('{}\n'.format(id))
    
    index += 1
    
    with open(STATE_FILE, 'w+') as f:
        f.write(str(index))

os.remove(STATE_FILE)
