# -*- coding: utf-8 -*-
"""
    sphinx.builders.text
    ~~~~~~~~~~~~~~~~~~~~

    Plain-text Sphinx builder.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import codecs

from docutils.io import StringOutput
from os import path

from sphinx.util import ensuredir

from ext.sphinxcontrib.restbuilder import RstBuilder

from .writer import MdWriter


class MdBuilder(RstBuilder):
    name = 'md'
    format = 'md'
    md_file_suffix = '.md'

    def __init__(self, app):
        super().__init__(app)
        self.file_suffix = self.md_file_suffix
        self.link_suffix = ''

    def prepare_writing(self, docnames):
        self.writer = MdWriter(self)

    def _get_filename(self, docname):
        return f'{docname}{self.md_file_suffix}'

    def get_outdated_docs(self):
        """
        Return an iterable of input files that are outdated.
        """
        # This method is taken from TextBuilder.get_outdated_docs()
        # with minor changes to support :confval:`rst_file_transform`.
        for docname in self.env.found_docs:
            yield docname

    def write_doc(self, docname, doctree):
        destination = StringOutput(encoding='utf-8')

        self.writer.write(doctree, destination)
        outfilename = path.join(self.outdir, self._get_filename(docname))
        ensuredir(path.dirname(outfilename))
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(self.writer.output)
            finally:
                f.close()
        except (IOError, OSError) as err:
            self.warn("error writing file %s: %s" % (outfilename, err))


def setup(app):
    app.add_builder(MdBuilder)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
