import logging, requests, time

from collections import OrderedDict
from queue import Empty, Queue
from threading import Thread
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from lxml.etree import ElementTree, Element, SubElement, tostring

BASE_NAMESPACE = 'http://www.sitemaps.org/schemas/sitemap/0.9'
IMAGE_NAMESPACE = 'http://www.google.com/schemas/sitemap-image/1.1'

logger = logging.getLogger('sitecartographer')
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler('sitecartographer.log')
ch = logging.StreamHandler()
fh.setLevel(logging.DEBUG)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('{asctime}: {levelname} - {message}', style='{')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


to_crawl = Queue()
crawled = Queue()
scraped = Queue()


def remove_fragment(url):
    """Remove fragment from the end of a url if present."""
    return url.split('#')[0]


def normalize_protocol(url, protocol):
    """Convert http/https URLs to desired protocol if present."""
    if '//' not in url:
        raise ValueError('No protocol specified in url: {}'.format(url))
    protocol = protocol.replace('://', '').lower()
    if protocol != 'http' and protocol != 'https':
        raise ValueError('Protocol must be "http" or "https".')
    if url.startswith('//'):
        url = '{}:{}'.format(protocol, url)
    if url.startswith('https:'):
        if protocol == 'http':
            url = url.replace('https', 'http', 1)
    elif url.startswith('http:'):
        if protocol == 'https':
            url = url.replace('http', 'https', 1)
    else:
        raise ValueError('No http/https protocol in url: {}'.format(url))
    return url


def normalize_url(url, base_url):
    """Attach base_url to url if not already present."""
    url = remove_url_fragment(url)
    if url[:len(base_url)] == base_url:
        return url
    else:
        return urljoin(base_url, url)


def clean_url(url):
    pass


# Begin move to main
START_URL = 'https://www.swallowtailgardenseeds.com'

BASE_URL = START_URL

to_crawl.put(clean_url(START_URL))

# end move to main


def case_ins_match(pattern):
    return lambda x: x and x.lower() == pattern.lower()


def scrape_page(url):
    page = WebPage(url)


def crawl():
    """Crawl through the site structure and scrape pages."""
    while not to_crawl.empty():
        pages = []
        while not to_crawl.empty():
            pages.append(to_crawl.get_nowait())
        threads = [Thread(target=scrape_page, args=(url,)) for url in pages]
        for t in threads:
            t.start()
        for t in threads:
            t.join()


class WebPage:
    def __init__(self, url):
        self.url = url
        r = requests.get(url)
        html = r.text.encode('utf-8')
        self.soup = BeautifulSoup(html, 'lxml')

    @property
    def a_tags(self):
        return self.soup.find_all('a')

    @property
    def img_tags(self):
        return self.soup.find_all('img')

    @property
    def canonical(self):
        can = self.soup.find('link', rel=case_ins_match('canonical'))
        try:
            return can['href']
        except KeyError:
            return None

    @property
    def robots(self):
        return self.soup.find('meta', {'name': case_ins_match('robots')}) 

    @property
    def noindex(self):
        return self.in_robots('noindex')

    @property
    def nofollow(self):
        return self.in_robots('nofollow')

    def get_links(self):
        for a in self.a_tags:
            href = a.get('href')
            if href:
                yield href

    def get_images(self):
        for img in self.img_tags:
            url = img.get('src')
            caption = img.get('title')
            if not caption:
                caption = img.get('alt')
            yield (url, caption)


    def in_robots(self, pattern):
        try:
            content = self.robots.attrs['content']
        except AttributeError:
            return False
        contents = (word.lower().strip() for word in content.split(','))
        return pattern.lower() in contents


#class SiteMap:
#    def __init__(self,
#                 url,
#                 exclude=[],
#                 include_images=True,
#                 ignore_noindex=False,
#                 ignore_nofollow=False,
#                 verbose=False):
#        self.url = url
#        parsed_url = urlparse(url)
#        if not 'http' in parsed_url.scheme:
#            raise ValueError('Please use a url with the http or https scheme.')
#        self.domain='{}://{}'.format(parsed_url.scheme, parsed_url.netloc)
#        self.exclude = []
#        self.include_images = include_images
#        self.ignore_noindex = ignore_noindex
#        self.ignore_nofollow = ignore_nofollow
#        self.verbose = verbose
#        nsmap = OrderedDict()
#        nsmap[None] = BASE_NAMESPACE
#        if include_images:
#            nsmap['image'] = IMAGE_NAMESPACE 
#        self.root = Element('urlset', nsmap=nsmap)
#        self.xmltree = ElementTree(self.root)
#        self.crawled = []
#
#    def crawl(self):
#        while True:
#            try:
#                url = to_crawl.get_nowait()
#            except Empty:
#                # Stop crawling once there are no more URLs to crawl.
#                break
#
#
#    def print(self, text):
#        if self.verbose:
#            print(text)
#
#    def write_xml(
#            self,
#            filename,
#            encoding='utf-8',
#            pretty_print=True,
#            xml_declaration=True,
#            **kwargs):
#        self.xmltree.write(
#            filename,
#            encoding=encoding,
#            pretty_print=pretty_print,
#            xml_declaration=True,
#            **kwargs
#        )
#
#    def is_excluded(self, url):
#        if url:
#            return any(pattern for pattern in self.exclude if pattern in url)
#        return True  # There's no sense in including blank URLs.
#
#    def validate_url(self, url):
#        return not self.is_excluded(url) and url not in self.used_urls
#
#    def build_xmltree(self):
#        def add_page(page):
#            if not self.ignore_noindex and page.noindex:
#                return
#            url_elem = SubElement(self.root, 'url')
#            loc = SubElement(url_elem, 'loc')
#            loc.text = page.url
#            self.used_urls.append(page.url)
#            self.print('Page "{}" added to sitemap.'.format(page.url))
#            if self.include_images:
#                for image in page.images:
#                    src = image.get('src')
#                    # Do not use validate_url here because images on multiple
#                    # pages should be allowed.
#                    if not self.is_excluded(src):
#                        self.print(
#                            '- Added image "{}" to page "{}".'
#                            .format(src, page.url)
#                        )
#                        img_elem = SubElement(
#                            url_elem,
#                            '{{{}}}image'.format(IMAGE_NAMESPACE)
#                        )
#                        img_loc = SubElement(
#                            img_elem,
#                            '{{{}}}loc'.format(IMAGE_NAMESPACE)
#                        )
#                        img_loc.text = src
#                        caption = image.get('title')
#                        if not caption:
#                            caption = image.get('alt')
#                        if caption:
#                            img_cap = SubElement(
#                                img_elem,
#                                '{{{}}}caption'.format(IMAGE_NAMESPACE)
#                            )
#                            self.print(
#                                '-- Caption for image "{}" set to "{}".'
#                                .format(src, caption)
#                            )
#                            img_cap.text = caption
##            start = time.time()
#            for link in page.links:
#                try:
#                    href = link['href']
#                except KeyError:
#                    continue
#                try:
#                    url = self.fix_url(href)
#                except ValueError as e:
#                    logger.log(logging.WARNING, e)
#                    continue
#                if self.validate_url(url):
#                    add_page(WebPage(url))
##            delta = time.time() - start
##            logger.log(
##                logging.DEBUG,
##                'Links on page "{}" checked in {} seconds.'.format(url, delta)
##            )
#
#        add_page(WebPage(self.url))
#
#    def tostring(self, *args, **kwargs):
#        return tostring(self.xmltree, *args, **kwargs)
