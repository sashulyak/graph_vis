"""
This code parse and cleanup users' data.
Then create graph by users' phone book contacts.
And finally saves it into GEXF format.
"""
import json
from typing import Any, Dict, List, Tuple
from collections import Counter
from itertools import chain


RAW_DATA_PATH = 'contacts.json'
GRAPH_DATA_PATH = 'graph.gexf'
CONNECTIVITY_THRESHOLD = 10
GEXF_COLOR_TEMPLATE='<viz:color hex="#{hex}"/>'
GEXF_ATTRIBUTES_TEMPLATE = (
    '<attvalues>'
        '<attvalue for="0" value="{id}"/>'
        '<attvalue for="1" value="{name}"/>'
        '<attvalue for="2" value="{phone}"/>'
    '</attvalues>'
)
GEXF_NODE_TEMPLATE = '<node id="{id}" label="{label}">\n{color}\n{attributes}\n</node>\n'
GEXF_EDGE_TEMPLATE = '<edge source="{source_id}" target="{target_id}"><viz:color hex="#000"/></edge>\n'
GEXF_GRAPH_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<gexf xmlns="http://gexf.net/1.3" xmlns:viz="http://gexf.net/1.3/viz" version="1.3">\n'
        '<graph mode="static" defaultedgetype="directed">\n'
            '<attributes class="node">\n'
                '<attribute id="0" title="id" type="string"/>\n'
                '<attribute id="1" title="name" type="string"/>\n'
                '<attribute id="2" title="phone" type="string"/>\n'
            '</attributes>\n'
            '<nodes>\n{nodes}</nodes>\n'
            '<edges>\n{edges}</edges>\n'
        '</graph>\n'
    '</gexf>\n'
)


def read_raw_data(raw_data_path: str) -> List[Dict[str, Any]]:
    """
    Read data from the source json file.
    
    :param raw_data_path: path to the raw data json
    :return: list of dictionaries with raw data
    """
    with open(raw_data_path) as json_fp:
        raw_data = json.load(json_fp)

    return raw_data


def get_registered_users(raw_data: Dict) -> Dict[str, Dict]:
    """
    Get registered users and their attributes.

    :param raw_data: list of dictionaries with raw data
    :return: registered users and their attributes.
             key - phone number, value - attributes dict
    """
    print('Getting registered users ...')
    registered_users = {}
    for user in raw_data:
        registered_users[user['phoneNumber']] = {
            'account_id': user['accountId'],
            'display_name': user['displayName'],
            'ziiname': user['ziiname'],
        }

    print(f'Got {len(registered_users)} registered users.')
    return registered_users


def get_phones_adjacency(
        registered_users:  Dict[str, Dict],
        users_non_registered_contacts: Dict[str, List[str]]
) -> List[List[str]]:
    """
    Get rows of adjacent phone contacts.

    :param registered_users: users who alreade registered on service
    :param users_non_registered_contacts: dict of registered users
                                          and their contacts cleared from
                                          other registered users
    :return: list of rows where each first element of the row
             is adjacent to the rest elements of the row
             (have them in contacts list) 
    """
    print('Getting phones adjacency ...')
    phones_adjacency = []
    for user in list(registered_users.keys()):
        phones_adjacency.append(
            [user] + users_non_registered_contacts[user]
        )
    print('Got phones adjacency.')
    return phones_adjacency


