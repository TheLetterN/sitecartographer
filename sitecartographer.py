import requests

from collections import OrderedDict

from bs4 import BeautifulSoup
from lxml.etree import ElementTree, Element, SubElement, tostring

BASE_NAMESPACE = 'http://www.sitemaps.org/schemas/sitemap/0.9'
IMAGE_NAMESPACE = 'http://www.google.com/schemas/sitemap-image/1.1'

def case_ins_match(pattern):
    return lambda x: x and x.lower() == pattern.lower()


class WebPage:
    def __init__(self, url):
        self.url = url
        r = requests.get(url)
        html = r.text.encode('utf-8')
        self.soup = BeautifulSoup(html, 'lxml')

    @property
    def images(self):
        return self.soup.find_all('img')

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
                 ignore_noindex=False):
        self.url = url
        self.exclude = []
        self.include_images = include_images
        self.ignore_noindex = ignore_noindex
        nsmap = OrderedDict()
        nsmap[None] = BASE_NAMESPACE
        if include_images:
            nsmap['image'] = IMAGE_NAMESPACE 
        self.root = Element('urlset', nsmap=nsmap)
        self.xmltree = ElementTree(self.root)

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

    def excluded(self, url):
        for pattern in self.exclude:
            if pattern in url:
                return True
        return False

    def build_xmltree(self):
        def add_page(page):
            if not self.ignore_noindex and page.noindex:
                return
            url_elem = SubElement(self.root, 'url')
            loc = SubElement(url_elem, 'loc')
            loc.text = page.url
            if self.include_images:
                for image in page.images:
                    src = image.get('src')
                    if src and not self.excluded(src):
                        img_elem = SubElement(
                            url_elem,
                            '{{{}}}image'.format(IMAGE_NAMESPACE)
                        )
                        img_loc = SubElement(
                            img_elem,
                            '{{{}}}loc'.format(IMAGE_NAMESPACE)
                        )
                        img_loc.text = src
                        # TODO: image caption

        top = WebPage(self.url)
        add_page(top)

    def tostring(self, *args, **kwargs):
        return tostring(self.xmltree, *args, **kwargs)
