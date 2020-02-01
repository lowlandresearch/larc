import networkx as nx
import toolz.curried as _

from .. import common as __
from . import common

class node_types:
    hostname = 'hostname'
    host = 'host'
    finding = 'finding'
    vuln = 'finding'
    scan = 'scan'
    software = 'software'
    tag = 'tag'
    label = 'tag'
    endpoint = 'endpoint'
    port = 'port'
    service = 'service'
    fingerprint = 'fingerprint'
    likely_os = 'os'

    relations = (
        (host, 'has_many', hostname),
        (host, 'has_many', finding),
        (host, 'has_many', fingerprint),
        (host, 'has_many', software),
        (finding, 'has_many', tag),
        (host, 'has_many', endpoint),
        (endpoint, 'has_a', port),
        (endpoint, 'has_many', service),
        (service, 'has_many', fingerprint),
    )

class node_functions:
    fingerprint = common.neighbors_of_type(node_types.fingerprint)
    host = common.neighbors_of_type(node_types.host)
    hostname = common.neighbors_of_type(node_types.hostname)
    name = hostname
    finding = common.neighbors_of_type(node_types.finding)
    vuln = finding
    tag = common.neighbors_of_type(node_types.tag)
    port = common.neighbors_of_type(node_types.port)

def graph_pipe(*function_spaces: common.FunctionSpace):
    return common.graph_pipe(*_.concatv([node_functions], function_spaces))

def new_graph(graph, *function_spaces):
    return common.Graph(graph, graph_pipe(*function_spaces))
