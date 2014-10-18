#!/usr/bin/python
# vim:ts=4:sw=4:ai:et:si:sts=4

"""
    VODie

    Updated AnLar scraper, handles several channels

    liam.friel@gmail.com

"""

import re
import sys
import urllib, urllib2
import MenuConstants
from datetime import date
from pyvirtualdisplay import Display
from selenium import webdriver
from bs4 import BeautifulSoup
import bs4
import json

# Channel Constants
CHANNEL = 'An Lar'
MAINURL = 'http://anlar.tv'
ANLARLOGO = 'http://anlar.tv/images/stories/logo1.png'

class Anlar:
    def __init__(self):
        pass

    def getChannelDetail(self):

        return {'Channel'  : CHANNEL,
                'Thumb'    : ANLARLOGO,
                'Title'    : 'An Lar',
                'mode'     : MenuConstants.MODE_MAINMENU,
                'Plot'     : 'An Lar'
                }

    def getMainMenu(self):

        # Load and read the URL. Not amenable to parsing entirely with regex, too crapiful

        headers = { 'User-Agent' : 'Mozilla/5.0' }
        req = urllib2.Request(MAINURL, None, headers)
        page = urllib2.urlopen(req)
        soup = BeautifulSoup(page)
        page.close()

        divs = soup.findAll("div", {"class" : "fusion-submenu-wrapper level2"})
        # Channels are in divs[0]
        bullets = divs[0].findAll("li")

        for bullet in bullets:
            chanString = str(bullet)

            REGEXP = '<a\s+.*href="(.*?)">\s*<span>\s*(.*?)\s*</span>\s*</a>'
            match = re.search(REGEXP, chanString, re.MULTILINE)
            if match:
                yield {'Channel' : CHANNEL,
                       'Thumb'   : ANLARLOGO,
                       'url'     : match.group(1),
                       'Title'   : match.group(2),
                       'mode'    : MenuConstants.MODE_PLAYVIDEO}

    def getVideoDetails(self, url):

        # Load and read the URL
        if not url.startswith("http://"):
            url = MAINURL + url

        self.browser.get(url)
        text = self.browser.page_source

        soup = BeautifulSoup(text)

        elems = soup("param", attrs={'name': 'flashvars'})
        flashvars = None
        if elems:
            flashvars = elems[0]['value'].replace("config=", "")
            flashvars = json.loads(flashvars)

        if not flashvars:
            articles = soup.find_all("div", class_="rt-article")
            if articles:
                article = articles[0]
                for titles in article.find_all("h1"):
                    title = titles.stripped_strings
                    strings = list(title)
                    title = " ".join(strings)
                    for elem in titles.next_siblings:
                        if type(elem) is bs4.element.NavigableString:
                            continue
                        if elem.name == 'h1' or elem.name == 'div':
                            break
                        if elem.name == 'p':
                            elem = elem.find_all("a")
                            if not elem:
                                continue
                            elem = elem[0]
                        if elem.name == 'a':
                            url = elem['href']
                            episode = elem.stripped_strings
                            strings = list(episode)
                            episode = " ".join(strings)
                            elem = elem.img
                            thumb = elem['src']
                            details = self.getVideoDetails(url)
                            details = list(details)
                            details = details[0]
                            if details:
                                del details['Genre']
                                channel = CHANNEL + " Video Archives"
                                details['Channel'] = channel
                                details['Director'] = channel
                                details['Title'] = title
                                details['Episode'] = episode
                                details['Thumb'] = thumb
                                details['url'] = details['url'].replace(" app=live ", " ")
                                yield details
        else: 
            playPath = None
            swf = None
            rtmpServer = None

            clip = flashvars.get('clip', None)
            if clip:
                playPath = clip.get('url', None)

            plugins = flashvars.get('plugins', None)
            if plugins:
                rtmp = plugins.get('rtmp', None)
                if rtmp:
                    swf = rtmp.get('url', None)
                    rtmpServer = rtmp.get('netConnectionUrl', None)

            if rtmpServer and swf and playPath:
                rtmpURL = '%s app=live swfUrl=%s playpath=%s' %(rtmpServer, swf, playPath)

                channel = CHANNEL + " " + playPath
                yield {'Channel'     : channel,
                       'Title'       : channel,
                       'Director'    : channel,
                       'Genre'       : playPath,
                       'id'          : rtmpURL,
                       'url'         : rtmpURL
                       }

    def startBrowser(self):
        self.display = Display(visible=0, size=(800, 600))
        self.display.start()
        self.browser = webdriver.Firefox()

    def stopBrowser(self):
        self.browser.quit()
        self.display.stop()

    def getAllVideosByTitle(self, titles, type="main"):
        regexp = re.compile("^(" + "|".join(titles) + ")$")
        channels = self.getMainMenu()

        videos = []
        try:
            anlar.startBrowser()

            for channel in channels:
                for detail in anlar.getVideoDetails(channel['url']):
                    vids.append(detail)
        finally:
            anlar.stopBrowser()

        videos = [ item for item in videos if regexp.match(item['Title']) ]

        return videos


if __name__ == '__main__':

    anlar = Anlar()
    channels = anlar.getMainMenu()

    vids = []
    try:
        anlar.startBrowser()

        for channel in channels:
            for detail in anlar.getVideoDetails(channel['url']):
                vids.append(detail)
    finally:
        anlar.stopBrowser()

    with open("all.Anlar.json", "w") as f:
        f.write(json.dumps(vids))

    titles = { item['Title'] for item in vids }
    with open("titles.Anlar.json", "w") as f:
        f.write(json.dumps(list(titles)))

    print vids
