#!/usr/bin/env python

"""
Copyright (c) 2014 Ranger Harke
See LICENSE file for details
"""

import os, hashlib, mmap, sys, argparse, fnmatch

def md5sum(filename):
    with open(filename, 'rb') as f:
        s = os.fstat(f.fileno()).st_size
        hasher = hashlib.md5()
        if s > 0:
            hasher.update(mmap.mmap(f.fileno(), s, prot=mmap.PROT_READ))
        return hasher.hexdigest()

def parse_args(args=None):
    if args is None:
        args = sys.argv

    parser = argparse.ArgumentParser(description='Verify a tree of files')
    parser.add_argument('verify_directory', metavar='VERIFY_DIRECTORY', type=str,
                        help='directory containing the files to verify')
    parser.add_argument('--db-file', '-d', metavar='DATABASE_FILE', type=str, dest='database_file',
                        help='file from/in which to read/store the checksum database')
    parser.add_argument('--ignorelist-file', metavar='IGNORELIST_FILE', type=str, dest='ignorelist_file',
                        help='file containing a list of shell-style patterns to ignore')
    parser.add_argument('--no-verify-existing', dest='verify_existing', action='store_false',
                        help='do not verify existing files against the database')
    parser.add_argument('--no-add-new', dest='add_new', action='store_false',
                        help='do not add new files to the database')
    parser.add_argument('--remove-deleted', dest='remove_deleted', action='store_true',
                        help='remove deleted files from the database')
    parser.add_argument('--update-changed', dest='update_changed', action='store_true',
                        help='update the database with the new checksum for files that do not pass verification')
    parser.add_argument('--verbose', '-v', dest='verbose', action='store_true',
                        help='display status messages for all operations instead of just exceptional conditions')

    parser.set_defaults(database_file='checksums', ignorelist_file=None, verify_existing=True,
                        add_new=True, remove_deleted=False, update_changed=False, verbose=False)

    return parser.parse_args()

def main():
    Verifier(parse_args()).run()

class Verifier(object):
    def __init__(self, args):
        self.args = args
        self.database = {}
        self.ignorelist = []

        self.failed = 0
        self.verified = 0
        self.added = 0
        self.removed = 0

    def read_database(self):
        if os.path.exists(self.args.database_file):
            with open(self.args.database_file, 'rt') as sumfile:
                for l in sumfile:
                    entry = l.rstrip('\r\n')
                    if len(entry) > 0:
                        checksum = entry[:32]
                        filepath = entry[34:]
                        self.database[filepath] = [checksum, False]

    def write_database(self):
        with open(self.args.database_file, 'wt') as sumfile:
            for filepath in self.database:
                sumfile.write('%s  %s\n' % (self.database[filepath][0], filepath))

    def read_ignorelist(self):
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

    def check_local_file(self, filepath):
        if filepath in self.database:
            self.vlog('Existing file %s... ' % (filepath,))
            if self.args.verify_existing:
                checksum = md5sum(filepath)
                if checksum != self.database[filepath][0]:
                    if self.args.update_changed:
                        self.vlog('updated\n')
                        self.nvlog('Existing file %s updated\n' % (filepath,))
                        self.database[filepath][0] = checksum
                    else:
                        self.vlog('failed\n')
                        self.nvlog('Existing file %s failed\n' % (filepath,))
                    self.failed += 1
                else:
                    self.vlog('verified\n')
                    self.verified += 1
            else:
                self.vlog('skipped\n')
            self.database[filepath][1] = True
        else:
            self.vlog('New file %s... ' % (filepath,))
            if self.args.add_new:
                checksum = md5sum(filepath)
                self.vlog('added\n')
                self.database[filepath] = [checksum, True]
            else:
                self.vlog('skipped\n')
            self.nvlog('New file %s added\n' % (filepath,))
            self.added += 1

    def check_database_file(self, filepath):
        if not self.database[filepath][1]:
            self.vlog('Deleted file %s... ' % (filepath,))
            if self.args.remove_deleted:
                del self.database[filepath]
                self.vlog('removed\n')
            else:
                self.vlog('skipped\n')
            self.nvlog('Deleted file %s removed\n' % (filepath,))
            self.removed += 1

    def run(self):
        self.read_database()
        self.read_ignorelist()

        for dirpath, dirnames, filenames in os.walk(self.args.verify_directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if not self.match_ignorelist(filepath):
                    self.check_local_file(filepath)

        # NB: iterate over keys so we can delete while iterating
        for filepath in self.database.keys():
            if not self.match_ignorelist(filepath):
                self.check_database_file(filepath)

        fail_update = (self.failed > 0) and self.args.update_changed
        add_update = (self.added > 0) and self.args.add_new
        del_update = (self.removed > 0) and self.args.remove_deleted

        if fail_update or add_update or del_update:
            self.write_database()

        self.log('\nSummary:\n')
        self.log('    %d verified\n' % (self.verified,))
        self.log('    %d failed%s\n' % (self.failed, ' (database updated)' if fail_update else ''))
        self.log('    %d new files%s\n' % (self.added, ' (database updated)' if add_update else ''))
        self.log('    %d deleted files%s\n' % (self.removed, ' (database updated)' if del_update else ''))

    def vlog(self, message):
        if self.args.verbose:
            sys.stderr.write(message)

    def nvlog(self, message):
        if not self.args.verbose:
            sys.stderr.write(message)

    def log(self, message):
        sys.stderr.write(message)

if __name__ == "__main__":
    main()
