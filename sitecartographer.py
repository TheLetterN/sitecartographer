import logging, requests, time

from collections import OrderedDict
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


def case_ins_match(pattern):
    return lambda x: x and x.lower() == pattern.lower()


class WebPage:
    def __init__(self, url):
        self._url = url
        r = requests.get(url)
        html = r.text.encode('utf-8')
        self.soup = BeautifulSoup(html, 'lxml')

    @property
    def images(self):
        return self.soup.find_all('img')

    @property
    def links(self):
        return self.soup.find_all('a')

    @property
    def canonical(self):
        can = self.soup.find('link', rel=case_ins_match('canonical'))
        try:
            return can['href']
        except KeyError:
            return None

    @property
    def url(self):
        return self.canonical or self._url

    @property
    def robots(self):
        return self.soup.find('meta', {'name': case_ins_match('robots')}) 

    @property
    def noindex(self):
        return self.in_robots('noindex')

    @property
    def nofollow(self):
        return self.in_robots('nofollow')

    def in_robots(self, pattern):
        try:
            content = self.robots.attrs['content']
        except AttributeError:
            return False
        contents = (word.lower().strip() for word in content.split(','))
        return pattern.lower() in contents


class SiteMap:
    def __init__(self,
                 url,
                 exclude=[],
                 include_images=True,
                 ignore_noindex=False,
                 ignore_nofollow=False,
                 verbose=False):
        self.url = url
        parsed_url = urlparse(url)
        if not 'http' in parsed_url.scheme:
            raise ValueError('Please use a url with the http or https scheme.')
        self.domain='{}://{}'.format(parsed_url.scheme, parsed_url.netloc)
        self.exclude = []
        self.include_images = include_images
        self.ignore_noindex = ignore_noindex
        self.ignore_nofollow = ignore_nofollow
        self.verbose = verbose
        nsmap = OrderedDict()
        nsmap[None] = BASE_NAMESPACE
        if include_images:
            nsmap['image'] = IMAGE_NAMESPACE 
        self.root = Element('urlset', nsmap=nsmap)
        self.xmltree = ElementTree(self.root)
        self.used_urls = []

    def fix_url(self, url):
        if url and url[0] != '#':
            url = url.split('#')[0]  # We don't want fragments!
        if self.domain in url:
            return url
        elif url and url[0]  == '/':
            return urljoin(self.domain, url)
        else:
            raise ValueError(
                '"{}" does not appear to be a crawlable url!'.format(url)
            )

    def print(self, text):
        if self.verbose:
            print(text)

    def write_xml(
            self,
            filename,
            encoding='utf-8',
            pretty_print=True,
            xml_declaration=True,
            **kwargs):
        self.xmltree.write(
            filename,
            encoding=encoding,
            pretty_print=pretty_print,
            xml_declaration=True,
            **kwargs
        )

    def is_excluded(self, url):
        if url:
            return any(pattern for pattern in self.exclude if pattern in url)
        return True  # There's no sense in including blank URLs.

    def validate_url(self, url):
        return not self.is_excluded(url) and url not in self.used_urls

    def build_xmltree(self):
        def add_page(page):
            if not self.ignore_noindex and page.noindex:
                return
            url_elem = SubElement(self.root, 'url')
            loc = SubElement(url_elem, 'loc')
            loc.text = page.url
            self.used_urls.append(page.url)
            self.print('Page "{}" added to sitemap.'.format(page.url))
            if self.include_images:
                for image in page.images:
                    src = image.get('src')
                    # Do not use validate_url here because images on multiple
                    # pages should be allowed.
                    if not self.is_excluded(src):
                        self.print(
                            '- Added image "{}" to page "{}".'
                            .format(src, page.url)
                        )
                        img_elem = SubElement(
                            url_elem,
                            '{{{}}}image'.format(IMAGE_NAMESPACE)
                        )
                        img_loc = SubElement(
                            img_elem,
                            '{{{}}}loc'.format(IMAGE_NAMESPACE)
                        )
                        img_loc.text = src
                        caption = image.get('title')
                        if not caption:
                            caption = image.get('alt')
                        if caption:
                            img_cap = SubElement(
                                img_elem,
                                '{{{}}}caption'.format(IMAGE_NAMESPACE)
                            )
                            self.print(
                                '-- Caption for image "{}" set to "{}".'
                                .format(src, caption)
                            )
                            img_cap.text = caption
#            start = time.time()
            for link in page.links:
                try:
                    href = link['href']
                except KeyError:
                    continue
                try:
                    url = self.fix_url(href)
                except ValueError as e:
                    logger.log(logging.WARNING, e)
                    continue
                if self.validate_url(url):
                    add_page(WebPage(url))
#            delta = time.time() - start
#            logger.log(
#                logging.DEBUG,
#                'Links on page "{}" checked in {} seconds.'.format(url, delta)
#            )

        add_page(WebPage(self.url))

    def tostring(self, *args, **kwargs):
        return tostring(self.xmltree, *args, **kwargs)
