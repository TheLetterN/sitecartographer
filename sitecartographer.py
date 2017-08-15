import requests

from collections import OrderedDict

from bs4 import BeautifulSoup
from lxml.etree import ElementTree, Element


def case_ins_match(pattern):
    return lambda x: x and x.lower() == pattern.lower()


class WebPage:
    def __init__(self, html, html_parser='lxml'):
        self.soup = BeautifulSoup(html, html_parser)

    @classmethod
    def from_url(cls, url, html_parser='lxml'):
        r = requests.get(url)
        return cls(html=r.text.encode('utf-8'), html_parser=html_parser)

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
    def __init__(self, url, include_images=False, include_videos=False):
        self.url = url
        nsmap = OrderedDict()
        nsmap[None] = 'http://www.sitemaps.org/schemas/sitemap/0.9'
        if include_images:
            nsmap['image'] = 'http://www.google.com/schemas/sitemap-image/1.1'
        if include_videos:
            nsmap['video'] = 'http://www.google.com/schemas/sitemap-video/1.1'
        root = Element('urlset', nsmap=nsmap)
        self.xmltree = ElementTree(root)
        self.soup = None

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
