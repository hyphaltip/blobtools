#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
import lib.BtLog as BtLog
import lib.BtIO as BtIO
import lib.BtTax as BtTax
from os.path import abspath, isfile, basename

class BlobDb():
    '''
    class BlobDB holds all information parsed from files
    '''
    def __init__(self, title):
        self.title = title
        self.assembly_f = ''
        self.dict_of_blobs = {}
        self.order_of_blobs = [] # ordereddict
        self.set_of_taxIds = set()
        self.lineages = {}
        self.length = 0
        self.seqs = 0
        self.n_count = 0
        self.covLibs = {}
        self.hitLibs = {}
        self.nodesDB_f = ''
        self.taxrules = []
        self.version = ''

    def view(self, **kwargs):
        # arguments
        print BtLog.status_d['14']
        viewObjs = kwargs['viewObjs']
        ranks = kwargs['ranks']
        taxrule = kwargs['taxrule']
        hits_flag = kwargs['hits_flag']
        seqs = kwargs['seqs']
        cov_libs = kwargs['cov_libs']
        # Default sequences if no subset
        if not (seqs):
            seqs = self.order_of_blobs
        # Default cov_libs if no subset
        cov_lib_names = cov_libs
        if not (cov_libs):
            cov_lib_names = [covLib for covLib in self.covLibs]

        tax_lib_names = [taxLib for taxLib in sorted(self.hitLibs)]
        lineages = self.lineages
        # headers
        for viewObj in viewObjs:
            if viewObj.name == 'table':
                viewObj.header = self.getTableHeader(taxrule, ranks, hits_flag, cov_lib_names)
            if viewObj.name == 'concoct_cov':
                viewObj.header = self.getConcoctCovHeader(cov_lib_names)
            if viewObj.name == 'cov':
                viewObj.header = self.getCovHeader(cov_lib_names)

        # bodies
        body = []
        for i, seq in enumerate(seqs):
            BtLog.progress(i, 1000, len(seqs))
            blob = self.dict_of_blobs[seq]
            for viewObj in viewObjs:
                if viewObj.name == 'table':
                    viewObj.body.append(self.getTableLine(blob, taxrule, ranks, hits_flag, cov_lib_names, tax_lib_names, lineages))
                if viewObj.name == 'concoct_cov':
                    viewObj.body.append(self.getConcoctCovLine(blob, cov_lib_names))
                if viewObj.name == 'concoct_tax':
                    for rank in ranks:
                        if not rank in viewObj.body:
                            viewObj.body[rank] = []
                        viewObj.body[rank].append(self.getConcoctTaxLine(blob, rank, taxrule))
                if viewObj.name == 'cov':
                    viewObj.body.append(self.getCovLine(blob, cov_lib_names))
        BtLog.progress(len(seqs), 1000, len(seqs))
        for viewObj in viewObjs:
            viewObj.output()

    def getCovHeader(self, cov_lib_names):
        cov_lib_name = cov_lib_names[0]
        header = '## %s\n' % (self.version)
        if isinstance(self.covLibs[cov_lib_name], CovLibObj):
            # CovLibObjs
            header += "## Total Reads = %s\n" % (self.covLibs[cov_lib_name].reads_total)
            header += "## Mapped Reads = %s\n" % (self.covLibs[cov_lib_name].reads_mapped)
            header += "## Unmapped Reads = %s\n" % (self.covLibs[cov_lib_name].reads_total - self.covLibs[cov_lib_name].reads_mapped)
            header += "## Source(s) : %s\n" % (self.covLibs[cov_lib_name].f)
        else:
            # CovLibObjs turned dicts
            header += "## Total Reads = %s\n" % (self.covLibs[cov_lib_name]['reads_total'])
            header += "## Mapped Reads = %s\n" % (self.covLibs[cov_lib_name]['reads_mapped'])
            header += "## Unmapped Reads = %s\n" % (self.covLibs[cov_lib_name]['reads_total'] - self.covLibs[cov_lib_name]['reads_mapped'])
            header += "## Source(s) : %s\n" % (self.covLibs[cov_lib_name]['f'])
        header += "# %s\t%s\t%s\n" % ("contig_id", "read_cov", "base_cov")
        return header

    def getCovLine(self, blob, cov_lib_names):
        if isinstance(blob, BlObj):
            # BlobObj
            return "%s\t%s\t%s\n" % (blob.name, blob.read_cov[cov_lib_names[0]], blob.covs[cov_lib_names[0]])
        else:
            # BlobObj turned dict
            return "%s\t%s\t%s\n" % (blob['name'], blob['read_cov'][cov_lib_names[0]], blob['covs'][cov_lib_names[0]])

    def getConcoctCovHeader(self, cov_lib_names):
        return "contig\t%s\n" % "\t".join(cov_lib_names)

    def getConcoctTaxLine(self, blob, rank, taxrule):
        if taxrule in blob['taxonomy']:
            return "%s,%s\n" % (blob['name'], blob['taxonomy'][taxrule][rank]['tax'])

    def getConcoctCovLine(self, blob, cov_lib_names):
        return "%s\t%s\n" % (blob['name'], "\t".join(map(str, [ blob['covs'][covLib] for covLib in cov_lib_names])))

    def getTableHeader(self, taxrule, ranks, hits_flag, cov_lib_names):
        sep = "\t"
        header = ''
        header += '## %s\n' % (self.version)
        header += "## assembly\t: %s\n" % self.assembly_f
        header += "%s\n" % "\n".join("## coverage\t: " + covLib['name'] + " - " + covLib["f"] for covLib in self.covLibs.values())
        if (self.hitLibs):
            header += "%s\n" % "\n".join("## taxonomy\t: " + hitLib['name'] + " - " + hitLib["f"] for hitLib in self.hitLibs.values())
        else:
            header += "## taxonomy\t: no taxonomy information found\n"
        header += "## nodesDB\t: %s\n" % self.nodesDB_f
        header += "## taxrule\t: %s\n" % taxrule
        header += "##\n"
        header += "# %s" % sep.join(map(str, ["name", "length", "GC", "N"]))
        col = 4
        header += "%s%s" % (sep, sep.join([cov_lib_name for cov_lib_name in cov_lib_names]))
        col += len(cov_lib_names)
        if (len(cov_lib_names)) > 1:
            col += 1
            header += "%s%s" % (sep, "cov_sum")
        for rank in ranks:
            header += "%s%s" % (sep, sep.join([rank + ".t." + str(col + 1), rank + ".s." + str(col + 2), rank + ".c." + str(col + 3)]))
            col += 3
            if hits_flag:
                header += "%s%s" % (sep, rank + ".hits." + str(col + 1))
                col += 1
        return header

    def getTableLine(self, blob, taxrule, ranks, hits_flag, cov_lib_names, tax_lib_names, lineages):
        sep = "\t"
        line = ''
        line += "\n%s" % sep.join(map(str, [ blob['name'], blob['length'], blob['gc'], blob['n_count']  ]))
        line += sep
        line += "%s" % sep.join(map(str, [ blob['covs'][covLib] for covLib in cov_lib_names]))
        if len(cov_lib_names) > 1:
            line += "%s%s" % (sep, sum([ blob['covs'][covLib] for covLib in cov_lib_names]))
        for rank in ranks:
            line += sep
            tax, score, c_index = 'N/A', 'N/A', 'N/A'
            if taxrule in blob['taxonomy']:
                tax = blob['taxonomy'][taxrule][rank]['tax']
                score = blob['taxonomy'][taxrule][rank]['score']
                c_index = blob['taxonomy'][taxrule][rank]['c_index']
            line += "%s" % sep.join(map(str, [tax, score, c_index ]))
            if (hits_flag) and (taxrule in blob['taxonomy']):
                line += sep
                for tax_lib_name in tax_lib_names:
                    if tax_lib_name in blob['hits']:
                        line += "%s=" % tax_lib_name
                        sum_dict = {}
                        for hit in blob['hits'][tax_lib_name]:
                            tax_rank = lineages[hit['taxId']][rank]
                            sum_dict[tax_rank] = sum_dict.get(tax_rank, 0.0) + hit['score']
                        line += "%s" % "|".join([":".join(map(str, [tax_rank, sum_dict[tax_rank]])) for tax_rank in sorted(sum_dict, key=sum_dict.get, reverse=True)])
                    else:
                        line += "%s=no-hit:0.0" % (tax_lib_name)
                    line += ";"
        return line

    def dump(self):
        dump = {'title' : self.title,
                'assembly_f' : self.assembly_f,
                'lineages' : self.lineages,
                'order_of_blobs' : self.order_of_blobs,
                'dict_of_blobs' : {name : blObj.__dict__ for name, blObj in self.dict_of_blobs.items()},
                'length' : self.length,
                'seqs' : self.seqs,
                'n_count' : self.n_count,
                'nodesDB_f' : self.nodesDB_f,
                'covLibs' : {name : covLibObj.__dict__ for name, covLibObj in self.covLibs.items()},
                'hitLibs' : {name : hitLibObj.__dict__ for name, hitLibObj in self.hitLibs.items()},
                'taxrules' : self.taxrules,
                'version' : self.version
                }
        return dump

    def new_dump(self):
        pass

    def load(self, BlobDb_f):
        blobDict = BtIO.parseJson(BlobDb_f)
        for k, v in blobDict.items():
            setattr(self, k, v)
        self.set_of_taxIds = blobDict['lineages'].keys()
        #for k, v in self.__dict__.items():
        #    print k, type(v), v # this seems to work

        #self.title = blobDict['title']
        #self.assembly_f = blobDict['assembly_f']
        #self.nodesDB_f = blobDict['nodesDB_f']
        #self.lineages = blobDict['lineages']
        #self.set_of_taxIds = blobDict['lineages'].keys()
        #self.order_of_blobs = blobDict['order_of_blobs']
        #self.dict_of_blobs = blobDict['dict_of_blobs']
        #self.length = int(blobDict['length'])
        #self.seqs = int(blobDict['seqs'])
        #self.n_count = int(blobDict['n_count'])
        #self.covLibs = blobDict['covLibs']
        #self.hitLibs = blobDict['hitLibs']
        #self.taxrules = blobDict['taxrules']

        # self.title = title
        # self.assembly_f = ''
        # self.dict_of_blobs = {}
        # self.order_of_blobs = []
        # self.set_of_taxIds = set()
        # self.lineages = {}
        # self.length = 0
        # self.seqs = 0
        # self.n_count = 0
        # self.covLibs = {}
        # self.hitLibs = {}
        # self.nodesDB_f = ''
        # self.taxrules = []

    def getPlotData(self, rank, min_length, hide_nohits, taxrule, c_index, catcolour_dict):
        data_dict = {}
        read_cov_dict = {}
        max_cov = 0.0

        if taxrule not in self.taxrules:
            BtLog.error('11', taxrule, self.taxrules)

        cov_lib_dict = self.covLibs
        cov_lib_names_l = self.covLibs.keys() # does not include cov_sum
        if len(cov_lib_names_l) > 1:
            # more than one cov_lib, cov_sum_lib has to be created
            cov_lib_dict['covsum'] = CovLibObj('covsum', 'covsum', 'Sum of cov in %s' % basename(self.title)).__dict__ # ugly
            cov_lib_dict['covsum']['reads_total'] = sum([self.covLibs[x]['reads_total'] for x in self.covLibs])
            cov_lib_dict['covsum']['reads_mapped'] = sum([self.covLibs[x]['reads_mapped'] for x in self.covLibs])
            cov_lib_dict['covsum']['cov_sum'] = sum([self.covLibs[x]['cov_sum'] for x in self.covLibs])
            cov_lib_dict['covsum']['mean_cov'] = cov_lib_dict['covsum']['cov_sum']/self.seqs
        for blob in self.dict_of_blobs.values():
            name, gc, length, group = blob['name'], blob['gc'], blob['length'], ''
            if (catcolour_dict): # annotation with categories specified in catcolour
                group = str(catcolour_dict[name])
            elif (c_index): # annotation with c_index instead of taxonomic group
                group = str(blob['taxonomy'][taxrule][rank]['c_index'])
            else: # annotation with taxonomic group
                group = str(blob['taxonomy'][taxrule][rank]['tax'])
            if not group in data_dict:
                data_dict[group] = {
                                    'name' : [],
                                    'length' : [],
                                    'gc' : [],
                                    'covs' : {covLib : [] for covLib in cov_lib_dict.keys()},           # includes cov_sum if it exists
                                    'reads_mapped' : {covLib : 0 for covLib in cov_lib_dict.keys()},    # includes cov_sum if it exists
                                    'count' : 0,
                                    'count_hidden' : 0,
                                    'count_visible' : 0,
                                    'span': 0,
                                    'span_hidden' : 0,
                                    'span_visible' : 0,
                                    }
            data_dict[group]['count'] = data_dict[group].get('count', 0) + 1
            data_dict[group]['span'] = data_dict[group].get('span', 0) + int(length)
            if ((hide_nohits) and group == 'no-hit') or length < min_length: # hidden
                data_dict[group]['count_hidden'] = data_dict[group].get('count_hidden', 0) + 1
                data_dict[group]['span_hidden'] = data_dict[group].get('span_hidden', 0) + int(length)
            else: # visible
                data_dict[group]['count_visible'] = data_dict[group].get('count_visible', 0) + 1
                data_dict[group]['span_visible'] = data_dict[group].get('span_visible', 0) + int(length)
                data_dict[group]['name'].append(name)
                data_dict[group]['length'].append(length)
                data_dict[group]['gc'].append(gc)
                cov_sum = 0.0
                reads_mapped_sum = 0
                for cov_lib in sorted(cov_lib_names_l):
                    cov = float(blob['covs'][cov_lib])
                    if cov < 0.02:
                        cov = 0.02
                    # increase max_cov
                    if cov > max_cov:
                        max_cov = cov
                    # add cov of blob to group
                    data_dict[group]['covs'][cov_lib].append(cov)
                    cov_sum += cov
                    # add readcov
                    if cov_lib in blob['read_cov']:
                        reads_mapped = blob['read_cov'][cov_lib]
                        data_dict[group]['reads_mapped'][cov_lib] += reads_mapped
                        reads_mapped_sum += reads_mapped
                if len(cov_lib_names_l) > 1:
                    if cov_sum < 0.02 :
                        cov_sum = 0.02
                    data_dict[group]['covs']['covsum'].append(cov_sum)
                    if cov_sum > max_cov:
                        max_cov = cov_sum
                    if (reads_mapped_sum):
                        data_dict[group]['reads_mapped']['covsum'] += reads_mapped_sum

        return data_dict, max_cov, cov_lib_dict

    def addCovLib(self, covLib):
        self.covLibs[covLib.name] = covLib
        for blObj in self.dict_of_blobs.values():
            blObj.addCov(covLib.name, 0.0)

    def parseFasta(self, fasta_f, fasta_type):
        print BtLog.status_d['1'] % ('FASTA', fasta_f)
        self.assembly_f = abspath(fasta_f)
        if (fasta_type):
            # Set up CovLibObj for coverage in assembly header
            self.covLibs[fasta_type] = CovLibObj(fasta_type, fasta_type, fasta_f)

        for name, seq in BtIO.readFasta(fasta_f):
            blObj = BlObj(name, seq)
            if not blObj.name in self.dict_of_blobs:
                self.seqs += 1
                self.length += blObj.length
                self.n_count += blObj.n_count

                if (fasta_type):
                    cov = BtIO.parseCovFromHeader(fasta_type, blObj.name)
                    self.covLibs[fasta_type].cov_sum += cov
                    blObj.addCov(fasta_type, cov)

                self.order_of_blobs.append(blObj.name)
                self.dict_of_blobs[blObj.name] = blObj
            else:
                BtLog.error('5', blObj.name)

        if self.seqs == 0 or self.length == 0:
            BtLog.error('1')

    def parseCoverage(self, **kwargs):
        # arguments
        covLibObjs = kwargs['covLibObjs']
        no_base_cov = kwargs['no_base_cov']

        for covLib in covLibObjs:
            self.addCovLib(covLib)
            print BtLog.status_d['1'] % (covLib.name, covLib.f)
            if covLib.fmt == 'bam' or covLib.fmt == 'sam':
                base_cov_dict = {}
                if covLib.fmt == 'bam':
                    base_cov_dict, covLib.reads_total, covLib.reads_mapped, read_cov_dict = BtIO.parseBam(covLib.f, set(self.dict_of_blobs), no_base_cov)
                else:
                    base_cov_dict, covLib.reads_total, covLib.reads_mapped, read_cov_dict = BtIO.parseSam(covLib.f, set(self.dict_of_blobs), no_base_cov)

                if covLib.reads_total == 0:
                    print BtLog.warn_d['4'] % covLib.f

                for name, base_cov in base_cov_dict.items():
                    cov = base_cov / self.dict_of_blobs[name].agct_count
                    covLib.cov_sum += cov
                    self.dict_of_blobs[name].addCov(covLib.name, cov)
                    self.dict_of_blobs[name].addReadCov(covLib.name, read_cov_dict[name])

            elif covLib.fmt == 'cas':
                cov_dict, covLib.reads_total, covLib.reads_mapped, read_cov_dict = BtIO.parseCas(covLib.f, self.order_of_blobs)
                if covLib.reads_total == 0:
                    print BtLog.warn_d['4'] % covLib.f
                for name, cov in cov_dict.items():
                    covLib.cov_sum += cov
                    self.dict_of_blobs[name].addCov(covLib.name, cov)
                    self.dict_of_blobs[name].addReadCov(covLib.name, read_cov_dict[name])

            elif covLib.fmt == 'cov':
                base_cov_dict, covLib.reads_total, covLib.reads_mapped, covLib.reads_unmapped, read_cov_dict = BtIO.parseCov(covLib.f, set(self.dict_of_blobs))
                #cov_dict = BtIO.readCov(covLib.f, set(self.dict_of_blobs))
                if not len(base_cov_dict) == self.seqs:
                    print BtLog.warn_d['4'] % covLib.f
                for name, cov in base_cov_dict.items():
                    covLib.cov_sum += cov
                    self.dict_of_blobs[name].addCov(covLib.name, cov)
                    if name in read_cov_dict:
                        self.dict_of_blobs[name].addReadCov(covLib.name, read_cov_dict[name])
            else:
                pass
            covLib.mean_cov = covLib.cov_sum/self.seqs
            if covLib.cov_sum == 0.0:
                print BtLog.warn_d['6'] % (covLib.name)
            self.covLibs[covLib.name] = covLib


    def parseHits(self, hitLibs):
        for hitLib in hitLibs:
            self.hitLibs[hitLib.name] = hitLib
            print BtLog.status_d['1'] % (hitLib.name, hitLib.f)
            # only accepts format 'seqID\ttaxID\tscore'
            for hitDict in BtIO.readTax(hitLib.f, set(self.dict_of_blobs)):
                if ";" in hitDict['taxId']:
                    hitDict['taxId'] = hitDict['taxId'].split(";")[0]
                    print BtLog.warn_d['5'] % (hitDict['name'], hitLib)
                self.set_of_taxIds.add(hitDict['taxId'])
                self.dict_of_blobs[hitDict['name']].addHits(hitLib.name, hitDict)

    def computeTaxonomy(self, taxrules, nodesDB, min_bitscore_diff, tax_collision_random):
        print BtLog.status_d['6'] % ",".join(taxrules)
        tree_lists = BtTax.getTreeList(self.set_of_taxIds, nodesDB)
        self.lineages = BtTax.getLineages(tree_lists, nodesDB)
        self.taxrules = taxrules
        i = 0
        for blObj in self.dict_of_blobs.values():
            i += 1
            BtLog.progress(i, 100, self.seqs)
            for taxrule in taxrules:
                if (blObj.hits):
                    blObj.taxonomy[taxrule] = BtTax.taxRule(taxrule, blObj.hits, self.lineages, min_bitscore_diff, tax_collision_random)
                else:
                    blObj.taxonomy[taxrule] = BtTax.noHit()

    def getBlobs(self):
        for blObj in [self.dict_of_blobs[key] for key in self.order_of_blobs]:
            yield blObj

