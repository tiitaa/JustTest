#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
from urllib import parse
import re, os, shutil, io
import json
import time

def processbar(percent):
    edge = chr(9474)
    #pl = range(9601, 9609)
    pl = range(9615, 9607, -1)

    num = int(min(1, abs(percent)) * 200)
    s0 = num // len(pl)
    s1 = num % len(pl)
    m = 200 // len(pl)
    ss0 = chr(pl[-1]) * s0
    ss1 = chr(pl[s1 - 1]) if s1 > 0 else ''
    ss2 = ' ' * (25 - s0) if s1 == 0 else ' ' * (m - 1 - s0)
    return '{ed}{fin}{part}{blank}{ed}'.format(
            ed=edge, fin=ss0, part=ss1, blank=ss2)

def reqget(url):
    for i in range(5):
        try:
            with requests.get(url, timeout=3) as rq:
                return rq
        except (requests.exceptions.BaseHTTPError,
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout) as err :
            print('\n{} {}'.format(url, err))
            time.sleep(3)
            print('retry {}'.format(i+1))
    raise requests.exceptions.Timeout(url)

def validDir(d):
    dp, dn = os.path.split(d)
    dn = dn.strip('.')
    dn = dn.strip(' ')
    dn = dn.replace('|', '')
    dn = dn.replace('?', '？')
    return os.path.join(dp, dn)

class dllog:
    def __init__(self, url='none', fname='comicdl_log.log'):
        self.url = url
        self.fname = fname
        self.json = dict()
        try:
            with io.open(fname, 'r', encoding='utf8') as fobj:
                self.json = json.load(fobj)
        except BaseException:
            pass
        if url not in self.json.keys():
            self.json[url] = dict()
        self.uj = self.json[url]

    def __getitem__(self, idx):
        if idx in self.uj.keys():
            return self.uj[idx]
        return ''

    def __setitem__(self, idx, val):
        self.uj[idx] = val
        return self

    def save(self):
        with io.open(self.fname, 'w', encoding='utf8') as fobj:
            json.dump(self.json, fobj, indent=2, ensure_ascii=False)
            #fobj.write(u'%s' %(json.dumps(self.json, indent=2)))


def dlchapter(cdir, urls):
    cdir = validDir(cdir)
    if not os.path.isdir(cdir):
        shutil.os.makedirs(cdir, exist_ok=True)

    def dlimg(url, fname):
        if os.path.exists(fname):
            return None
        with reqget(url) as r, open(fname, 'wb') as fobj:
            fobj.write(r.content)

    urls = list(urls)
    cl = len(urls)

    for n, i in enumerate(urls, start=1):
        fname = '{:03d}{}'.format(n, os.path.splitext(i)[1])
        fname = os.path.join(cdir, fname)
        dlimg(i, fname)
        print('\r {} dl {}/{}    \b\b\b\b'.format(processbar(n/cl), n, cl), end='')

    print('')


class comicdl:
    comicwebs = dict()
    def __init__(self, url):
        netloc = parse.urlparse(url).netloc
        if netloc not in self.comicwebs.keys():
            raise TypeError('Unsupport website {}'.format(netloc))
        self.webparse = self.comicwebs[netloc](url)

    @classmethod
    def webreg(cls, c):
        netloc = parse.urlparse(c.home).netloc
        cls.comicwebs[netloc] = c
        return c

    def download(self, start=0, end=None, cmd = ''):
        title = self.webparse.title
        self.dllog = dllog(title, os.path.join(title, 'download.log'))
        chapters = self.webparse.chapters[start:end]
        print('title: {}'.format(title))
        idx = start-1
        #self.dllog['title'] = title

        for chap, link in chapters:
            idx += 1
            if self.dllog[chap] == '':
                self.dllog[chap] = dict()
                self.dllog[chap]['finish'] = False
            self.dllog[chap]['link'] = link
            if self.dllog[chap]['finish'] == True and cmd != 'redownload':
                continue

            print('download [{}] {} ...'.format(idx, chap))
            chapimgs = self.webparse.chapimgs(link)
            print('\r {} ft {}/{}'.format(processbar(1), len(chapimgs), len(chapimgs)), end='')
            dlchapter(os.path.join(title, chap), chapimgs)
            self.dllog[chap]['finish'] = True

            self.dllog.save()

@comicdl.webreg
class manhua123:
    home = 'https://m.manhua123.net'
    imgbase = 'https://img.detatu.com'

    def __init__(self, url):
        self.url = url
        with reqget(url) as r:
            self.soup = BeautifulSoup(r.content, 'lxml')

        self.title = self.soup.find('div', class_='data').find('h4').string.strip()

        c = self.soup.find('ul', class_="list_block show").findAll('a')
        self.chapters = [(a.string, parse.urljoin(url, a['href'])) for a in c]

    def chapimgs(self, link):
        with reqget(link) as r:
            s = BeautifulSoup(r.content, 'lxml')
            imgs = list(filter(lambda a: a.string is not None and 'z_img' in a.string, s.findAll('script')))
            imgs = re.findall('"(.+?)"', imgs[0].string)
            return list(map(lambda url:parse.urljoin(self.imgbase, url), imgs))
        return list()


