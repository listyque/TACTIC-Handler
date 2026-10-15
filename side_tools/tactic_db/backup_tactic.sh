#!/bin/sh
# Back up sthpw and the project databases registered in sthpw.project.
# Usage: sh backup_tactic.sh [backup_directory]

set -eu
umask 077

backup_dir=${1:-"$PWD/tactic_backups"}
mkdir -p "$backup_dir"
work_dir=$(mktemp -d "$backup_dir/.tactic-backup.XXXXXXXX")
trap 'rm -f "$work_dir/globals.sql" "$work_dir/databases.txt" "$work_dir/skipped-projects.txt" "$work_dir/projects.txt" "$work_dir/available.txt" "$work_dir/backup.tar.gz" "$work_dir"/db/*.dump; rmdir "$work_dir/db" "$work_dir"' 0
trap 'exit 130' 2
trap 'exit 143' 15
mkdir "$work_dir/db"

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

# Redirection is opened by the invoking user, so root can write under /root
# while PostgreSQL commands authenticate as the postgres OS user.
pg pg_dumpall --globals-only --no-password > "$work_dir/globals.sql"
pg psql -X -A -t -w -v ON_ERROR_STOP=1 -d sthpw \
    -c "SELECT DISTINCT code FROM project WHERE code IS NOT NULL AND code <> '' AND code <> 'sthpw' ORDER BY code" \
    > "$work_dir/projects.txt"
pg psql -X -A -t -w -v ON_ERROR_STOP=1 -d postgres \
    -c "SELECT datname FROM pg_database WHERE NOT datistemplate" \
    > "$work_dir/available.txt"

printf 'sthpw\n' > "$work_dir/databases.txt"
: > "$work_dir/skipped-projects.txt"
while IFS= read -r database; do
    case "$database" in
        ''|postgres|template0|template1|*[!A-Za-z0-9_-]*)
            printf 'Invalid TACTIC project code: %s\n' "$database" >&2
            exit 1
            ;;
    esac
    if grep -Fx -e "$database" "$work_dir/available.txt" > /dev/null; then
        printf '%s\n' "$database" >> "$work_dir/databases.txt"
    else
        printf '%s\n' "$database" >> "$work_dir/skipped-projects.txt"
        printf 'Skipping project without a local database: %s\n' "$database" >&2
    fi
done < "$work_dir/projects.txt"

while IFS= read -r database; do
    printf 'Backing up: %s\n' "$database"
    pg pg_dump -Fc -w -d "$database" > "$work_dir/db/$database.dump"
done < "$work_dir/databases.txt"

tar -czf "$work_dir/backup.tar.gz" -C "$work_dir" globals.sql databases.txt skipped-projects.txt db

archive="$backup_dir/tactic_$(date +%Y-%m-%d_%H-%M-%S)_$$.tar.gz"
ln "$work_dir/backup.tar.gz" "$archive"
printf 'Backup created: %s\n' "$archive"
if [ -s "$work_dir/skipped-projects.txt" ]; then
    printf 'Review skipped-projects.txt in the archive before treating it as complete.\n' >&2
fi
