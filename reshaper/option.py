""" This module contains functions related to settings 
common options for reshaper tools.
"""

import os

    
def setup_options(option_parser):
    """ setup common options for reshaper tools
    
    Arguments:
    - `option_parser`: optparse.OptionParser compatible object
    """
    option_parser.add_option("--config", dest = "config",
                             type = "string",
                             default = os.path.expanduser("~/.reshaper.cfg"),
                             help = "Path to the config file. Default is ~/.reshaper.cfg")
    option_parser.add_option("--cdb-path", dest = "cdb_path",
                             type = "string",
                             help = "Directory the compilation database(CDB). "
                             "If not given, do not use CDB.")


def setup_find_reference_options(option_parser):
    """ setup the common options for find_reference
    
    Arguments:
    - `option_parser`: optparse.OptionParser compatible object
    """
    setup_options(option_parser)

    option_parser.add_option("-f", "--file", dest = "filename",
                             type = "string",
                             help = "Names of file to find reference")
    option_parser.add_option("-s", "--spelling", dest = "spelling",
                             type = "string",
                             help = "spelling of target to find reference")
    option_parser.add_option("-l", "--line", dest = "line",
                             type = "int",
                             help = "line of target to find reference")
    option_parser.add_option("-c", "--column", dest = "column",
                             type = "int",
                             help = "column of target to find reference",
                             default = None)
    option_parser.add_option("-d", "--directory", dest = "directory",
                             type = "string",
                             help = "directory to search for finding reference",
                             default = ".")
    option_parser.add_option("-o", "--output-file", dest = "output_file_name",
                             type = "string",
                             help = "output file name")
    