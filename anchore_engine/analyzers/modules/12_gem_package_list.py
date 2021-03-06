#!/usr/bin/env python3

import sys
import os
import re
import json
import tarfile

import anchore_engine.analyzers.utils

analyzer_name = "package_list"

try:
    config = anchore_engine.analyzers.utils.init_analyzer_cmdline(sys.argv, analyzer_name)
except Exception as err:
    print(str(err))
    sys.exit(1)

imgname = config['imgid']
imgid = imgname
outputdir = config['dirs']['outputdir']
unpackdir = config['dirs']['unpackdir']

pkglist = {}

try:
    allfiles = {}
    if os.path.exists(unpackdir + "/anchore_allfiles.json"):
        with open(unpackdir + "/anchore_allfiles.json", 'r') as FH:
            allfiles = json.loads(FH.read())
    else:
        fmap, allfiles = anchore_engine.analyzers.utils.get_files_from_squashtar(os.path.join(unpackdir, "squashed.tar"))
        with open(unpackdir + "/anchore_allfiles.json", 'w') as OFH:
            OFH.write(json.dumps(allfiles))

    with tarfile.open(os.path.join(unpackdir, "squashed.tar"), mode='r', format=tarfile.PAX_FORMAT) as tfl:
        memberhash = anchore_engine.analyzers.utils.get_memberhash(tfl)

        for tfile in list(allfiles.keys()):
            patt = re.match(".*specifications.*\.gemspec$", tfile)
            if patt:
                thefile = re.sub("^/+", "", tfile)
                try:
                    basemember = memberhash.get(thefile)
                    member = anchore_engine.analyzers.utils._get_extractable_member(tfl, basemember, memberhash=memberhash)
                    with tfl.extractfile(member) as FH:
                        pdata = str(FH.read(), 'utf-8')
                        precord = anchore_engine.analyzers.utils.gem_parse_meta(pdata)
                        for k in list(precord.keys()):
                            record = precord[k]
                            pkglist[tfile] = json.dumps(record)
                except Exception as err:
                    import traceback
                    traceback.print_exc()
                    print("WARN: found gemspec but cannot parse (" + str(tfile) +") - exception: " + str(err))

except Exception as err:
    import traceback
    traceback.print_exc()
    raise err

if pkglist:
    ofile = os.path.join(outputdir, 'pkgs.gems')
    anchore_engine.analyzers.utils.write_kvfile_fromdict(ofile, pkglist)

sys.exit(0)
