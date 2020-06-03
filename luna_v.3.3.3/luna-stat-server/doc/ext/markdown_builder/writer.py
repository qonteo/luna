from docutils import languages
from docutils import writers

import pypandoc

from ext.sphinxcontrib.writers.rst import RstWriter


class MdWriter(RstWriter):
    supported = ('text',)
    settings_spec = ('No options here.', '', ())
    settings_defaults = {}

    output = None

    def __init__(self, builder):
        writers.Writer.__init__(self)
        self.builder = builder

    def translate(self):
        super().translate()
        self.output = pypandoc.convert_text(
            self.output, to='markdown_mmd', format='rst'
        )
