#!/usr/bin/env python

"""
Copyright (c) 2014-2015 Ranger Harke
See LICENSE file for details
"""

import os, hashlib, mmap, sys, fnmatch

class VerifierBase(object):
    def __init__(self, args):
        self.args = args
        self.ignorelist = []

    @staticmethod
    def read_database(database_file, database_dict):
        if os.path.exists(database_file):
            with open(database_file, 'rt') as sumfile:
                for l in sumfile:
                    entry = l.rstrip('\r\n')
                    if len(entry) > 0:
                        checksum = entry[:32]
                        filepath = entry[34:]
                        database_dict[filepath] = [checksum, False]

    @staticmethod
    def write_database(database_file, database_dict):
        with open(database_file, 'wt') as sumfile:
            for filepath in database_dict:
                sumfile.write('%s  %s\n' % (database_dict[filepath][0], filepath))

    def read_ignorelist(self):
        if self.args.ignorelist_file is not None:
            with open(self.args.ignorelist_file, 'rt') as ignorelistfile:
                for l in ignorelistfile:
                    entry = l.rstrip('\r\n')
                    if len(entry) > 0:
                        self.ignorelist.append(entry)

    def match_ignorelist(self, filepath):
        for entry in self.ignorelist:
            if fnmatch.fnmatch(filepath, entry):
                return True
        return False

    def vlog(self, message):
        if self.args.verbose:
            sys.stderr.write(message)
            sys.stderr.flush()

    def nvlog(self, message):
        if not self.args.verbose:
            sys.stderr.write(message)
            sys.stderr.flush()

    def log(self, message):
        sys.stderr.write(message)
        sys.stderr.flush()

    @staticmethod
    def md5sum(filename):
        with open(filename, 'rb') as f:
            s = os.fstat(f.fileno()).st_size
            hasher = hashlib.md5()
            if s > 0:
                hasher.update(mmap.mmap(f.fileno(), s, prot=mmap.PROT_READ))
            return hasher.hexdigest()
