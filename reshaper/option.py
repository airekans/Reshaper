""" This module contains functions related to settings 
common options for reshaper tools.
"""

def setup_options(option_parser):
    """ setup common options for reshaper tools
    
    Arguments:
    - `option_parser`: optparse.OptionParser compatible object
    """
    option_parser.add_option("-c", "--config", dest = "config",
                             type = "string",
                             help = "Path to the config file. Default is ~/.reshaper.cfg")
    option_parser.add_option("--cdb-path", dest = "cdb_path",
                             type = "string",
                             help = "Directory the compilation database(CDB). "
                             "If not given, do not use CDB.")

    