"""
Visualize a topology using Graphviz.
"""
# This code is based on the code from Dask's dot module
from __future__ import absolute_import, print_function

import os
from functools import partial

from six import iteritems

from ..dsl.spout import JavaSpoutSpec, ShellSpoutSpec
from ..util import get_topology_definition, get_topology_from_file
from .common import add_name

try:
    import graphviz
    HAVE_GRAPHVIZ = True
except:
    HAVE_GRAPHVIZ = False


IPYTHON_IMAGE_FORMATS = frozenset(['jpeg', 'png'])
IPYTHON_NO_DISPLAY_FORMATS = frozenset(['dot', 'pdf'])


def to_graphviz(topology_class, node_attr=None, edge_attr=None, **kwargs):
    """Convert a Topology into a DiGraph"""
    if not HAVE_GRAPHVIZ:
        raise ImportError('The visualize command requires the `graphviz` Python'
                          ' library and `graphviz` system library to be '
                          'installed.')
    attributes = {'fontsize': '16',
                  'fontcolor': 'white',
                  'bgcolor': '#333333',
                  'rankdir': 'LR'}
    node_attributes = {'fontname': 'Helvetica',
                       'fontcolor': 'white',
                       'color': 'white',
                       'style': 'filled',
                       'fillcolor': '#006699'}
    edge_attributes = {'style': 'solid',
                       'color': 'white',
                       'arrowhead': 'open',
                       'fontname': 'Helvetica',
                       'fontsize': '12',
                       'fontcolor': 'white'}
    attributes.update(kwargs)
    if node_attr is not None:
        node_attributes.update(node_attr)
    if edge_attr is not None:
        edge_attributes.update(edge_attr)
    g = graphviz.Digraph(graph_attr=attributes, node_attr=node_attributes,
                         edge_attr=edge_attributes)

    all_specs = {}
    all_specs.update(topology_class.thrift_bolts)
    all_specs.update(topology_class.thrift_spouts)

    sametail_nodes = set()

    for spec in topology_class.specs:
        if isinstance(spec, (JavaSpoutSpec, ShellSpoutSpec)):
            shape = 'box'
        else:
            shape = None
        g.node(spec.name, label=spec.name, shape=shape)
        for stream_id, grouping in list(iteritems(spec.inputs)):
            parent = stream_id.componentId
            outputs = all_specs[parent].common.streams[stream_id.streamId].output_fields
            label = ('Stream: {}\lFields: {}\lGrouping: {}\l'
                     .format(stream_id.streamId, outputs, grouping))
            sametail = '{}-{}'.format(parent, stream_id.streamId)
            if sametail not in sametail_nodes:
                g.node(sametail, shape='point', width='0')
                g.edge(parent, sametail, label=label, dir='none')
                sametail_nodes.add(sametail)
            g.edge(sametail, spec.name, samehead=str(outputs))

    return g


def _get_display_cls(format):
    """
    Get the appropriate IPython display class for `format`.

    Returns `IPython.display.SVG` if format=='svg', otherwise
    `IPython.display.Image`.

    If IPython is not importable, return dummy function that swallows its
    arguments and returns None.
    """
    dummy = lambda *args, **kwargs: None
    try:
        import IPython.display as display
    except ImportError:
        # Can't return a display object if no IPython.
        return dummy

    if format in IPYTHON_NO_DISPLAY_FORMATS:
        # IPython can't display this format natively, so just return None.
        return dummy
    elif format in IPYTHON_IMAGE_FORMATS:
        # Partially apply `format` so that `Image` and `SVG` supply a uniform
        # interface to the caller.
        return partial(display.Image, format=format)
    elif format == 'svg':
        return display.SVG
    else:
        raise ValueError("Unknown format '%s' passed to `dot_graph`" % format)


def visualize_topology(name=None, filename=None, format=None, **kwargs):
    """
    Render a topology graph using dot.

    If `filename` is not None, write a file to disk with that name in the
    format specified by `format`.  `filename` should not include an extension.

    Parameters
    ----------
    name : str
        The name of the topology to display.
    filename : str or None, optional
        The name (without an extension) of the file to write to disk.  If
        `filename` is None, no file will be written, and we communicate with
        dot using only pipes.  Default is `name`.
    format : {'png', 'pdf', 'dot', 'svg', 'jpeg', 'jpg'}, optional
        Format in which to write output file.  Default is 'png'.
    **kwargs
        Additional keyword arguments to forward to `to_graphviz`.

    Returns
    -------
    result : None or IPython.display.Image or IPython.display.SVG  (See below.)

    Notes
    -----
    If IPython is installed, we return an IPython.display object in the
    requested format.  If IPython is not installed, we just return None.

    We always return None if format is 'pdf' or 'dot', because IPython can't
    display these formats natively. Passing these formats with filename=None
    will not produce any useful output.
    """
    name, topology_file = get_topology_definition(name)
    topology_class = get_topology_from_file(topology_file)

    if filename is None:
        filename = name

    g = to_graphviz(topology_class, **kwargs)

    fmts = ['.png', '.pdf', '.dot', '.svg', '.jpeg', '.jpg']
    if format is None and any(filename.lower().endswith(fmt) for fmt in fmts):
        filename, format = os.path.splitext(filename)
        format = format[1:].lower()

    if format is None:
        format = 'png'

    data = g.pipe(format=format)
    if not data:
        raise RuntimeError("Graphviz failed to properly produce an image. "
                           "This probably means your installation of graphviz "
                           "is missing png support. See: "
                           "https://github.com/ContinuumIO/anaconda-issues/"
                           "issues/485 for more information.")

    display_cls = _get_display_cls(format)

    if not filename:
        return display_cls(data=data)

    full_filename = '.'.join([filename, format])
    with open(full_filename, 'wb') as f:
        f.write(data)

    return display_cls(filename=full_filename)


def subparser_hook(subparsers):
    """ Hook to add subparser for this command. """
    subparser = subparsers.add_parser('visualize',
                                      description=__doc__,
                                      help=main.__doc__)
    subparser.set_defaults(func=main)
    add_name(subparser)
    subparser.add_argument('-f', '--format',
                           help='File extension for graph file. Defaults to PNG')
    subparser.add_argument('-o', '--output_file',
                           help='Name of output file. Defaults to NAME.FORMAT')


def main(args):
    """Create a Graphviz visualization of the topology"""
    visualize_topology(name=args.name, format=args.format,
                       filename=args.output_file)
