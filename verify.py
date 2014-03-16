#!/usr/bin/env python

"""
Copyright (c) 2014 Ranger Harke
See LICENSE file for details
"""

import os, hashlib, mmap, sys

DATABASE_FILE = 'checksums'
VERIFY_DIRECTORY = 'data'
VERIFY_EXISTING = True
ADD_NEW = True
REMOVE_DELETED = False
UPDATE_CHANGED = False
VERBOSE = True

def md5sum(filename):
    with open(filename, 'r+b') as f:
        s = os.fstat(f.fileno()).st_size
        hasher = hashlib.md5()
        hasher.update(mmap.mmap(f.fileno(), s))
        return hasher.hexdigest()

def log(message):
    if VERBOSE:
        sys.stderr.write(message)

database = {}
if os.path.exists(DATABASE_FILE):
    with open(DATABASE_FILE, 'r+a') as sumfile:
        for l in sumfile:
            entry = l.rstrip('\r\n')
            checksum = entry[:32]
            filepath = entry[34:]
            database[filepath] = [checksum, False]

failed = 0
verified = 0
added = 0
removed = 0

for dirpath, dirnames, filenames in os.walk(VERIFY_DIRECTORY):
    for filename in filenames:
        filepath =  os.path.join(dirpath, filename)
        if filepath in database:
            log('Existing file %s... ' % (filepath,))
            if VERIFY_EXISTING:
                checksum = md5sum(filepath)
                if checksum != database[filepath][0]:
                    if UPDATE_CHANGED:
                        log('updated\n')
                        database[filepath][0] = checksum
                    else:
                        log('failed\n')
                    failed += 1
                else:
                    log('verified\n')
                    verified += 1
            else:
                log('skipped\n')
            database[filepath][1] = True
        else:
            log('New file %s... ' % (filepath,))
            if ADD_NEW:
                checksum = md5sum(filepath)
                log('computed\n')
                database[filepath] = [checksum, True]
            else:
                log('skipped\n')
            added += 1

todelete = []  # do not delete immediately because we are iterating
for filepath in database:
    if not database[filepath][1]:
        log('Deleted file %s... ' % (filepath,))
        if REMOVE_DELETED:
            todelete.append(filepath)
            log('removed\n')
        else:
            log('skipped\n')
        removed += 1

for filepath in todelete:
    del database[filepath]

fail_update = ((failed > 0) and UPDATE_CHANGED)
add_update = ((added > 0) and ADD_NEW)
del_update = ((removed > 0) and REMOVE_DELETED)

if fail_update or add_update or del_update:
    with open(DATABASE_FILE, 'w+a') as sumfile:
        for filepath in database:
            sumfile.write('%s  %s\n' % (database[filepath][0], filepath))

log('\nSummary:\n')
log('    %d verified\n' % (verified,))
log('    %d failed%s\n' % (failed, ' (database updated)' if fail_update else ''))
log('    %d new files%s\n' % (added, ' (database updated)' if add_update else ''))
log('    %d deleted files%s\n' % (removed, ' (database updated)' if del_update else ''))
