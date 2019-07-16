#! /usr/bin/env python

import argparse
import sys
import logging
from logging import config
from ndexutil.config import NDExUtilConfig
import ndexnetworkcollapse

import ndex2

logger = logging.getLogger(__name__)

TSV2NICECXMODULE = 'ndexutil.tsv.tsv2nicecx2'

LOG_FORMAT = "%(asctime)-15s %(levelname)s %(relativeCreated)dms " \
             "%(filename)s::%(funcName)s():%(lineno)d %(message)s"

def _parse_arguments(desc, args):
    """
    Parses command line arguments
    :param desc:
    :param args:
    :return:
    """
    help_fm = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=desc,
                                     formatter_class=help_fm)
    parser.add_argument('--profile', help='Profile in configuration '
                                          'file to use to load '
                                          'NDEx credentials which means'
                                          'configuration under [XXX] will be'
                                          'used '
                                          '(default '
                                          'ndexnetworkcollapse)',
                        default='ndexnetworkcollapse')
    parser.add_argument('--logconf', default=None,
                        help='Path to python logging configuration file in '
                             'this format: https://docs.python.org/3/library/'
                             'logging.config.html#logging-config-fileformat '
                             'Setting this overrides -v parameter which uses '
                             ' default logger. (default None)')

    parser.add_argument('--conf', help='Configuration file to load '
                                       '(default ~/' +
                                       NDExUtilConfig.CONFIG_FILE)
    parser.add_argument('--verbose', '-v', action='count', default=0,
                        help='Increases verbosity of logger to standard '
                             'error for log messages in this module and'
                             'in ' + TSV2NICECXMODULE + '. Messages are '
                             'output at these python logging levels '
                             '-v = ERROR, -vv = WARNING, -vvv = INFO, '
                             '-vvvv = DEBUG, -vvvvv = NOTSET (default no '
                             'logging)')
    parser.add_argument('--version', action='version',
                        version=('%(prog)s ' +
                                 ndexnetworkcollapse.__version__))

    parser.add_argument('--uuid', help='UUID of network to be collapsed', required=True)

    return parser.parse_args(args)


def _setup_logging(args):
    """
    Sets up logging based on parsed command line arguments.
    If args.logconf is set use that configuration otherwise look
    at args.verbose and set logging for this module and the one
    in ndexutil specified by TSV2NICECXMODULE constant
    :param args: parsed command line arguments from argparse
    :raises AttributeError: If args is None or args.logconf is None
    :return: None
    """

    if args.logconf is None:
        level = (50 - (10 * args.verbose))
        logging.basicConfig(format=LOG_FORMAT,
                            level=level)
        logging.getLogger(TSV2NICECXMODULE).setLevel(level)
        logger.setLevel(level)
        return

    # logconf was set use that file
    logging.config.fileConfig(args.logconf,
                              disable_existing_loggers=False)


