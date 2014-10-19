#!/usr/bin/python
# vim:ts=4:sw=4:ai:et:si:sts=4

"""
    Brightcove class
    Based on version from andrepl repository @ git://github.com/andrepl/plugin.video.canada.on.demand.git
"""

import time
import cgi
import datetime
import httplib
import urllib, urllib2
import re
import json

try:
    from pyamf import remoting
    has_pyamf = True
except ImportError:
    has_pyamf = False

userAgentHeaders = { "User-Agent" : "Mozilla/5.0" }
    
BRIGHTCOVE_API = "http://api.brightcove.com/services/library?"
 
# Base class ... helps with channels which are Brightcove served (AerTV and TG4)
class BrightcoveBaseChannel:
    
    def __init__(self, token="", hash_url=""):
        self.token = token
        self.hash_url = hash_url

    def get_all_videos_url(self, page_number, qsdata):
        qsdatalocal = { "token" : self.token, "command" : "search_videos",
                        "video_fields" : "id,name,customFields",
                        "custom_fields" : "tv_show", "sort_by" : "PUBLISH_DATE",
                        "page_number" : str(page_number),
                        "page_size" : str(100), "get_item_count" : True,
                      }
        qsdatalocal.update(qsdata)
        url = BRIGHTCOVE_API + urllib.urlencode(qsdatalocal)
        return url

    def get_video_desc_url(self, id):
        qsdata = { "token" : self.token, "command" : "find_video_by_id",
                   "video_fields" : "name,renditions", "video_id" : id }
        url = BRIGHTCOVE_API + urllib.urlencode(qsdata)
        return url

    def get_download_link(self, id, metadata):
        url = self.get_video_desc_url(id)
        print url
        text = ""
        try:
            req = urllib2.Request(url, None, userAgentHeaders)
            f = urllib2.urlopen(req) 
            text = f.read()
            f.close()
        except urllib2.HTTPError:
            pass

        if not text:
            return None

        data = json.loads(text)
        if not data:
            return None

        print data

        best_encoding_rate = 0
        best_url = None
        timestamp = None
        duration = None
        for item in data['renditions']:
            encoding_rate = item['encodingRate']
            if (encoding_rate > best_encoding_rate) and \
               (not item['url'].startswith('http://')):
                best_encoding_rate = encoding_rate
                best_url = item['url']
                timestamp = item.get('uploadTimestampMillis', None)
                duration = item.get('videoDuration', None)

        if best_url is None:
            print "Could not find non HDS video URL: " + url
            return False

        if timestamp is not None:
            metadata['pubDate'] = float(timestamp) / 1000.0

        if duration is not None:
            metadata['duration'] = float(duration) / 1000.0

        if best_url.startswith("http://"):
            print "This video is using HDS, which is not supporting"
            return False
        else:
            vbase, vpath = best_url.split('&')
            rtmpurl = "%s playpath=%s swfVfy=%s" % (vbase, vpath, self.hash_url)
            return rtmpurl
       
    def get_swf_url(self):
        conn = httplib.HTTPConnection('c.brightcove.com')
        qsdata = dict(width=self.flashWidth, height=self.flashHeight, flashID=self.flash_experience_id, 
                      bgcolor=self.bgColour, playerID=self.playerId, publisherID=self.publisherId,
                      isSlim='true', wmode=self.flashwmode, optimizedContentLoad='true', autoStart=self.autoStart, debuggerID='')
        qsdata['@videoPlayer'] = self.videoId
        conn.request("GET", "/services/viewer/federated_f9?&" + urllib.urlencode(qsdata))
        resp = conn.getresponse()
        location = resp.getheader('location')
        base = location.split("?",1)[0]
        location = base.replace("BrightcoveBootloader.swf", "federatedVideoUI/BrightcoveBootloader.swf")
        self.swf_url = location 
