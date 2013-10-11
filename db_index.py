from reshaper import db
from reshaper.ast import get_tu
from optparse import OptionParser
from reshaper.option import setup_options


def parse_options():
    """ parse the command line options and arguments and returns them
    """

    option_parser = OptionParser(usage = "%prog [options] PROJ FILE1 [FILE2...]")
    setup_options(option_parser)
    
    option_parser.add_option("-n", "--new", dest = "new",
                             action="store_true")
    option_parser.add_option("-p", "--post-update", dest = "post_update",
                             action="store_true", default=False)
    
    # handle option or argument error.
    options, args = option_parser.parse_args()
    return option_parser, options, args

def main():
    option_parser, options, args = parse_options()
    if len(args) < 2:
        option_parser.error("Please input at least one source file.")

    proj_engine = db.ProjectEngine(args[0])
    for filename in args[1:]:
        _tu = get_tu(filename, config_path = options.config,
                     cdb_path = options.cdb_path)
        if options.new:
            proj_engine.build_db_tree2(_tu.cursor)
            if options.post_update:
                proj_engine.post_db_update()
        else:
            proj_engine.build_db_tree(_tu.cursor)


if __name__ == '__main__':
    main()
    
