import webbrowser
import urllib.parse
import io
import typing
import xml.etree.ElementTree as ET
import struct
import glob
import os.path
import csformat


class RawPage(object):
    def __init__(self):
        self.html_page = io.StringIO()

    def read_page(self)->typing.Union[str, bytes]:
        return self.html_page.getvalue()

    def get_dump_url(self):
        cat_page = ''.join(self.read_page().splitlines())
        return 'data:text/html;charset=UTF-8,{}'.format(urllib.parse.quote(cat_page))

    def close(self):
        self.html_page.close()

    def __del__(self):
        self.close()

    def write(self, s1: typing.Union[str, bytes]):
        self.html_page.write(s1)


class HtmlTree(object):
    def __init__(self):
        self.html_page = io.StringIO()
        self.html_tree = ET.ElementTree(element=ET.Element('html'))
        self.root.append(ET.Element('head'))
        self.root.append(ET.Element('body'))

    @property
    def root(self)->ET.Element:
        return self.html_tree.getroot()

    @property
    def head(self)->ET.Element:
        return self.root.find('head')

    @property
    def body(self)->ET.Element:
        return self.root.find('body')

    def _clear_html_file(self):
        self.html_page.seek(0)
        self.html_page.truncate()

    def _write_tree(self, pretty=True):
        self.root.tail = self.root.text = self.head.tail = self.head.text = self.body.tail = '\n' if pretty else ''
        self.html_tree.write(self.html_page, encoding='unicode', xml_declaration=False, method='html')

    def _write_doctype(self, pretty=True):
        self.html_page.write('<!DOCTYPE html>')
        if pretty:
            self.html_page.write('\n')

    def dump(self, pretty=True):
        self._clear_html_file()
        self._write_doctype(pretty)
        self._write_tree(pretty)
        return self.html_page.getvalue()

    def flat_dump(self):
        self._clear_html_file()
        self._write_tree(pretty=False)
        return ''.join(self.html_page.getvalue().splitlines())

    def flat_url_dump(self):
        s1 = self.flat_dump()
        return 'data:text/html;charset=UTF-8,{}'.format(urllib.parse.quote(s1))

    def add_style(self, stylesheet_text, pretty=True):
        style_el = ET.Element('style', {'type': 'text/css'})
        style_el.text = stylesheet_text
        style_el.tail = '\n' if pretty else ''
        self.head.append(style_el)

    def __del__(self):
        self.html_page.close()


class PaletteShowcase(object):
    def __init__(self):
        self.cb_count = 0
        self.ht = HtmlTree()
        self.ht.add_style('html,body{background-color:#222;color:#EEE;font-family:sans-serif;}')
        self.ht.add_style('.shelf, .shelf2{margin:10px;display:inline-block;min-width:300px;min-height:100px;}')
        self.ht.add_style('.shelf{background-color:#333;}')
        self.ht.add_style('.shelf2{background-color:#BBB;color:#222}')
        self.ht.add_style('.dimension{color:#555;}')
        self.ht.add_style('.shelf>*,.shelf2>*{display:block;margin:0 auto;text-align:center;}')

    def write_to_file(self, fname):
        with open(fname, 'w') as fd1:
            fd1.write(self.ht.dump())
        return fname

    def add_color_block(self, cb:csformat.ColorBlock):
        r1, g1, b1 = float(cb.colors_od['r']), float(cb.colors_od['g']), float(cb.colors_od['b'])
        id_str = "cb" + str(self.cb_count)
        r2, g2, b2 = [str(int(x * 255)) for x in (r1, g1, b1)]
        style_str = "#" + id_str + "{background-color: rgb(" + ",".join([r2, g2, b2]) + ");}"
        self.ht.add_style(style_str)
        span_el = ET.Element('span', {'id': id_str})
        span_el.text = str(cb.name_field, encoding='ascii') if cb.name_field else "rgb(" + ", ".join((r2, g2, b2)) + ")"
        self.cb_count += 1
        self.ht.body.append(span_el)

    def add_group_block(self, gb:csformat.GroupBlockStart):
        h2_el = ET.Element('h2', {'class': 'moo'})
        h2_el.text = str(gb.name_field, encoding='ascii') if gb.name_field else "Untitled Group"
        self.ht.body.append(h2_el)

    @classmethod
    def from_csfile(cls, csf:csformat.CSFileReader):
        new_ps = cls()
        for anyb in csf.blocks:
            if anyb.__class__.__name__ == 'ColorBlock':
                new_ps.add_color_block(anyb)
            elif anyb.__class__.__name__ == 'GroupBlockStart':
                new_ps.add_group_block(anyb)
            else:
                print("skipping", anyb, anyb.__class__.__name__)

        return new_ps


def bfloat_to_sint(bf):
    # s1 = str(bf, encoding='ascii')
    f1 = float(bf)
    return int(f1 * 255)


class GimpPalette(object):
    def __init__(self):
        self.color_lines = []
        self.palette_name = ""

    @staticmethod
    def color_line(r, g, b, name=None):
        cname = str(name, encoding='ascii') if name else "Untitled"
        r2, g2, b2 = [bfloat_to_sint(x) for x in (r, g, b)]
        return "{} {} {}\t{}".format(r2, g2, b2, cname)

    def write_color_line(self, cb:csformat.ColorBlock):
        self.color_lines.append(self.color_line(name=cb.name_field, **cb.colors_od))

    def write_to_file(self, fname):
        with open(fname, 'w') as fd1:
            fd1.write("GIMP Palette\nName: ")
            fd1.write(str(fname).rpartition('.')[0])
            fd1.write("\nColumns: 10\n#\n")
            for cl in self.color_lines:
                fd1.write(cl)
                fd1.write("\n")
            fd1.write("\n")
        return fname

    @classmethod
    def from_csfile(cls, csf:csformat.CSFileReader):
        new_gp = cls()
        for anyb in csf.blocks:
            if anyb.__class__.__name__ == 'ColorBlock':
                new_gp.write_color_line(anyb)
            else:
                print("skipping", anyb, anyb.__class__.__name__)
        return new_gp