class NDExNetworkCollapse(object):
    """
    Class to load content
    """
    def __init__(self, args):
        """

        :param args:
        """
        self._conf_file = args.conf
        self._profile = args.profile
        self._user = None
        self._pass = None
        self._server = None

        self._uuid = args.uuid

    def _parse_config(self):
            """
            Parses config
            :return:
            """
            ncon = NDExUtilConfig(conf_file=self._conf_file)
            con = ncon.get_config()
            self._user = con.get(self._profile, NDExUtilConfig.USER)
            self._pass = con.get(self._profile, NDExUtilConfig.PASSWORD)
            self._server = con.get(self._profile, NDExUtilConfig.SERVER)

    def _get_network_from_server(self):
        """
        """

        self._network = ndex2.create_nice_cx_from_server(
            server=self._server, uuid=self._uuid, username=self._user, password=self._pass)

        #import json
        #print('edges:\n {}'.format(json.dumps(self._network.edges, indent=4)))
        #print('\nedgeAttributes:\n {}'.format(json.dumps(self._network.edgeAttributes, indent=4)))
        #print(json.dumps(self._network.edgeAttributes, indent=4))
        #logger.info('Found {:,} unique Ensembl Ids in {}\n'.format(len(ensembl_ids), self._full_file_name))

        return 0


    '''def _check_if_edge_is_duplicate(self, edge, unique_edges):
        edge_is_duplicate = False

        edge_key = (edge['s'], edge['i'], edge['t'])
        edge_key_reverse = (edge['t'], edge['i'], edge['s'])

        if edge_key not in unique_edges and edge_key_reverse not in unique_edges:
            unique_edges[key] = []
         elif key in unique_edges:
            unique_edges[key].append(edge['@id'])
         elif key_reverse in unique_edges:
            unique_edges[key].append(edge['@id'])'''


    def _merge_attributes(self, attribute_list_1, attribute_list_2):

        for attribute1 in attribute_list_1:

            name1 = attribute1['n']

            found = False
            for attribute2 in attribute_list_2:
                if attribute2['n'] == name1:
                    found = True
                    break

            if not found:
                continue

            if attribute1['v'] == attribute2['v']:
                # attriubute with the samae name and value; do not add
                continue


            if not 'd' in attribute1:
                attribute1['d'] = 'list_of_string'
            elif attribute1['d'] == 'boolean':
                attribute1['d'] = 'list_of_boolean'
            elif attribute1['d'] == 'double':
                attribute1['d'] = 'list_of_double'
            elif attribute1['d'] == 'integer':
                attribute1['d'] = 'list_of_integer'
            elif attribute1['d'] == 'long':
                attribute1['d'] = 'list_of_long'
            elif attribute1['d'] == 'string':
                attribute1['d'] = 'list_of_string'


            new_list_of_values = []

            if isinstance(attribute1['v'], list):
                for value in attribute1['v']:
                    if value not in new_list_of_values and value:
                        new_list_of_values.append(value)
            else:
                if attribute1['v'] not in new_list_of_values and attribute1['v']:
                    new_list_of_values.append(attribute1['v'])


            if isinstance(attribute2['v'], list):
                for value in attribute2['v']:
                    if value not in new_list_of_values and value:
                        new_list_of_values.append(value)
            else:
                if attribute2['v'] not in new_list_of_values and attribute2['v']:
                    new_list_of_values.append(attribute2['v'])

            attribute1['v'] = new_list_of_values




    def _generate_map_of_collaspsed_edges(self):

        unique_edges = {}

        # in the loop below, we build a map where key is a tuple (edge_source, interacts, edge_target)
        # and the value is a list of edge ids
        for edge_id, edge in self._network.edges.items():

            edge_key = (edge['s'], edge['i'], edge['t'])
            edge_key_reverse = (edge['t'], edge['i'], edge['s'])


            if edge_key in unique_edges:
                if (edge_id not in unique_edges[edge_key]):
                    unique_edges[edge_key].append(edge_id)

            elif edge_key_reverse in unique_edges:
                if (edge_id not in unique_edges[edge_key_reverse]):
                    unique_edges[edge_key_reverse].append(edge_id)

            else:
                unique_edges[edge_key] = [edge_id]


        print(len(unique_edges))

        # build collapsed edges and collapsed edges attributes
        # and then use them to replace self._network.edges and self._network.edgeAttributes
        collapsed_edges = {}
        collapsed_edgeAttributes = {}


        # create a new edges aspect in collapsed_edges
        for key, list_of_edge_attribute_ids in unique_edges.items():
            edge_id = list_of_edge_attribute_ids.pop(0)
            collapsed_edges[edge_id] = self._network.edges[edge_id]

            if not list_of_edge_attribute_ids:
                collapsed_edgeAttributes[edge_id] = self._network.edgeAttributes[edge_id]
                del self._network.edgeAttributes[edge_id]
                continue


            attribute_list = self._network.edgeAttributes[edge_id]

            # here, the list of collapsed edges is not empty, we need to iterate over it
            # and add attributes of the edge(s) to already existing list of edge attributes
            for attribute_id in list_of_edge_attribute_ids:

                attribute_list_for_adding = self._network.edgeAttributes[attribute_id]

                self._merge_attributes(attribute_list, attribute_list_for_adding)

                collapsed_edgeAttributes[edge_id] = attribute_list

        del self._network.edges
        self._network.edges = collapsed_edges

        del self._network.edgeAttributes
        self._network.edgeAttributes = collapsed_edgeAttributes


    def _get_URL_of_parent_network(self):
        url = self._server if self._server.startswith('http') else 'http://' + self._server
        url = url + '/#/network/' +  self._uuid
        return url


    def _set_network_attributes(self):
        self._network.set_network_attribute(name='prov:wasDerivedFrom', values=self._get_URL_of_parent_network())

    def run(self):
        """
        Runs content loading for NDEx Network Collapse
        :param theargs:
        :return:
        """
        self._parse_config()

        self._get_network_from_server()

        self._generate_map_of_collaspsed_edges()

        self._set_network_attributes()

        self._network.upload_to(self._server, self._user, self._pass)

        return 0

def main(args):
    """
    Main entry point for program
    :param args:
    :return:
    """
    desc = """
    Version {version}

    Loads NDEx Network Collapse data into NDEx (http://ndexbio.org).

    To connect to NDEx server a configuration file must be passed
    into --conf parameter. If --conf is unset the configuration
    the path ~/{confname} is examined.

    The configuration file should be formatted as follows:

    [<value in --profile (default ncipid)>]

    {user} = <NDEx username>
    {password} = <NDEx password>
    {server} = <NDEx server(omit http) ie public.ndexbio.org>


    """.format(confname=NDExUtilConfig.CONFIG_FILE,
               user=NDExUtilConfig.USER,
               password=NDExUtilConfig.PASSWORD,
               server=NDExUtilConfig.SERVER,
               version=ndexnetworkcollapse.__version__)
    theargs = _parse_arguments(desc, args[1:])
    theargs.program = args[0]
    theargs.version = ndexnetworkcollapse.__version__

    try:
        _setup_logging(theargs)
        loader = NDExNetworkCollapse(theargs)
        return loader.run()
    except Exception as e:
        print("\n{}: {}".format(type(e).__name__, e))
        logger.exception(e)
        return 2
    finally:
        logging.shutdown()


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main(sys.argv))
