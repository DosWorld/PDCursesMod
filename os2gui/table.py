#!/usr/bin/env python

class UnicodeData:
    """Parser for the UnicodeData.txt file"""

    def __init__(self, path):
        self.path = path

    def __iter__(self):
        return UnicodeData.UnicodeDataIterator(self.path)

    class UnicodeDataIterator:
        def __init__(self, path):
            self.file = None
            self.file = open(path, "r")
            self.rec = None
            self.first = None
            self.last = None
            self.current = None

        def __del__(self):
            if self.file is not None:
                self.file.close()

        def __next__(self):
            if self.current is not None:
                # Between a "First>" and a "Last>" line
                tup = (self.current, self.rec)
                if self.current >= self.last:
                    # End of range
                    self.current = None
                else:
                    # Go to next
                    self.current += 1
            else:
                line = self.file.readline()
                if line == '':
                    raise StopIteration()
                if line.endswith("\n"):
                    line = line[:-1]
                rec = line.split(';')
                codepoint = int(rec[0], 16)
                if rec[1].endswith(' First>'):
                    self.rec = rec
                    self.first = codepoint
                elif rec[1].endswith(' Last>'):
                    self.last = codepoint
                    rec = self.rec
                    codepoint = self.first + 1
                    self.current = self.first + 2
                    if self.current > self.last:
                        self.current = None
                tup = (codepoint, rec)
            return tup

combining = {}
decompose = {}
compose = {}
exclude = set()

for cp, rec in UnicodeData("UnicodeData.txt"):
    cclass = int(rec[3])
    if cclass != 0:
        combining[cp] = cclass

    if rec[5] != "" and not rec[5].startswith('<'):
        comp = tuple(map(lambda x: int(x, 16), rec[5].split(' ')))
        decompose[cp] = comp
        if len(comp) == 2:
            compose[comp] = cp

with open('CompositionExclusions.txt', 'r') as file:
    while True:
        line = file.readline()
        if line == '':
            break
        sharp = line.find('#')
        if sharp != -1:
            line = line[:sharp]
        line = line.strip()
        if line != '':
            exclude.add(int(line, 16))

with open("unitable.h", "w") as file:
    file.write("/* Generated by table.py from UnicodeData.txt and CompositionExclusions.txt */\n")
    file.write("static const struct CClassTable cclass_table[] = {\n")
    c = list(combining.keys())
    c.sort()
    for cp in c:
        file.write("    { 0x%04X, %d },\n" % (cp, combining[cp]))
    file.write("};\n")
    file.write("\n")

    file.write("static const struct DecompTable decomp_table[] = {\n")
    d = list(decompose.keys())
    d.sort()
    for cp in d:
        comp = decompose[cp]
        comp0 = comp[0]
        comp1 = comp[1] if len(comp) > 1 else 0
        file.write("    { 0x%04X, 0x%04X, 0x%04X },\n" % ( cp, comp0, comp1 ))
    file.write("};\n")
    file.write("\n")

    file.write("static const struct CompTable comp_table[] = {\n")
    c = list(compose.keys())
    c.sort()
    for comp in c:
        cp = compose[comp]
        if not (cp in exclude or cp in combining or comp[0] in combining):
            file.write("    { 0x%04X, 0x%04X, 0x%04X },\n" % ( comp[0], comp[1], cp ))
    file.write("};\n")
