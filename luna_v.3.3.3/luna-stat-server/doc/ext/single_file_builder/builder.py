from itertools import count
from os import path

from docutils.io import StringOutput
from docutils.nodes import TextElement, reference
from sphinx.builders import Builder
from sphinx.util import ensuredir


class SFBuilder(Builder):
    name = 'sf'
    format = 'rst'
    file_suffix = '.rst'
    link_suffix = None  # defaults to file_suffix

    def __init__(self, app):
        self.conf = None
        self.docks = None
        super().__init__(app)

    def init(self):
        self.docks = []

        """Load necessary templates and perform initialization."""
        try:
            self.conf = self.config.single_file_builder
        except Exception:
            self.conf = {}

        if 'output' not in self.conf:
            self.conf['output'] = 'single_file_output.{}'.format(self.file_suffix)

        if 'order' not in self.conf:
            self.conf['order'] = ['index']

        if 'writer' not in self.conf:
            raise ValueError(
                'You must specify writer class in config'
            )

    def get_outdated_docs(self):
        """
        Return an iterable of input files that are outdated.
        """
        # This method is taken from TextBuilder.get_outdated_docs()
        # with minor changes to support :confval:`rst_file_transform`.
        for docname in self.env.found_docs:
            yield docname

    def get_target_uri(self, docname, typ=None):
        return docname

    def get_relative_uri(self, from_, to, typ=None):
        """
        Return a relative URI between two source filenames.
        """
        # This is slightly different from Builder.get_relative_uri,
        # as it contains a small bug (which was fixed in Sphinx 1.2).
        return to

    def prepare_writing(self, docnames):
        self.writer = self.conf['writer'](self)

    def write_doc(self, docname, doctree):
        self.docks += [(docname, doctree)]

    def finish(self):
        # This method is taken from TextBuilder.write_doc()
        # with minor changes to support :confval:`rst_file_transform`.
        destination = StringOutput(encoding='utf-8')
        # print "write(%s,%s)" % (type(doctree), type(destination))

        doc_names = [i[0] for i in self.docks]
        for order, order_item in zip(count(), self.conf['order']):
            try:
                index_position = doc_names.index(order_item)
            except Exception:
                continue

            if index_position != order:
                self.docks[index_position], self.docks[order] = self.docks[order], self.docks[index_position]

        out = ''
        for docname, doctree in self.docks:
            out += self.writer.write(doctree, destination).decode()

        outfilename = path.join(self.outdir, self.conf['output'])
        ensuredir(path.dirname(outfilename))
        try:
            f = open(outfilename, 'w')
            try:
                f.write(out)
            finally:
                f.close()
        except (IOError, OSError) as err:
            self.warn("error writing file %s: %s" % (outfilename, err))
