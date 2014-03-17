verify
======

**Verify** is a quick utility to maintain a database of checksums for a tree of files.

The idea is to keep track of the checksums of a tree of files to help protect against bit rot. Some filesystems (ZFS, etc.) provide this themselves; most do not. Some people falsely believe that RAID protects against bit rot; in fact it does not.

My personal use case is to keep checksums for my large collection of media files so that I can tell if/when a file has sustained damage and restore from backup. Similarly, I use it to make sure my backups are intact.

## Usage

```
usage: verify.py [-h] [--db-file DATABASE_FILE]
                 [--ignorelist-file IGNORELIST_FILE] [--no-verify-existing]
                 [--no-add-new] [--remove-deleted] [--update-changed]
                 [--clean-ignored] [--verbose]
                 VERIFY_DIRECTORY

Verify a tree of files

positional arguments:
  VERIFY_DIRECTORY      directory containing the files to verify

optional arguments:
  -h, --help            show this help message and exit
  --db-file DATABASE_FILE, -d DATABASE_FILE
                        file from/in which to read/store the checksum database
  --ignorelist-file IGNORELIST_FILE
                        file containing a list of shell-style patterns to
                        ignore
  --no-verify-existing  do not verify existing files against the database
  --no-add-new          do not add new files to the database
  --remove-deleted      remove deleted files from the database
  --update-changed      update the database with the new checksum for files
                        that do not pass verification
  --clean-ignored       remove files from the database that match an ignore
                        pattern (to clean up a crufty database)
  --verbose, -v         display status messages for all operations instead of
                        just exceptional conditions
```

By default, **Verify** runs in a fairly non-destructive fashion, only adding new files to the database and reporting on files that have changed or been removed.

If files have been changed or removed, the idea is that you would manually validate the changes, and then re-run with `--remove-deleted` or `--update-changed` to incorporate the changes into the database if they are acceptable. Otherwise,  you could take corrective action (e.g. restore from backup).

The database is stored in a simple format compatible with md5sum. Each line is the lowercase MD5 hex digest (32 characters), followed by two spaces, followed by the file path. In a pinch, you can use `md5sum -c` to check files against the database.

## Issues / to-do

* There is no way to run against a subset of files. If a file has been updated, a re-run with `--update-changed` will need to rescan all files (which is actually a race, since perhaps something else has gone wrong in the meantime).
* The ignorelist does not support globstar syntax, which makes it difficult to precisely ignore files recursively. Mainly this is because Python does not natively support this syntax. It could be hacked in, but I haven't run into a pressing need for it yet. You can mostly hack around it (e.g. ignore both `.DS_Store` and `*/.DS_Store`).
