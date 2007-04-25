#!/usr/bin/env python

#-----------------------------------------------------------------------------
# Name:        ArchGenXML.py
# Purpose:     generating plone products (archetypes code) out of an UML-model
#
# Author:      Philipp Auersperg
#
# Created:     2003/16/04
# Copyright:   (c) 2003 BlueDynamics
# Licence:     GPL
#-----------------------------------------------------------------------------

# originally inspired Dave Kuhlman's generateDS Copyright (c) 2003 Dave Kuhlman

from OptionParser import parser
from pkg_resources import resource_filename
import archgenxml
import logging
import sys
import utils
import os

try:
    # for standalone use
    from ArchetypesGenerator import ArchetypesGenerator
except ImportError:
    # if installed in site-packages:
    from ArchGenXML.ArchetypesGenerator import ArchetypesGenerator

def main():
    utils.initLog('archgenxml.log')
    utils.addConsoleLogging()
    log = logging.getLogger('main')

    log.debug("Initializing zope3 machinery...")
    ZOPEPATHFILE = '.agx_zope_path'
    userDir = os.path.expanduser('~')
    pathFile = os.path.join(userDir, ZOPEPATHFILE)
    if os.path.exists(pathFile):
        f = open (pathFile)
        additionalPath = f.readline().strip()
        f.close()
        sys.path.insert(0, additionalPath)
        log.debug("Read %s, added %s in front of the PYTHONPATH.",
                  pathFile, additionalPath)
    try:
        from zope import component
        from zope.configuration import xmlconfig
    except ImportError:
        log.error("Could not import zope3 components.\n"
                  "They are not available on the PYTHONPATH.\n"
                  "Alternatively, you can place the path location "
                  "in ~/%s.\n"
                  "Put something like /opt/zope2.10.3/lib/python "
                  "in there.", ZOPEPATHFILE)
        if os.path.exists(pathFile):
            log.error("Hm. Apparently the file already exists. "
                      "Sure it points at a good zope's /lib/python "
                      "directory? A good zope is 2.9 or 3.3+.")
        sys.exit(1)
    zcmlConfigFile = resource_filename(__name__, 'configure.zcml')
    xmlconfig.file(zcmlConfigFile, package=archgenxml)
    log.debug("Finished initializing zope3 machinery.")

    log.debug("Reading command line options first.")
    (settings, args) = parser.parse_args()
    # Note: settings is all that the parser can recognize and parse
    # from the command line arguments. 'args' is everything else
    # that's left. The first (and probably only) left-over argument
    # should be the model file
    try:
        model = args[0]
        log.debug("Model file is '%s'.", model)
    except:
        log.critical("Hey, we need to be passed a UML file as an argument!")
        parser.print_help()
        sys.exit(2)
    log.info(utils.ARCHGENXML_VERSION_LINE, str(utils.version()))
    # This is a little bit hacky. Probably should read optparse's doc
    # better. [Reinout]
    log.debug("Figuring out the settings we're passing to the "
              "main program...")
    keys = dir(settings)
    keys = [key for key in keys
            if not key.startswith('_')
            and not key in ['ensure_value', 'read_file', 'read_module']]
    log.debug("Keys available through the option parser: %r.",
              keys)
    options = {}
    for key in keys:
        options[key] = getattr(settings, key)
        log.debug("Option '%s' has value '%s'.",
                  key, options[key])

    # if outfilename is not given by the -o option try getting the second
    # regular argument
    if not options['outfilename']:
        log.debug("Outfilename not specified in the options. "
                  "Trying second loose commandline argument.")
        if len(args) > 1:
            options['outfilename']=args[1]
        else:
            log.debug("No second argument found: keeping outfilename empty.")
            # the output dir will be named after the model

    # hook into sys.excepthook if the user requested it
    if options['pdb_on_exception']:
        sys.excepthook = info

    # start generation
    gen=ArchetypesGenerator(model, **options)
    gen.parseAndGenerate()

def info(type, value, tb):
    # from http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/65287
    if hasattr(sys, 'ps1') or not (
        sys.stderr.isatty() and sys.stdin.isatty()):
        # Interactive mode, no tty-like device, or syntax error: nothing
        # to do but call the default hook
        sys.__excepthook__(type, value, tb)
    else:
        import traceback, pdb
        # You are NOT in interactive mode; so, print the exception...
        traceback.print_exception(type, value, tb)
        print
        # ... then start the debugger in post-mortem mode
        pdb.pm()

if __name__ == '__main__':
    main()
