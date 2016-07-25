#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""usage: blobtools seqfilter       -i FASTA -l LIST [-o PREFIX] [-v]
                                    [-h|--help]

    Options:
        -h --help                   show this

        -i, --infile <FASTA>        FASTA file of sequences (Headers are split at whitespaces)
        -l, --list <LIST>           TXT file containing headers of sequences to keep
        -o, --out <PREFIX>          Output prefix
        -v, --invert                Invert filtering (Sequences w/ headers NOT in list)
"""

from __future__ import division
from docopt import docopt

from os.path import basename, isfile, join, dirname, abspath
from sys import path
path.append(dirname(dirname(abspath(__file__))))

import lib.BtLog as BtLog
import lib.BtIO as BtIO

if __name__ == '__main__':
    main_dir = dirname(__file__)
    #print data_dir
    args = docopt(__doc__)
    fasta_f = args['--infile']
    list_f = args['--list']
    invert = args['--invert']
    prefix = args['--out']

    out_f = BtIO.getOutFile(fasta_f, prefix, "filtered.fna")

    print BtLog.status_d['21'] % list_f
    items = BtIO.parseSet(list_f)
    output = []
    print BtLog.status_d['22'] % fasta_f
    seen_items = set()
    for header, sequence in BtIO.readFasta(fasta_f):
        if header in items:
            if not (invert):
                seen_items.add(header)
                output.append(">%s\n%s\n" % (header, sequence))
        else:
            if (invert):
                seen_items.add(header)
                output.append(">%s\n%s\n" % (header, sequence))
        BtLog.progress(len(output), 10, len(items), no_limit=True)
    with open(out_f, "w") as fh:
        fh.write("".join(output))


