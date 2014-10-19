#!usr/bin/python
# vim:ts=4:sw=4:ai:et:si:sts=4

"""
    VODie
    kitesurfing@kitesurfing.ie
"""

import re
import sys
import time
from datetime import datetime
from bs4 import BeautifulSoup
import urllib, urllib2
import MenuConstants
from brightcove import BrightcoveBaseChannel
import json

userAgentHeaders = { "User-Agent" : "Mozilla/5.0" }

# URL Constants http://www.tg4.ie/en/programmes.html

BASEURL          = 'http://www.tg4.tv'
MAINURL          = BASEURL + '/index.html?l=en'

# Channel constants
CHANNEL = 'TG4'
LOGOICON = 'http://www.tg4.ie/assets/templates/tg4/images/logo-trans.png'
TOKEN = 'TpAfy9MVrSV25Xi49sYFIdS1qmF32sMqHclRGT0xOQuxwE9FnXHETQ..'
HASH_URL = 'http://admin.brightcove.com/viewer/us20130212.1339/federatedVideoUI/BrightcovePlayer.swf?uid=1360751436519'

videoFields = [ "name", "id", "referenceId", "length", "shortDescription",
                "startDate", "endDate", "publishedDate", "thumbnailURL",
                "videoStillURL", "longDescription" ]
customFields = [ "category_c", "seriestitle", "seriesimgurl", "part", "title",
                 "series", "episode", "totalparts" ]

class TG4(BrightcoveBaseChannel):
    def __init__(self):
        BrightcoveBaseChannel.__init__(self, TOKEN, HASH_URL)

    def getChannelDetail(self):
        return {'Channel'  : CHANNEL,
                'Thumb'    : LOGOICON,
                'Title'    : CHANNEL,
                'mode'     : MenuConstants.MODE_MAINMENU,
                'Plot'     : CHANNEL}
        
    def getVideoDetails(self, id, includeAds = True):
        metadata = { 'id' : id }
        metadata['url'] = self.get_download_link(id, metadata)
        if metadata['url']:
            yield metadata

    def getMainMenu(self, level = '', mode = MenuConstants.MODE_CREATEMENU):
        # Being a brightcove site (YAY), this should be simple
        qsdata = { "video_fields" : ",".join(videoFields), 
                   "custom_fields" : ",".join(customFields) }
        page = 0
        items = []
        totalCount = 0
        while True:
            url = self.get_all_videos_url(page, qsdata)

            text = ""
            try:
                req = urllib2.Request(url, None, userAgentHeaders)
                f = urllib2.urlopen(req) 
                text = f.read()
                f.close()
            except urllib2.HTTPError:
                pass

            if not text:
                break

            data = json.loads(text)
            items.extend(data['items'])
            if not totalCount:
                totalCount = data['total_count']
                lastPage = int(totalCount / 100)
                if totalCount % 100 == 0:
                    lastPage -= 1
            if page >= lastPage:
                break
            page += 1
            
        for item in items:
            desc = None
            if 'longDescription' in item and item['longDescription']:
                desc = item['longDescription']
            else:
                desc = item.get('shortDescription', None)

            metadata = {'Channel'    : CHANNEL,
                        'Thumb'      : item['thumbnailURL'],
                        'url'        : item['id'],
                        'Title'      : item['customFields']['seriestitle'],
                        'Episode'    : item['customFields']['title'],
                        'mode'       : MenuConstants.MODE_PLAYVIDEO,
                        'Duration'   : float(item['length']) / 1000.0,
                        'pubDate'    : float(item['publishedDate']) / 1000.0,
                        'seriesNum'  : item['customFields']['series'],
                        'episodeNum' : item['customFields']['episode'],
            }
            if desc:
                metadata['Plot'] = desc
            yield metadata

    def getMenuItems(self, type):
        if type == MenuConstants.MODE_MAINMENU:
            return self.getMainMenu()
        else:
            return self.getMainMenu(level = type, mode = MenuConstants.MODE_GETEPISODES)
        
if __name__ == '__main__':
    tg4 = TG4()
    for item in tg4.getMainMenu():
        print item
        for video in tg4.getVideoDetails(item['url']):
            print video
