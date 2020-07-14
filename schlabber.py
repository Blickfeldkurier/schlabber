#!/usr/bin/env python3
import os
import stat
import argparse
import requests
import json
import pprint
import hashlib
from bs4 import BeautifulSoup

class Soup:
    def assertdir(self,dirname):
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def has_valid_timestamp(self, meta):
        return meta and 'time' in meta and meta['time']

    def __init__(self, soup, bup_dir):
        self.rooturl = "http://"+soup+".soup.io"
        self.bup_dir = os.path.abspath(bup_dir)
        self.assertdir(self.bup_dir)
        self.dlnextfound = False
        self.sep = os.path.sep
        print("Backup: " + self.rooturl)
        print("into: " + self.bup_dir)
    
    def find_next_page(self, cur_page, cur_url):
        for script in cur_page.find_all('script'):
            if script.string and "SOUP.Endless.next_url" in script.string:
                self.dlnextfound = True
                url = script.string.split('\'')[-2].strip()
                print("\t...found script: " + url)
                return url
        for more in cur_page.find_all('a', class_='more'):
            if more['href'] and "since" in more['href']:
                self.dlnextfound=True
                url = more['href'].strip()
                print("\t...found pagination: " + url)
                return url
        self.dlnextfound = False
        return cur_url
    
    def get_asset_name(self, name):
        return name.split('/')[-1].split('.')[0]
    
    def get_timstemp(self, post):
        for time_meta in post.find_all("abbr"):
            return time_meta.get('title').strip().split(" ")
        return None
    
    def process_image(self, post, dlurl):
        print("\t\tImage:")
        meta = {'soup_page' : dlurl}
        meta['time'] = self.get_timstemp(post)
        for caption in post.find_all("div", {'class': 'caption'}):
            meta['source'] = caption.find('a').get("href")
        for desc in post.find_all("div", {'class': 'description'}):
            meta['text'] = desc.get_text()
        for link in post.find_all('div', {"class":"imagecontainer"}):
            lightbox = link.find("a", {"class": "lightbox"})
            if lightbox:
                meta['soup_url'] = lightbox.get('href')
            else:
                meta['soup_url'] = link.find("img").get('src')
        if 'soup_url' in meta:
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_url: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                self.assertdir(basepath + "meta" + self.sep )
                with open(basepath + "meta" + self.sep + filename + ".json", 'w') as outfile:
                    json.dump(meta, outfile)

    def process_quote(self, post):
        print("\t\tQuote:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        body = post.find("span", {"class", 'body'}).get_text()
        author = post.find("cite").get_text()
        quote = '"' + body + '"' + "\n\t" + author + "\n"
        qhash = hashlib.sha256(quote.encode())
        hashsum = str(qhash.hexdigest().upper())
        filename = "quote_" + hashsum + ".txt"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            self.assertdir(basepath)
            print("\t\t\t-> " + path)
            with open(path, "w") as qf:
                qf.write(quote)

    def process_link(self, post, dlurl):
        print("\t\tLink:")
        meta = {'soup_page' : dlurl}
        meta['time'] = self.get_timstemp(post)
        linkelem = post.find("h3")
        meta["link_title"] = linkelem.get_text().strip()
        meta["url"] = linkelem.find('a').get('href')
        meta["text"] = post.find('span', {'class','body'}).get_text().strip()
        qhash = hashlib.sha256(meta["url"].encode())
        hashsum = str(qhash.hexdigest().upper())
        filename = "dl-link_" + hashsum + ".sh"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            self.assertdir(basepath)
            print("\t\t\t-> " + path)
            filecontent="#! /bin/bash\nwget -c " + meta['url'] + "\n"
            with open(path, "w") as df:
                df.write(filecontent)
            st = os.stat(path)
            os.chmod(path, st.st_mode | stat.S_IEXEC)
            self.assertdir(basepath + "meta" + self.sep )
            with open(basepath + "meta" + self.sep + "dl-link_" + hashsum + ".meta", "w") as jf:
                json.dump(meta, jf)

    def process_video(self, post, dlurl):
        print("\t\tVideo:")
        meta = {'soup_page' : dlurl}
        meta['time'] = self.get_timstemp(post)
        meta['embeded'] = post.find("div", {'class':'embed'}).prettify()
        video = post.find("div", {'class':'embed'}).find('video')
        if video:
            meta['soup_url'] = video.get("src")
            if meta['soup_url'] is None and video.find('source'):
                for source in video.find_all('source'):
                    src = source.get("src")
                    # prefer mp4 (as for my example webm returned 404)
                    if meta['soup_url'] is None or (src is not None and src.endswith(".mp4")):
                        meta['soup_url'] = src
        bodyelem = post.find("div", {'class':'body'})
        if bodyelem:
            meta['body'] = bodyelem.get_text().strip()
        else:
            meta['body'] = "";
        if 'soup_url' in meta and meta['soup_url'] is not None:
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_url: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                self.assertdir(basepath + "meta" + self.sep )
                with open(basepath + "meta" + self.sep + filename + ".json", 'w') as outfile:
                    json.dump(meta, outfile)
        else:
            data = meta['embeded'] + meta['body']
            qhash = hashlib.sha256(data.encode())
            hashsum = str(qhash.hexdigest().upper())
            filename = "video_" + hashsum + ".json"
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            path = basepath + filename
            if os.path.isfile(path) == True:
                print("\t\t\tSkip: " + filename + ": File exists")
            else:
                self.assertdir(basepath)
                print("\t\t\t-> " + path)
                with open(path, "w") as vf:
                    json.dump(meta, vf)

    def process_file(self, post, dlurl):
        print("\t\tFile:")
        meta = {'soup_page' : dlurl}
        meta['time'] = self.get_timstemp(post)
        linkelem = post.find("h3")
        if linkelem:
            meta["link_title"] = linkelem.get_text().strip()
            meta["soup_url"] = linkelem.find('a').get('href')
        meta["text"] = post.find('div', {'class','body'}).get_text().strip()
        if 'soup_url' in meta:
            filename = meta["soup_url"].split("/")[-1]
        else:
            filename = "file_unkown"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            if 'soup_url' in meta:
                print("\t\t\tsoup_ulr: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as df:
                    df.write(r.content)
            self.assertdir(basepath + "meta" + self.sep )
            jsonname = filename.split(".")[0]
            with open(basepath + "meta" + self.sep + jsonname + ".json", 'w') as outfile:
                json.dump(meta, outfile)

    def process_review(self, post, dlurl):
        print("\t\tReview:")
        meta = {'soup_page' : dlurl}
        meta['time'] = self.get_timstemp(post)
        for link in post.find_all('div', {"class":"imagecontainer"}):
            lightbox = link.find("a", {"class": "lightbox"})
            if lightbox:
                meta['soup_url'] = lightbox.get('href')
            else:
                meta['soup_url'] = link.find("img").get('src')
        descelem = post.find("div", {'class','description'})
        if descelem:
            meta['description'] = descelem.get_text().strip()
        meta['rating'] = post.find("abbr", {"class", "rating"}).get("title")
        h3elem = post.find("a", {"class":"url"})
        meta['url'] = h3elem.get("href")
        meta['title'] = h3elem.get_text()
        if 'soup_url' in meta:
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = "review_" + self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_ulr: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                self.assertdir(basepath + "meta" + self.sep )
                with open(basepath + "review_" + filename + ".json", 'w') as outfile:
                    json.dump(meta, outfile)

    def process_event(self, post, dlurl):
        print("\t\tEvent:")
        meta = {'soup_page' : dlurl}
        meta['time'] = self.get_timstemp(post)
        for link in post.find_all('div', {"class":"imagecontainer"}):
            lightbox = link.find("a", {"class": "lightbox"})
            if lightbox:
                meta['soup_url'] = lightbox.get('href')
            else:
                meta['soup_url'] = link.find("img").get('src')
        h3elem = post.find("a", {"class":"url"})
        meta['url'] = h3elem.get("href")
        meta['title'] = h3elem.get_text()
        meta['dtstart'] = post.find("abbr", {'class':'dtstart'}).get("title")
        dtelem = post.find("abbr", {'class':'dtend'})
        if dtelem:
            meta['dtend'] = dtelem.get("title")
        meta['location'] = post.find("span", {'class':'location'}).get_text().strip()
        meta['ical_url'] = post.find("div", {'class': 'info'}).find('a').get('href')
        descelem = post.find("div", {'class','description'})
        if descelem:
            meta['description'] = descelem.get_text().strip()
        if 'soup_url' in meta:
            basepath = self.bup_dir + self.sep
            if self.has_valid_timestamp(meta):
                basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
            filename = "event_" + self.get_asset_name(meta['soup_url'])
            path = basepath + filename + "." + meta['soup_url'].split(".")[-1]
            if os.path.isfile(path) == True:
                print("\t\t\tSkip " + meta['soup_url'] + ": File exists")
            else:
                print("\t\t\tsoup_ulr: " + meta['soup_url'] + " -> " + path)
                self.assertdir(basepath)
                r = requests.get(meta['soup_url'], allow_redirects=True)
                with open(path, "wb") as tf:
                    tf.write(r.content)
                i = requests.get(meta['ical_url'], allow_redirects=True)
                with open(basepath + filename + ".ical", "wb") as icf:
                    icf.write(i.content)
                self.assertdir(basepath + "meta" + self.sep )
                with open(basepath + "meta" + self.sep + filename + ".json", 'w') as outfile:
                    json.dump(meta, outfile)

    def process_regular(self, post):
        print("\t\tRegular:")
        meta = {}
        meta['time'] = self.get_timstemp(post)
        h3elem = post.find("h3")
        title = ""
        if h3elem:
            title = h3elem.get_text().strip()
        body = post.find("div", {'class':'body'}).get_text().strip()
        content = title + "\n" + body + "\n"
        qhash = hashlib.sha256(content.encode())
        hashsum = str(qhash.hexdigest().upper())
        filename = "regular_" + hashsum + ".txt"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep

        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            self.assertdir(basepath)
            print("\t\t\t-> " + path)
            with open(path, "w") as rf:
                rf.write(content)

    def process_unkown(self, post, post_type, dlurl):
        print("\t\tUnsuported tpye:")
        print("\t\t\tType: " + post_type)
        meta = {'soup_page' : dlurl}
        meta['type'] = post_type
        meta['time'] = self.get_timstemp(post)
        content = post.prettify()
        qhash = hashlib.sha256(content.encode())
        hashsum = str(qhash.hexdigest().upper())
        meta['content'] = content
        filename = "unknown_" + hashsum + ".txt"
        basepath = self.bup_dir + self.sep
        if self.has_valid_timestamp(meta):
            basepath = basepath + meta['time'][2] + self.sep + meta['time'][0] + self.sep
        path = basepath + filename
        if os.path.isfile(path) == True:
            print("\t\t\tSkip: " + filename + ": File exists")
        else:
            print("\t\t\t-> " + path)
            self.assertdir(basepath)
            with open(path, "w") as uf:
                json.dump(meta, uf)

    def process_posts(self, cur_page, dlurl):
        posts = cur_page.find_all('div', {"class": "post"})
        for post in posts:
            post_type = post.get('class')[1] 
            if post_type == "post_image":
                self.process_image(post, dlurl)
            elif post_type == "post_quote":
                self.process_quote(post)
            elif post_type == "post_video":
                self.process_video(post, dlurl)
            elif post_type == "post_link":
                self.process_link(post, dlurl)
            elif post_type == "post_file":
                self.process_file(post, dlurl)
            elif post_type == "post_review":
                self.process_review(post, dlurl)
            elif post_type == "post_event":
                self.process_event(post, dlurl)
            elif post_type == "post_regular":
                self.process_regular(post)
            else:
                self.process_unkown(post, post_type, dlurl)
        
    def backup(self, cont_url = "", max_retries = "10"):
        maxretrycount = max_retries
        retrycount = 0
        dlurl = self.rooturl + cont_url
        old_url = ""
        while retrycount < maxretrycount:
            print("Get: " + dlurl)
            dl = requests.get(dlurl)
            if dl.status_code == 200:
                page = BeautifulSoup(dl.content, 'html.parser')
                if dlurl != old_url:
                    print("Process Posts")
                    self.process_posts(page, dlurl)
                print("Looking for next Page")
                old_url = dlurl
                dlurl = self.rooturl + self.find_next_page(page, dlurl)
            else:
                self.dlnextfound = False
                print("Failed with Status Code: " + str(dl.status_code))
            if self.dlnextfound == False:
                retrycount=retrycount+1
                print("no next found. retry {} of {}".format(retrycount, maxretrycount))
            else:
                retrycount = 0
            
def main(soups, bup_dir, cont_from, max_retries):
    for site in soups:
        soup = Soup(site, bup_dir)
        soup.backup(cont_from, max_retries)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Soup.io backup')
    parser.add_argument('soups', nargs=1, type=str, default=None, help="Name your soup")
    parser.add_argument('-d','--dir', default=os.getcwd(), help="Directory for Backup (default: Working dir)")
    parser.add_argument('-c', '--continue_from', default="", help='Continue from given suburl (Example: /since/696270106?mode=own)')
    parser.add_argument('-r', '--retries', type=int, default=10, help="Set the maximum number of retries (default: 10)")
    args = parser.parse_args()
    main(args.soups, args.dir, args.continue_from, args.retries)
