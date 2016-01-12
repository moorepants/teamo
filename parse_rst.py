# -*- coding: utf-8 -*-

"""
Extract title and metadata from a reStructuredText document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This functionality was sourced out of the docutils_ integration of the
`homework productions`_ web application.

Its purpose is to transform reStructuredText_ documents to HTML, but extract
the title and metadata before rendering the body and provide them separately.

The resulting HTML content would then be assembled from those fragments, but
with more flexibility (e.g. the document's date and tags can be rendered
according to a template instead of how docutils_ would generate markup).

The metadata is parsed from a reStructuredText_ field list. The fields that
should be extracted have to be specified along with a function that parses
the string value. Unspecified fields are discarded.

.. _docutils: http://docutils.sourceforge.net/
.. _homework productions: http://homework.nwsnet.de/
.. _reStructuredText: http://docutils.sourceforge.net/rst.html

:Copyright: 2007-2012 Jochen Kupperschmidt
:Date: 13-Jun-2012
:License: MIT
"""

from collections import namedtuple
from contextlib import contextmanager
from datetime import date, datetime

from docutils import core, io, nodes, readers


DocumentParts = namedtuple('DocumentParts', ['metadata', 'title', 'body'])

def parse_document(input_string, field_names_and_parsers):
    """
    Parse the input string as a reStructuredText document and return these
    values, wrapped in a named tuple:

    - ``metadata``: A dictionary with metadata extracted from the first field
      list in the document. A field is only considered if it is explicitly
      specified, and its value will be transformed using the function assigned
      for it.

    - ``title``: The document's first-level heading.

    - ``body``: The document body, rendered as HTML. This will not include the
      first field list and the first-level heading unless ``False`` is passed
      passed as the value of the ``remove`` argument.
    """
    overrides = {
        # Disable the promotion of a lone top-level section title to document
        # title (and subsequent section title to document subtitle promotion).
        'docinfo_xform': 0,
        'initial_header_level': 2,
    }

    # Read tree and extract metadata.
    doctree = core.publish_doctree(input_string, settings_overrides=overrides)

    title = extract_title(doctree)
    metadata = extract_metadata(doctree, field_names_and_parsers)

    # Parse content.
    reader = readers.doctree.Reader(parser_name='null')
    pub = core.Publisher(reader, source=io.DocTreeInput(doctree),
         destination_class=io.StringOutput)
    pub.set_writer('html')
    # Make ``initial_header_level`` work.
    pub.process_programmatic_settings(None, overrides, None)
    pub.publish()

    return DocumentParts(
        metadata=metadata,
        title=title,
        body=pub.writer.parts['html_body'],
    )

@contextmanager
def find_node_by_class(doctree, node_class, remove):
    """Find the first node of the specified class."""
    index = doctree.first_child_matching_class(node_class)
    if index is not None:
        yield doctree[index]
        if remove:
            del doctree[index]
    else:
        yield

def extract_title(doctree, remove=True):
    """Find, extract, optionally remove, and return the document's first
    heading (which is assumed to be the main title).
    """
    with find_node_by_class(doctree, nodes.title, remove) as node:
        if node is not None:
            return node.astext()

def extract_metadata(doctree, field_names_and_parsers, remove=True):
    """Find, extract, optionally remove, and return the values for the
    specified names from the document's first field list (which is assumed to
    represent the document's meta data).
    """
    field_names = frozenset(field_names_and_parsers.keys())
    metadata = dict.fromkeys(field_names)

    with find_node_by_class(doctree, nodes.field_list, remove) as node:
        if node is not None:
            field_nodes = select_field_nodes(node, field_names)
            # Parse each field's value using the function
            # specified for the field's name.
            for name, value in field_nodes:
                metadata[name] = field_names_and_parsers[name](value)

    return metadata

def select_field_nodes(subtree, names):
    """Return a (name, value) pair for any node with one of the given names."""
    field_nodes = (node for node in subtree if node.__class__ is nodes.field)
    for field_node in field_nodes:
        name = field_node[0].astext().lower()
        if name in names:
            value = field_node[1].astext()
            yield name, value


# tests
#

TEST_INPUT = """\
=======
Example
=======

:Id: 42
:Author: John Doe
:Date: 2012-06-13
:Version: 0.1
:Tags: crazy, plain stupid, crazy, unexpected
:SomethingElse: This should be ignored.

Once upon a time ...\
"""

def test_parse_document():
    """Example usage as well as unit test."""
    expected = DocumentParts(
        metadata={
            'id': 42,
            'author': 'John Doe',
            'date': date(2012, 6, 13),
            'version': '0.1',
            'tags': frozenset(['crazy', 'plain stupid', 'unexpected']),
        },
        title='Example',
        body \
            = '<div class="document" id="example">\n' \
            + '<p>Once upon a time ...</p>\n</div>\n',
    )

    # Define field names to watch out for as well as
    # functions to parse their values.
    field_names_and_parsers = {
        'id': int,
        'author': str,
        'date': lambda s: datetime.strptime(s, '%Y-%m-%d').date(),
        'version': str,
        'tags': lambda s: frozenset(map(unicode.strip, s.split(','))),
    }

    actual = parse_document(TEST_INPUT, field_names_and_parsers)

    # Compare actual to expected values.
    for attr_name in 'metadata', 'title', 'body':
        assert_helper(actual, expected, attr_name)

def assert_helper(actual_obj, expected_obj, attr_name):
    actual = getattr(actual_obj, attr_name)
    expected = getattr(expected_obj, attr_name)
    assert actual == expected, \
        'Value of attribute "%s" must be %r but is %r.' \
            % (attr_name, expected, actual)

#
# /tests

if __name__ == '__main__':
    print('Running tests ...')
    test_parse_document()
    print('alright!')
