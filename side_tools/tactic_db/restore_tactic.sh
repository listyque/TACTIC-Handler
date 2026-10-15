#!/bin/sh
# Restore a backup made by backup_tactic.sh. Stop TACTIC first.
# Usage: sh restore_tactic.sh ARCHIVE [--replace]

set -eu
umask 077

if [ "$#" -lt 1 ] || [ "$#" -gt 2 ] || { [ "$#" -eq 2 ] && [ "$2" != --replace ]; }; then
    printf 'Usage: sh restore_tactic.sh ARCHIVE [--replace]\n' >&2
    exit 2
fi
archive=$1
replace=${2:-}
[ -f "$archive" ] || { printf 'Archive not found: %s\n' "$archive" >&2; exit 1; }

archive_dir=$(dirname "$archive")
work_dir=$(mktemp -d "$archive_dir/.tactic-restore.XXXXXXXX")
trap 'rm -f "$work_dir/members" "$work_dir/details" "$work_dir/databases.txt" "$work_dir/skipped-projects.txt" "$work_dir/globals.sql" "$work_dir"/db/*.dump; rmdir "$work_dir/db" "$work_dir" 2>/dev/null || :' 0
trap 'exit 130' 2
trap 'exit 143' 15

tar -tzf "$archive" > "$work_dir/members"
tar -tvzf "$archive" > "$work_dir/details"
while IFS= read -r detail; do
    case "$detail" in -*) ;; d*) ;; *) printf 'Unsafe archive member type\n' >&2; exit 1 ;; esac
done < "$work_dir/details"
while IFS= read -r member; do
    case "$member" in
        globals.sql|databases.txt|skipped-projects.txt|db/) ;;
        db/*.dump)
            database=${member#db/}
            database=${database%.dump}
            case "$database" in ''|*[!A-Za-z0-9_-]*) printf 'Unsafe archive member: %s\n' "$member" >&2; exit 1 ;; esac
            ;;
        *) printf 'Unsafe archive member: %s\n' "$member" >&2; exit 1 ;;
    esac
done < "$work_dir/members"
[ -z "$(sort "$work_dir/members" | uniq -d)" ] || { printf 'Duplicate archive members\n' >&2; exit 1; }
grep -Fxq globals.sql "$work_dir/members"
grep -Fxq databases.txt "$work_dir/members"
grep -Fxq skipped-projects.txt "$work_dir/members"
tar -xzf "$archive" -C "$work_dir" --no-same-owner --no-same-permissions
[ "$(sed -n '1p' "$work_dir/databases.txt")" = sthpw ] || { printf 'Archive has no sthpw database\n' >&2; exit 1; }
[ -z "$(sort "$work_dir/databases.txt" | uniq -d)" ] || { printf 'Duplicate database names\n' >&2; exit 1; }

peer=0
if [ "$(id -u)" -eq 0 ] && [ -z "${PGUSER:-}" ] && [ -z "${PGHOST:-}" ] &&
    [ -z "${PGHOSTADDR:-}" ] && [ -z "${PGSERVICE:-}" ]; then
    peer=1
fi
pg() {
    if [ "$peer" -eq 1 ]; then
        (cd / && runuser -u postgres -- "$@")
    else
        "$@"
    fi
}

# Check all targets before changing any database. Existing databases require
# an explicit flag; active connections must be stopped by the operator.
while IFS= read -r database; do
    case "$database" in
        ''|postgres|template0|template1|*[!A-Za-z0-9_-]*)
            printf 'Invalid database name: %s\n' "$database" >&2
            exit 1
            ;;
    esac
    [ -f "$work_dir/db/$database.dump" ] || { printf 'Missing dump: %s\n' "$database" >&2; exit 1; }
    dump_database=$(pg_restore -l "$work_dir/db/$database.dump" | sed -n 's/^;[[:space:]]*dbname: //p')
    [ "$dump_database" = "$database" ] || { printf 'Dump name does not match %s: %s\n' "$database" "$dump_database" >&2; exit 1; }
    exists=$(pg psql -X -A -t -w -v ON_ERROR_STOP=1 -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$database'")
    case "$exists" in ''|1) ;; *) printf 'Cannot determine whether %s exists\n' "$database" >&2; exit 1 ;; esac
    if [ "$exists" = 1 ] && [ "$replace" != --replace ]; then
        printf '%s exists. Re-run with --replace to drop and restore it.\n' "$database" >&2
        exit 1
    fi
    active=$(pg psql -X -A -t -w -v ON_ERROR_STOP=1 -d postgres -c "SELECT count(*) FROM pg_stat_activity WHERE datname = '$database'")
    case "$active" in ''|*[!0-9]*) printf 'Cannot count connections to %s\n' "$database" >&2; exit 1 ;; esac
    if [ "$active" -gt 0 ]; then
        printf '%s has %s active connections. Stop TACTIC first.\n' "$database" "$active" >&2
        exit 1
    fi
done < "$work_dir/databases.txt"

# The destination server's roles are kept. globals.sql is in the archive for
# disaster recovery, but replaying it here would conflict with existing roles.
while IFS= read -r database; do
    printf 'Restoring: %s\n' "$database"
    exists=$(pg psql -X -A -t -w -v ON_ERROR_STOP=1 -d postgres -c "SELECT 1 FROM pg_database WHERE datname = '$database'")
    case "$exists" in ''|1) ;; *) printf 'Cannot determine whether %s exists\n' "$database" >&2; exit 1 ;; esac
    if [ "$exists" = 1 ]; then
        pg pg_restore -w -e --create --clean --if-exists -d postgres < "$work_dir/db/$database.dump"
    else
        pg pg_restore -w -e --create -d postgres < "$work_dir/db/$database.dump"
    fi
done < "$work_dir/databases.txt"
printf 'Restore completed: %s\n' "$archive"
