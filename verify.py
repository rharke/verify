#!/usr/bin/env python

"""
Copyright (c) 2014 Ranger Harke
See LICENSE file for details
"""

import os, hashlib, mmap, sys, argparse

def md5sum(filename):
    with open(filename, 'r+b') as f:
        s = os.fstat(f.fileno()).st_size
        hasher = hashlib.md5()
        if s > 0:
            hasher.update(mmap.mmap(f.fileno(), s))
        return hasher.hexdigest()

def main():
    parser = argparse.ArgumentParser(description='Verify a tree of files')
    parser.add_argument('verify_directory', metavar='VERIFY_DIRECTORY', type=str,
                        help='directory containing the files to verify')
    parser.add_argument('--db-file', '-d', metavar='DATABASE_FILE', type=str, dest='database_file',
                        help='file from/in which to read/store the checksum database')
    parser.add_argument('--no-verify-existing', dest='verify_existing', action='store_false',
                        help='do not verify existing files against the database')
    parser.add_argument('--no-add-new', dest='add_new', action='store_false',
                        help='do not add new files to the database')
    parser.add_argument('--remove-deleted', dest='remove_deleted', action='store_true',
                        help='remove deleted files from the database')
    parser.add_argument('--update-changed', dest='update_changed', action='store_true',
                        help='update the database with the new checksum for files that do not pass verification')
    #parser.add_argument('--verbose', '-v', dest='verbose', action='store_true',
    #                    help='display status messages for all operations instead of just exceptional conditions')
    parser.add_argument('--no-verbose', dest='verbose', action='store_false',
                        help='display status only for exceptional conditions')

    parser.set_defaults(database_file='checksums', verify_existing=True, add_new=True,
                        remove_deleted=False, update_changed=False, verbose=True)

    args = parser.parse_args()

    Verifier(args).run()

class Verifier(object):
    def __init__(self, args):
        self.args = args
        self.database = {}

    def read_database(self):
        if os.path.exists(self.args.database_file):
            with open(self.args.database_file, 'r+a') as sumfile:
                for l in sumfile:
                    entry = l.rstrip('\r\n')
                    checksum = entry[:32]
                    filepath = entry[34:]
                    self.database[filepath] = [checksum, False]

    def write_database(self):
        with open(self.args.database_file, 'w+a') as sumfile:
            for filepath in self.database:
                sumfile.write('%s  %s\n' % (self.database[filepath][0], filepath))

    def run(self):
        self.read_database()
        
        failed = 0
        verified = 0
        added = 0
        removed = 0

        for dirpath, dirnames, filenames in os.walk(self.args.verify_directory):
            for filename in filenames:
                filepath =  os.path.join(dirpath, filename)
                if filepath in self.database:
                    self.log('Existing file %s... ' % (filepath,))
                    if self.args.verify_existing:
                        checksum = md5sum(filepath)
                        if checksum != self.database[filepath][0]:
                            if self.args.update_changed:
                                self.log('updated\n')
                                self.database[filepath][0] = checksum
                            else:
                                self.log('failed\n')
                            failed += 1
                        else:
                            self.log('verified\n')
                            verified += 1
                    else:
                        self.log('skipped\n')
                    self.database[filepath][1] = True
                else:
                    self.log('New file %s... ' % (filepath,))
                    if self.args.add_new:
                        checksum = md5sum(filepath)
                        self.log('computed\n')
                        self.database[filepath] = [checksum, True]
                    else:
                        self.log('skipped\n')
                    added += 1

        todelete = []  # do not delete immediately because we are iterating
        for filepath in self.database:
            if not self.database[filepath][1]:
                self.log('Deleted file %s... ' % (filepath,))
                if self.args.remove_deleted:
                    todelete.append(filepath)
                    self.log('removed\n')
                else:
                    self.log('skipped\n')
                removed += 1

        for filepath in todelete:
            del self.database[filepath]

        fail_update = ((failed > 0) and self.args.update_changed)
        add_update = ((added > 0) and self.args.add_new)
        del_update = ((removed > 0) and self.args.remove_deleted)

        if fail_update or add_update or del_update:
            self.write_database()

        self.log('\nSummary:\n')
        self.log('    %d verified\n' % (verified,))
        self.log('    %d failed%s\n' % (failed, ' (database updated)' if fail_update else ''))
        self.log('    %d new files%s\n' % (added, ' (database updated)' if add_update else ''))
        self.log('    %d deleted files%s\n' % (removed, ' (database updated)' if del_update else ''))

    def log(self, message):
        if self.args.verbose:
            sys.stderr.write(message)

if __name__ == "__main__":
    main()