def get_users_non_registered_contacts(raw_data: Dict, registered_users: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Remove registered users from contact lists.

    Because we don't want to send them advertisement.

    :param raw_data_path: path to the raw data json
    :param registered_users: users who alreade registered on service
    :return: dict of registered users and their contacts cleared from other registered users
    """
    print('Getting user\'s non registered contacts ...')
    users_non_registered_contacts = {}
    for user in raw_data:
        user_contacts = []
        for phone in set(user['contactList']):
            if phone not in registered_users:
                user_contacts.append(phone)
        users_non_registered_contacts[user['phoneNumber']] = user_contacts
    print('Got non registered phones.')
    return users_non_registered_contacts


def get_connectivity_degrees(users_non_registered_contacts: Dict[str, List[str]]) -> Dict[str, int]:
    """
    :param users_non_registered_contacts: dict of registered users
                                          and their contacts cleared from
                                          other registered users
    :return: how many times each phone number
             appeared in others' phone books
    """
    print('Getting connectivity degrees ...')
    plain_contacts = list(chain.from_iterable(list(users_non_registered_contacts.values())))
    connectivity_degrees = dict(Counter(plain_contacts))
    print('Got connectivity degrees.')
    return connectivity_degrees


def create_gexf_graph(
        phones_adjacency: List[List[str]],
        registered_users: Dict[str, Dict],
        connectivity_degrees: Dict[str, int]
) -> None:
    """
    Create GEXF grapf structure.

    More about GEXF format: https://gexf.net/.
    
    :param phones_adjacency: list of rows where each first element of the row
                             is adjacent to the rest elements of the row
                             (have them in contacts list) 
    :param registered_users: users who alreade registered on service
    :param connectivity_degrees: how many times each phone number
                                 appeared in others' phone books
    """
    plain_phones = list(chain.from_iterable(phones_adjacency))
    unique_phones = list(set(plain_phones))

    nodes = create_gexf_nodes(registered_users, connectivity_degrees, unique_phones)
    edges = create_gexf_edges(phones_adjacency)

    nodes_string = ''.join(nodes)
    edges_string = ''.join(edges)
    graph_string = GEXF_GRAPH_TEMPLATE.format(nodes=nodes_string, edges=edges_string)

    with open(GRAPH_DATA_PATH, 'w') as gexf_fp:
        gexf_fp.write(graph_string)


def create_gexf_nodes(
        registered_users: Dict[str, Dict],
        connectivity_degrees: Dict[str, int],
        unique_phones: List[str]
) -> List[str]:
    """
    Create GEXF nodes for the graph structure.

    :param registered_users: users who alreade registered on service
    :param connectivity_degrees: how many times each phone number
                                 appeared in others' phone books
    :param unique_phones: all phone numbers without repetition
    :return: list of nodes in GEXF format
    """
    nodes = []
    for phone in unique_phones:
        if phone in registered_users:
            color = GEXF_COLOR_TEMPLATE.format(hex='ce54ff')
            attributes = GEXF_ATTRIBUTES_TEMPLATE.format(
                id=registered_users[phone]['account_id'],
                name=registered_users[phone]['display_name'],
                phone=phone
            )
            label = registered_users[phone]['display_name']
        elif connectivity_degrees[phone] >= CONNECTIVITY_THRESHOLD:
            color = GEXF_COLOR_TEMPLATE.format(hex='ffff00')
            attributes = GEXF_ATTRIBUTES_TEMPLATE.format(
                id='',
                name='',
                phone=phone
            )
            label = '???'
        else:
            color = GEXF_COLOR_TEMPLATE.format(hex='333333')
            attributes = GEXF_ATTRIBUTES_TEMPLATE.format(
                id='',
                name='',
                phone=phone[:5] + '...'
            )
            label = '???'

        node_string = GEXF_NODE_TEMPLATE.format(
            id=phone,
            label=label,
            color=color,
            attributes=attributes
        )
        nodes.append(node_string)
    return nodes


def create_gexf_edges(phones_adjacency: List[List[str]]) -> List[str]:
    """
    Create GEXF edges for the graph structure.

    :param phones_adjacency: list of rows where each first element of the row
                             is adjacent to the rest elements of the row
                             (have them in contacts list)
    :return: list of edges in GEXF format
    """
    edges = []
    for row in phones_adjacency:
        source = row[0]
        for target in row[1:]:
            edges.append(GEXF_EDGE_TEMPLATE.format(source_id=source, target_id=target))

    return edges


if __name__ == '__main__':
    raw_data = read_raw_data(RAW_DATA_PATH)

    registered_users = get_registered_users(raw_data)
    users_non_registered_contacts = get_users_non_registered_contacts(raw_data, registered_users)
    connectivity_degrees = get_connectivity_degrees(users_non_registered_contacts)
    phones_adjacency = get_phones_adjacency(registered_users, users_non_registered_contacts)

    create_gexf_graph(phones_adjacency, registered_users, connectivity_degrees)
