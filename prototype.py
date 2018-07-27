# rabbit
# a modern, high performance file and data carving framework
# Copyright (C) 2018 Bruno Constanzo
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
# USA

import os


from pprint import pprint


class FileFormat:
    def __init__(self, extension=None, header=None, footer=None, comment=None,
                 maxlen=None, minlen=None,
                 ):
        self.extension   = extension
        self.header      = header
        self.footer      = footer
        self.comment     = comment
        self.maxlen      = maxlen
        self.minlen      = minlen
    
    def __repr__(self):
        return (
            f"FileFormat(ext='{self.extension}', header={self.header}, footer='{self.footer}, "
            f"maxlen={self.maxlen}, minlen={self.minlen})"
            #f"\nComment: {self.comment}" * bool(self.comment)
        )


class Provider:
    def __init__(self, path, bsize=512):
        self.fd = open(path, "rb")
        self.bsize = bsize

    def find(self, needles, start=0):
        fd, bsize = self.fd, self.bsize
        fd.seek(start)
        data = fd.read(bsize)
        while data:
            if any(n for n in needles if n in data):
                for n in needles:
                    pos = data.find(n)
                    if pos > -1:
                        yield ((fd.tell() - bsize) // bsize, pos, n)
            data = fd.read(bsize)


class Extractor:
    def __init__(self, path, src_path):
        self.path = path
        if not(os.path.exists(path)):
            os.makedirs(path)
        self.basename = "{count:08d}.{ext}"
        self.count = 0
        self.src_path = src_path
        self.src_img = open(src_path, "rb")
        self.extracted = []

    def extract(self, start, end, ext):
        self.count += 1
        fname = self.basename.format(count=self.count, ext=ext)
        with open(f"{self.path}/{fname}", "wb") as fd:
            self.src_img.seek(start)
            data = self.src_img.read(end - start)
            fd.write(data)
            self.extracted.append(f"{self.path}/{fname}")


class Carver:
    def __init__(self, provider, extractor, formats):
        self.provider = provider
        self.extractor = extractor
        self.formats = formats

    def carve(self):
        needles = {}
        stack = {}
        for f in self.formats:
            needles.update({f.header: ("header", f), f.footer: ("footer", f)})
            stack[f] = {"header":[], "footer":[]}
        provider = self.provider
        extractor = self.extractor
        for block, offset, n in provider.find(needles):
            match_type, fmt = needles[n]
            stack[fmt][match_type].append((block, offset, n))
            if match_type == "footer":
                if stack[fmt]["footer"] and stack[fmt]["header"]:
                    end = stack[fmt]["footer"].pop()
                    start = stack[fmt]["header"].pop()
                else:
                    continue
                bsize = provider.bsize
                start = (start[0] * bsize) + start[1]
                end = (end[0] * bsize) + end[1] + len(n)
                extractor.extract(start, end, fmt.extension)



