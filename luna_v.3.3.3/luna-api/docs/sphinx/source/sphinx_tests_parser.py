# -*- coding: utf-8 -*-
from docutils import nodes
import docutils
from docs.sphinx.source import tests_html_parser

class test(nodes.Admonition, nodes.Element):
    pass

class testlist(nodes.General, nodes.Element):
    pass

def visit_test_node(self, node):
    self.visit_admonition(node)

def depart_test_node(self, node):
    self.depart_admonition(node)

from docutils.parsers.rst import Directive

class TestlistDirective(Directive):

    def run(self):
        return [testlist('')]

from sphinx.locale import _

class testDirective(Directive):

    # this enables content in the directive
    has_content = True
    add_index = True

    option_spec = {'resources': docutils.parsers.rst.directives.unchanged,
                   'description': docutils.parsers.rst.directives.unchanged,
                   'tag': docutils.parsers.rst.directives.unchanged,
                   'LIS': docutils.parsers.rst.directives.unchanged, }

    def run(self):
        env = self.state.document.settings.env

        targetid = "test-%d" % env.new_serialno('test')
        targetnode = nodes.target('', '', ids=[targetid])

        test_node = test('\n'.join(self.content))
        test_node += nodes.title(_('Test'), _('Test'))

        self.state.nested_parse(self.content, self.content_offset, test_node)

        if not hasattr(env, 'test_all_tests'):
            env.test_all_tests = []
        env.test_all_tests.append({
            'docname': env.docname,
            'lineno': self.lineno,
            'test': test_node.deepcopy(),
            'target': targetnode,
        })
        #print(23232, test_node.__dict__, env.test_all_tests,"\n", targetnode, "\n", test_node)

        return [targetnode, test_node]


def process_test_nodes(app, doctree, fromdocname):

    if not app.config.test_include_tests:
        for node in doctree.traverse(test):
            node.parent.remove(node)


    # Replace all testlist nodes with a list of the collected tests.
    # Augment each test with a backlink to the original location.
    env = app.builder.env

    for node in doctree.traverse(testlist):

        if not app.config.test_include_tests:
            node.replace_self([])
            continue

        content = []

        tests = [tests_html_parser.parse(str(test_["test"]).replace('\n',"")) for test_ in env.test_all_tests]
        for test_ in tests:
            test_.resources = test_.resources.split(',')

        setTests = []
        tags = []
        for test_ in tests:
            if test_.tag == "":
                test_.tag = "Without tag"
            tags.append(test_.tag)

        tags = list(set(tags))

        for tag in tags:
            setT ={"tag": tag, "tests": []}
            t = setT.copy()
            for test_ in tests:
                if tag == test_.tag:
                    t["tests"].append(test_)

            def sortByResources(el):
                return el.resources[0]


            t["tests"] = sorted(t["tests"], key = sortByResources)
            setTests.append(t)

        def sortByTag(el):
            return el["tag"]

        setTests = sorted(setTests, key = sortByTag)
        for tests in setTests:
            content.append(nodes.title(text = tests["tag"]))

            table = tests_html_parser.generateTestsNode(tests["tests"])
            content.append(table)

        for test_info in env.test_all_tests:
            para = nodes.paragraph()
            filename = env.doc2path(test_info['docname'], base=None)
            description = (
                _('(The original entry is located in %s, line %d and can be found ') %
                (filename, test_info['lineno']))
            para += nodes.Text(description, description)

            # Create a reference
            newnode = nodes.reference('', '')
            innernode = nodes.emphasis(_('here'), _('here'))
            newnode['refdocname'] = test_info['docname']
            newnode['refuri'] = app.builder.get_relative_uri(
                fromdocname, test_info['docname'])
            newnode['refuri'] += '#' + test_info['target']['refid']
            newnode.append(innernode)
            para += newnode
            para += nodes.Text('.)', '.)')
            # Insert into the testlist
            content.append(test_info['test'])
            content.append(para)

        node.replace_self(content)


def purge_tests(app, env, docname):
    global flag
    if not hasattr(env, 'test_all_tests'):
        return

    env.test_all_tests = [test for test in env.test_all_tests
                          if test['docname'] != docname]


def setup(app):
    app.add_config_value('test_include_tests', True, 'html')

    app.add_node(testlist)
    app.add_node(test,
                 html=(visit_test_node, depart_test_node),
                 latex=(visit_test_node, depart_test_node),
                 text=(visit_test_node, depart_test_node))

    app.add_directive('test', testDirective)
    app.add_directive('testlist', TestlistDirective)
    app.connect('doctree-resolved', process_test_nodes)
    app.connect('env-purge-doc', purge_tests)

    return {'version': '0.1'}