@comicdl.webreg
class gufengmh8:
    home = 'https://m.gufengmh8.com'
    imgbase = 'https://res.xiaoqinre.com'

    def __init__(self, url):
        self.url = url
        with reqget(url) as r:
            self.soup = BeautifulSoup(r.content, 'lxml')

        self.title = self.soup.find('h1', class_='title').string.strip()

        c = self.soup.find('div', class_='list').findAll('a')
        self.chapters = [(a.span.string, parse.urljoin(url, a['href'])) for a in c]

    def chapimgs(self, link):
        with reqget(link) as r:
            s = BeautifulSoup(r.content, 'lxml')
            ss = list(filter(lambda a: a.string is not None and 'chapterImages' in a.string, s.findAll('script')))
            ss = ss[0].string
            imgs = re.findall(r'chapterImages(.*?);', ss)
            imgs = re.findall('"(.+?)"', imgs[0])
            imgpath = re.findall(r'chapterPath(.*?);', ss)
            imgpath = re.findall('"(.+?)"', imgpath[0])[0]
            imgbase = re.findall(r'pageImage(.*?);', ss)
            imgbase = re.findall('"(.+?)"', imgbase[0])[0]
            return list(map(lambda url:parse.urljoin(self.imgbase, os.path.join(imgpath,url)), imgs))
        return list()

@comicdl.webreg
class bnmanhua:
    home = 'https://m.bnmanhua.com'
    imgbase = 'https://img.yaoyaoliao.com'

    def __init__(self, url):
        self.url = url
        with reqget(url) as r:
            self.soup = BeautifulSoup(r.content, 'lxml')

        self.title = self.soup.find('div', class_='data').h4.string.strip()

        c = self.soup.find('div', class_="tabs_block").findAll('a')
        self.chapters = [(a.string, parse.urljoin(url, a['href'])) for a in c]

    def chapimgs(self, link):
        with reqget(link) as r:
            s = BeautifulSoup(r.content, 'lxml')
            ss = list(filter(lambda a: a.string is not None and 'z_img' in a.string, s.findAll('script')))
            ss = ss[0].string
            imgs = re.findall(r'z_img(.*?);', ss)
            imgs = re.findall('"(.+?)"', imgs[0])
            return list(map(lambda url:parse.urljoin(self.imgbase, url.replace('\\/', '/')), imgs))
        return list()

@comicdl.webreg
class m90mh:
    home = 'http://m.90mh.com'
    imgbase = 'https://img.yaoyaoliao.com'

    def __init__(self, url):
        self.url = url
        with reqget(url) as r:
            self.soup = BeautifulSoup(r.content, 'lxml')

        self.title = self.soup.find(class_='title').string.strip()
        self.chapters = list()

        cs = self.soup.findAll(class_='comic-chapters')
        for c in cs:
            ct = c.find('h3').string.strip()
            if len(cs) < 2:
                ct = ''
            cts = c.findAll('a')
            self.chapters += [(os.path.join(ct, a.span.string.strip()),
                parse.urljoin(url, a['href']))
                    for a in cts]

    def chapimgs(self, link):
        imgs = list()
        if len(link) < 3:
            return imgs
        while True:
            with reqget(link) as r:
                soup = BeautifulSoup(r.content, 'lxml')
                p_c = int(soup.find(attrs={'id':'k_page'}).string.strip())
                p_t = int(soup.find(attrs={'id':'k_total'}).string.strip())
                imgs.append(soup.find('mip-img')['src'])
                link = soup.find('mip-img').parent['href']
                print('\r {} ft {}/{}'.format(processbar(p_c/p_t), p_c, p_t), end='')
                if p_c == p_t:
                    break
        return imgs


def dlall():
    urls = [
            #'https://m.bnmanhua.com/comic/17708.html', # 鬼灭之刃 富冈义勇外传
            #'https://m.bnmanhua.com/comic/847.html', # 鬼灭之刃
            #'https://m.manhua123.net/comic/8333.html', # 恶之华
            'https://m.gufengmh8.com/manhua/luoxiaoheizhanjilanxizhen/', # 罗小黑
            'https://m.gufengmh8.com/manhua/yirenzhixia/', # 一人之下
            'https://m.gufengmh8.com/manhua/zhenhunjie/', # 镇魂街
            #'https://m.bnmanhua.com/comic/23886.html', # 欢迎回来爱丽丝
            #'https://m.bnmanhua.com/comic/12837.html', # 博人传
            #'http://m.90mh.com/manhua/wodexianshishilianaiyouxi/', # 我的现实
            #'http://m.90mh.com/manhua/jishengshouyilingyin/', # 寄生兽医铃音
            #'http://m.90mh.com/manhua/yiquanchaoren/', # 一拳超人
            #'http://m.90mh.com/manhua/GrandBlue/', # 碧海之蓝
            ]

    for url in urls:
        try:
            comicdl(url).download()
        except requests.exceptions.Timeout:
            pass

if __name__ == '__main__':
    dlall()


