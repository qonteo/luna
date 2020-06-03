# -*- coding: utf-8 -*-
from lxml import objectify
from docutils import nodes


class TestRst:
    def __init__(self):
        self.resources = []
        self.description = ""
        self.tag = ""
        self.titel = ""

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return ""

    def __setitem__(self, key, value):
        return setattr(self, key, value)


def parse(testHtml):
    rootHTMLTest = objectify.fromstring(testHtml)

    test = TestRst()
    if hasattr(rootHTMLTest, "field_list"):
        for field_ in rootHTMLTest.field_list:
            for field in field_.field:
                test[field.field_name.text] = field.field_body.paragraph.text
    if hasattr(rootHTMLTest, "paragraph"):
        for testTitel in rootHTMLTest.paragraph:
            test["titel"] = testTitel.text
    return test


def generateRowSetTestsMD(tests, tag):
    lengthTest = 0
    lengthResource = 0
    lengthDescription = len("Description")
    for test in tests:

        if len(test.titel) > lengthTest:
            lengthTest = len(test.titel)
        test.resources = test.resources.split(',')
        for resourse in test.resources:
            if len(resourse) > lengthResource:
                lengthResource = len(resourse)
        if len(test.description) > lengthDescription:
            lengthDescription = len(test.description)

    rows = [tag, ('{:-^' + '{}'.format(len(tag)) + '}').format("")]

    formatRow = '|{:<' + '{}'.format(lengthTest) + \
                '}|{:<' + '{}'.format(lengthResource) + \
                '}|{:<' + '{}'.format(lengthDescription) +'}|'
    formatSeparatorHeaders = '|{:-^' + '{}'.format(lengthTest) + \
                             '}|{:-^' + '{}'.format(lengthResource) + \
                             '}|{:-^' + '{}'.format(lengthDescription) + '}|'
    rows.append(formatRow.format("Test", "Resources", "Test description"))
    rows.append(formatSeparatorHeaders.format("", "", ""))
    for test in tests:
        countResource = len(test.resources)
        if countResource > 0:
            r = formatRow.format(test.titel, test.resources[0], test.description)
        else:
            r = formatRow.format(test.titel, "", test.description)
        rows.append(r)
        for resource in test.resources[1:]:
            r = formatRow.format("", resource, "")
            rows.append(r)
    return rows


def generateRowSetTestsReStr(tests, tag):
    lengthTest = 0
    lengthResource = 0
    lengthDescription = len("Description")
    for test in tests:

        if len(test.titel) > lengthTest:
            lengthTest = len(test.titel)
        test.resources = test.resources.split(',')
        for resourse in test.resources:
            if len(resourse) > lengthResource:
                lengthResource = len(resourse)
        if len(test.description) > lengthDescription:
            lengthDescription = len(test.description)

    rows = [tag, ('{:-^' + '{}'.format(len(tag)) + '}').format("")]

    formatSeparator = '+{:-^' + '{}'.format(lengthTest) + \
                      '}+{:-^' + '{}'.format(lengthResource) + \
                      '}+{:-^' + '{}'.format(lengthDescription) + '}+'
    formatSeparatorHeaders = '+{:=^' + '{}'.format(lengthTest) + \
                             '}+{:=^' + '{}'.format(lengthResource) + \
                             '}+{:=^' + '{}'.format(lengthDescription) + '}+'
    formatSeparatorResources = '|{:^' + '{}'.format(lengthTest) + \
                               '}+{:-^' + '{}'.format(lengthResource) + \
                               '}+{:^' + '{}'.format(lengthDescription) + '}|'
    rows.append(formatSeparator.format("", "", "", ""))

    formatRow = '|{:<' + '{}'.format(lengthTest) + \
                '}|{:<' + '{}'.format(lengthResource) + \
                '}|{:<' + '{}'.format(lengthDescription) + '}|'

    rows.append(formatRow.format("Test", "Resourses", "Test description"))
    rows.append(formatSeparatorHeaders.format("", "", ""))

    for test in tests:
        countResource = len(test.resources)
        if countResource > 0:
            r = formatRow.format(test.titel, test.resources[0], test.description)
        else:
            r = formatRow.format(test.titel, "", test.description)
        rows.append(r)
        for resource in test.resources[1:]:
            rows.append(formatSeparatorResources.format("", "", ""))
            r = formatRow.format("", resource, "")
            rows.append(r)
        rows.append(formatSeparator.format("", "", ""))
    return rows


def generateTestsNode(tests):
    def addTestRow(test, tbody):

        row = nodes.row()
        rowSpawn = max(len(test.resources) - 1, 0)
        entry = nodes.entry(morerows=rowSpawn)
        row += entry
        entry += nodes.paragraph(text=test.titel)
        entry = nodes.entry()
        row += entry
        if len(test.resources) > 0:
            entry += nodes.paragraph(text=test.resources[0])
        else:
            entry += nodes.paragraph(text="")
        entry = nodes.entry(morerows=rowSpawn)
        row += entry
        entry += nodes.paragraph(text=test.description)

        tbody += row
        for resource in test.resources[1:]:
            row = nodes.row()

            entry = nodes.entry()
            row += entry
            entry += nodes.paragraph(text=resource)
            tbody += row

    def create_table_row(row_cells):
        row = nodes.row()

        for cell in row_cells:
            entry = nodes.entry()
            row += entry
            entry += nodes.paragraph(text=cell)

        return row

    headers = ('Test', 'Resourses', 'Description')
    table = nodes.table()

    tgroup = nodes.tgroup(cols=len(headers))
    colwidths = (2, 1.75, 4)
    table += tgroup

    for colwidth in colwidths:
        tgroup += nodes.colspec(colwidth=colwidth)

    thead = nodes.thead()
    tgroup += thead
    thead += create_table_row(headers)

    tbody = nodes.tbody()
    tgroup += tbody
    for test in tests:
        addTestRow(test, tbody)
    print(182,table)
    return table