class BlObj():
    def __init__(self, name, seq):
        self.name = name
        self.length = len(seq)
        self.n_count = seq.count('N')
        self.agct_count = self.length - self.n_count
        self.gc = round(self.calculateGC(seq), 4)
        self.covs = {}
        self.read_cov = {}
        self.hits = {}
        self.taxonomy = {}

    def calculateGC(self, seq):
        return float((seq.count('G') + seq.count('C') ) / self.agct_count \
                     if self.agct_count > 0 else 0.0)

    def addCov(self, lib_name, cov):
        self.covs[lib_name] = cov

    def addReadCov(self, lib_name, read_cov):
        self.read_cov[lib_name] = read_cov

    def addHits(self, hitLibName, hitDict):
        if not hitLibName in self.hits:
            self.hits[hitLibName] = []
        self.hits[hitLibName].append(hitDict)

class CovLibObj():
    def __init__(self, name, fmt, f):
        self.name = name
        self.fmt = fmt
        self.f = abspath(f) if isfile(f) else f # pass file/string/''
        self.cov_sum = 0.0
        self.reads_total = 0
        self.reads_mapped = 0
        self.reads_unmapped = 0
        self.mean_cov = 0.0

class HitLibObj():
    def __init__(self, name, fmt, f):
        self.name = name
        self.fmt = fmt
        self.f = abspath(f) if isfile(f) else f # pass file/string/''

class ViewObj():
    def __init__(self, name, out_f, suffix, header, body):
        self.name = name
        self.out_f = out_f
        self.suffix = suffix
        self.header = header
        self.body = body

    def output(self):
        if isinstance(self.body, dict):
            for category in self.body:
                out_f = "%s.%s.%s" % (self.out_f, category, self.suffix)
                print BtLog.status_d['13'] % (out_f)
                with open(out_f, "w") as fh:
                    fh.write(self.header + "".join(self.body[category]))
        elif isinstance(self.body, list):
            out_f = "%s.%s" % (self.out_f, self.suffix)
            print BtLog.status_d['13'] % (out_f)
            with open(out_f, "w") as fh:
                fh.write(self.header + "".join(self.body))
        else:
            sys.exit("[ERROR] - 001")

if __name__ == '__main__':
    pass
