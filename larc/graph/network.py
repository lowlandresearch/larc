import networkx as nx
import toolz.curried as _

from .. import common as __
from . import common

class node_types:
    hostname = 'hostname'
    ip = 'ip'
    local_admin = 'local_admin'
    admin = local_admin
    group = 'group'
    user = 'user'
    session = 'session'
    domain = 'domain'
    trust = 'trust'
    finding = 'finding'
    finding_i = 'finding_i'
    vuln = finding
    vuln_i = finding_i
    scan = 'scan'
    software = 'software'
    tag = 'tag'
    label = 'tag'
    endpoint = 'endpoint'
    port = 'port'
    service = 'service'
    fingerprint = 'fingerprint'
    os = 'os'
    likely_os = os

    relations = (
        (ip, 'many', hostname),
        (hostname, 'many', ip),

        (ip, 'many', local_admin),
        (hostname, 'many', local_admin),

        (ip, 'many', session),
        (hostname, 'many', session),

        (ip, 'many', finding),
        (hostname, 'many', finding),

        (ip, 'many', fingerprint),
        (hostname, 'many', fingerprint),

        (ip, 'many', software),
        (hostname, 'many', software),

        (ip, 'one', domain),
        (domain, 'many', ip),
        (hostname, 'one', domain),
        (domain, 'many', hostname),

        (local_admin, 'one', user),

        (domain, 'many', group),
        (group, 'one', domain),
        
        (domain, 'many', user),
        (user, 'one', domain),
        
        (domain, 'many', trust),
        (trust, 'one', domain),

        (finding, 'many', tag),
        (tag, 'many', finding),
        
        (ip, 'many', endpoint),
        (hostname, 'many', endpoint),

        (endpoint, 'one', ip),
        (endpoint, 'one', hostname),
        (endpoint, 'one', port),
        (endpoint, 'many', service),
        (endpoint, 'many', finding),

        (port, 'many', endpoint),
        
        (service, 'many', fingerprint),
    )

type_selectors = {
    aname: common.neighbors_of_type(getattr(node_types, aname))
    for aname in node_types.__dict__
    if not aname.startswith('_') and aname != 'relations'
}

# class type_selectors:
#     for aname in node_types.__dict__:
#         if not aname.startswith('_') and aname != 'relations':
#             attr = getattr(node_types, aname)
#             locals()[aname] = common.neighbors_of_type(attr)
            
#     # fingerprint = common.neighbors_of_type(node_types.fingerprint)
#     # host = common.neighbors_of_type(node_types.host)
#     # hostname = common.neighbors_of_type(node_types.hostname)
#     name = hostname
#     finding = common.neighbors_of_type(node_types.finding)
#     vuln = finding
#     tag = common.neighbors_of_type(node_types.tag)
#     port = common.neighbors_of_type(node_types.port)

def graph_pipe(*function_spaces: common.FunctionSpace):
    return common.graph_pipe(*_.concatv([type_selectors], function_spaces))

def new_graph(graph, *function_spaces):
    return common.Graph(graph, graph_pipe(*function_spaces))
