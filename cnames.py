import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from collections.abc import Generator
print("Hi")


def sort_by_hex(self: list):
    self.sort(key=lambda x: (max(int('0x' + x[0][1:][:2], base=16),
                                 int('0x' + x[0][3:][:2], base=16),
                                 int('0x' + x[0][5:][:2], base=16)) +
                                (int('0x' + x[0][1:], base=16) * 0.0000001)
                             ))


def sort_by_name(self: list):
    self.sort(key=lambda x: x[1])


def rip_table(wiki_subpage:str)->Generator:

    if __debug__:
        print("-->  ripping", wiki_subpage)

    with urllib.request.urlopen('https://en.wikipedia.org/wiki/' +
                                urllib.parse.quote_plus(wiki_subpage.split('/')[-1])) as f:
        webpage_str = f.read().decode('utf-8')

        with open(wiki_subpage.strip('/') + '.html', 'w') as cf:
            cf.write(webpage_str)

        root = ET.fromstring(webpage_str)
        color_table = root.find("./body/div[@id='content']/div[@id='bodyContent']/div[@id='mw-content-text']/table")

        for chex, cname, cname2 in [(row.find("./td[1]"), row.find(".//a"), row.find("./th"))
                                    for row in color_table.findall("./tr")]:
            if cname is None:
                cname = cname2
            if cname is not None and chex is not None:
                yield (chex.text, cname.text)


def do_rip()->None:
    color_list = []

    for trange in ('A-F', 'G-M', 'N-Z'):
        for y, z in rip_table('/List_of_colors:_' + trange):
            color_list.append((y, z))

    sort_by_hex(color_list)

    if len(color_list) < 5:
        raise Warning("may have an incomplete list. Aborting")

    with open("color_names.txt", 'w') as fd:
        for color in color_list:
            fd.write(color[0] + " " + color[1] + "\n")
    return None


def parse_rip()->Generator:
    with open("color_names.txt", 'r') as fd:
        for line in fd:
            if len(line) > 3:
                yield tuple(line.rstrip('\n').split(maxsplit=1))

do_rip()

color_list2 = list(parse_rip())
print(len(color_list2))
sort_by_name(color_list2)
print(len(color_list2))
# color_list2.sort(key=lambda x: x[1])
for c in color_list2:
    print(c[0], c[1])

with open('color_names2.txt', 'w') as cn2:
    for c in color_list2:
        cn2.write(c[0] + " " + c[1] + "\n")

