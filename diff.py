#!/usr/bin/env python

"""
Copyright (c) 2014-2015 Ranger Harke
See LICENSE file for details
"""

import sys, argparse, io, os, tarfile, base

def parse_args(args=None):
    if args is None:
        args = sys.argv

    parser = argparse.ArgumentParser(description='Diff a local tree against a remote one and generate a patch file')
    parser.add_argument('local_db_file', metavar='LOCAL_DATABASE_FILE', type=str,
                        help='file from which to read the local checksum database')
    parser.add_argument('remote_db_file', metavar='REMOTE_DATABASE_FILE', type=str,
                        help='file from which to read the remote checksum database')
    parser.add_argument('local_directory', metavar='LOCAL_DIRECTORY', type=str,
                        help='directory corresponding to the local database file')
    parser.add_argument('patch_file', metavar='PATCH_FILE', type=str,
                        help='file in which to store the resulting patch')
    parser.add_argument('--ignorelist-file', metavar='IGNORELIST_FILE', type=str, dest='ignorelist_file',
                        help='file containing a list of shell-style patterns to ignore')
    parser.add_argument('--no-diff-new', dest='diff_new', action='store_false',
                        help='do not generate diffs to add new files to the remote')
    parser.add_argument('--diff-changed', dest='diff_changed', action='store_true',
                        help='generate diffs to update changed files on the remote')
    parser.add_argument('--diff-deleted', dest='diff_deleted', action='store_true',
                        help='generate diffs to remove deleted files from the remote')
    parser.add_argument('--verbose', '-v', dest='verbose', action='store_true',
                        help='display status messages for all operations instead of just exceptional conditions')

    parser.set_defaults(ignorelist_file=None, diff_new=True, diff_changed=False,
                        diff_deleted=False, clean_ignored=False, verbose=False)

    return parser.parse_args()

def main():
    PatchGenerator(parse_args()).run()

class PatchGenerator(base.VerifierBase):
    def __init__(self, args):
        super(PatchGenerator, self).__init__(args)

        self.local_database = {}
        self.remote_database = {}

        self.new = 0
        self.changed = 0
        self.deleted = 0

        self.read_database(self.args.local_db_file, self.local_database)
        self.read_database(self.args.remote_db_file, self.remote_database)
        self.read_ignorelist()

    def check_local_file(self, filepath):
        local_entry = self.local_database[filepath]
        remote_entry = self.remote_database.get(filepath)
        if not remote_entry is None:
            self.vlog('Existing file %s... ' % (filepath,))
            if self.args.diff_changed:
                if local_entry[0] != remote_entry[0]:
                    meta = ('replace\n' + filepath).encode('utf-8')
                    with io.BytesIO(meta) as metafile:
                        tarinfo = tarfile.TarInfo(str(self.taridx) + 'meta')
                        tarinfo.size = len(metafile.getvalue())
                        self.tarfile.addfile(tarinfo, metafile)
                    self.tarfile.add(os.path.join(self.args.local_directory, filepath), arcname=str(self.taridx) + 'data')
                    self.taridx += 1
                    self.vlog('modified\n')
                    self.nvlog('Existing file %s changed\n' % (filepath,))
                    self.changed += 1
                else:
                    self.vlog('unchanged\n')
            else:
                self.vlog('skipped\n')
            remote_entry[1] = True
        else:
            self.vlog('New file %s... ' % (filepath,))
            if self.args.diff_new:
                meta = ('add\n' + filepath).encode('utf-8')
                with io.BytesIO(meta) as metafile:
                    tarinfo = tarfile.TarInfo(str(self.taridx) + 'meta')
                    tarinfo.size = len(metafile.getvalue())
                    self.tarfile.addfile(tarinfo, metafile)
                self.tarfile.add(os.path.join(self.args.local_directory, filepath), arcname=str(self.taridx) + 'data')
                self.taridx += 1
                self.vlog('added\n')
                self.nvlog('New file %s added\n' % (filepath,))
                self.new += 1
            else:
                self.vlog('skipped\n')

    def check_remote_file(self, filepath):
        remote_entry = self.remote_database[filepath]
        if not remote_entry[1]:
            self.vlog('Deleted file %s... ' % (filepath,))
            if self.args.diff_deleted:
                meta = ('delete\n' + filepath).encode('utf-8')
                with io.BytesIO(meta) as metafile:
                    tarinfo = tarfile.TarInfo(str(self.taridx) + 'meta')
                    tarinfo.size = len(metafile.getvalue())
                    self.tarfile.addfile(tarinfo, metafile)
                self.taridx += 1
                self.vlog('removed\n')
                self.nvlog('Deleted file %s removed\n' % (filepath,))
                self.deleted += 1
            else:
                self.vlog('skipped\n')

    def run(self):
        self.tarfile = tarfile.open(self.args.patch_file, 'w|gz')
        self.taridx = 0

        try:
            for filepath in self.local_database:
                if not self.match_ignorelist(filepath):
                    self.check_local_file(filepath)

            for filepath in self.remote_database:
                if not self.match_ignorelist(filepath):
                    self.check_remote_file(filepath)
        finally:
            self.tarfile.close()

        self.log('\nSummary:\n')
        if self.args.diff_new:
            self.log('    %d new files will be added\n' % (self.new,))
        if self.args.diff_changed:
            self.log('    %d existing files will be updated\n' % (self.changed,))
        if self.args.diff_deleted:
            self.log('    %d deleted files will be removed\n' % (self.deleted,))

if __name__ == "__main__":
    main()
