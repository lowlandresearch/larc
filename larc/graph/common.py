'''Functiona graph analysis tools

'''
from pathlib import Path
import json
import hashlib
import logging
import re
import abc
import types
import typing as T

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

import toolz.curried as _
import networkx as nx

from .. import common as __

class _graph_null(__._null):
    _instance = None

    def __repr__(self):
        return 'GraphNull'

    def __gt__(self, function):
        return function(self)

GraphNull = _graph_null()
    
GraphFunction = T.Callable[['...'], nx.Graph]

def node_type(graph, node_id):
    return graph.nodes[node_id]['type']

_traversal_functions = set()
def traversal_function(func):
    _traversal_functions.add(func.__name__)
    return func

def is_traversal_function(function):
    return function.__name__ in _traversal_functions
        
_introspect_functions = set()
def introspect_function(func):
    _introspect_functions.add(func.__name__)
    return func

def is_introspect_function(function):
    return function.__name__ in _introspect_functions

_edge_functions = set()
def edge_function(func):
    _edge_functions.add(func.__name__)
    return func
        
Selector = T.Callable[[nx.Graph, T.Any, dict], bool]

@_.curry
@traversal_function
def neighbor_selector(selectors: T.Iterable[Selector],
                      graph: nx.Graph, node_id: T.Any,
                      **attrs) -> T.Iterable[T.Tuple[T.Any, dict]]:
    if attrs:
        selectors = _.concatv(
            selectors, [lambda graph, node_id, edge_data: all(
                v(graph.nodes[node_id][k]) for k, v in attrs.items()
            )],
        )
    return _.pipe(
        graph[node_id].items(),
        __.vfilter(lambda node_id, edge_data: all(
            s(graph, node_id, edge_data) for s in selectors
        )),
    )

@_.curry
@traversal_function
def neighbors_of_type(type, graph, node_id, *,
                      edge_selector=lambda n, e: True):
    return _.pipe(
        graph[node_id].items(),
        __.vfilter(lambda nid, edata: node_type(graph, nid) == type),
        __.vfilter(edge_selector),
        _.map(_.first),
    )

@_.curry
@introspect_function
def get(key: str, graph: nx.Graph, node_id: T.Any):
    return _.pipe(
        graph.nodes[node_id],
        __.jmes(key),
    )

@_.curry
@edge_function
def e_get(key: str, graph: nx.Graph, v0: T.Any, v1: T.Any):
    return _.pipe(
        graph.edges,
    )

@_.curry
@introspect_function
def items(graph: nx.Graph, node_id: T.Any):
    return graph.nodes[node_id].items()

FunctionSpace = T.Dict[str, T.Callable]

def to_function_space(f_space: T.Union[type, FunctionSpace,
                                       T.Iterable[T.Callable]]):
    if __.is_dict(f_space):
        return f_space
    if __.is_seq(f_space):
        return {
            f.__name__: f for f in f_space
        }
    return _.pipe(
        f_space.__dict__.items(),
        __.vfilter(lambda k, v: not (k.startswith('__') and k.endswith('__'))),
        dict,
    )

def graph_pipe(*function_spaces: FunctionSpace):
    @_.curry
    def pipe(graph, selection):
        return GraphPipe(
            graph, selection,
            *_.pipe(
                _.concatv(
                    [{
                        'neighbors_of_type': neighbors_of_type,
                        'neighbor_selector': neighbor_selector,
                        'get': get,
                        'items': items,
                    }],
                    function_spaces,
                ),
                _.map(to_function_space),
            )
        )
    return pipe

class GraphPipe:
    def __init__(self, graph, selection, *function_spaces):
        self.graph = graph
        self.selection = selection
        self.function_space = _.merge(*function_spaces)

    def __or__(self, function):
        if __.is_str(function):
            # function = globals()[function]
            log.debug(f'function space: {self.function_space}')
            function = eval(function, self.function_space)

        if is_traversal_function(function):
            nids, _neighbors = zip(*self.selection)

            return _.pipe(
                # self.selection,
                # _.mapcat(_.second),
                nids,
                # _.concat,
                set,
                # _.do(print),
                _.map(function(self.graph)),
                _.mapcat(tuple),
                set,
                lambda node_ids: self.graph(*node_ids),
            )
        elif is_introspect_function(function):
            node_ids, _nb = zip(*self.selection)
            return _.pipe(
                node_ids,
                set,
                _.map(function(self.graph)),
                ValuePipe,
            )
        else:
            node_ids, _nb = zip(*self.selection)
            return ValuePipe(function(node_ids))
            
    def __gt__(self, function):
        node_ids, _nb = zip(*self.selection)
        return function(node_ids)

class ValuePipe:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return repr(self.value)

    def __or__(self, other):
        if callable(other):
            return ValuePipe(other(self.value))
        return self.value | other

    def __gt__(self, function):
        return function(self.value)

class Graph(nx.DiGraph):
    def __init__(self, data, graph_pipe, **attr):
        self.graph_pipe = graph_pipe
        super().__init__(data, **attr)

    def __call__(self, *node_ids):
        if len(node_ids) == 1 and __.is_seq(node_ids[0]):
            node_ids = tuple(node_ids[0])

        bad_ids = _.pipe(
            node_ids,
            _.filter(lambda i: i not in self),
            tuple,
        )
        if bad_ids:
            bad_str = _.pipe(bad_ids, _.map(str), ', '.join)
            log.error(f'Bad node ids: {bad_str}')

        # log.info(type(node_ids[0]))
        node_ids = set(node_ids) - set(bad_ids)
        # log.info(node_ids)
        if not node_ids:
            log.error('No ids left')
            return GraphNull
            
        return _.pipe(
            node_ids,
            _.map(lambda n: (n, self[n])),
            self.graph_pipe(self),
        )
    
    def of_type(self, type):
        return _.pipe(
            self,
            _.filter(lambda n: self.nodes[n]['type'] == type),
            _.map(lambda n: (n, self[n])),
            self.graph_pipe(self),
        )

    # @_.curry
    # @classmethod
    # def from_graph_function(cls, function: GraphFunction, *a, **kw):
    #     return cls(function(*a, **kw))

