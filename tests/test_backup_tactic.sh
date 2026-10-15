#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_dir=$(mktemp -d)
trap 'rm -f "$test_dir/bin/"* "$test_dir/runuser.called" "$test_dir/restore.log" "$test_dir/with space"/*.tar.gz; rmdir "$test_dir/bin" "$test_dir/with space" "$test_dir/failed" "$test_dir"' 0
mkdir "$test_dir/bin" "$test_dir/with space" "$test_dir/failed"

cat > "$test_dir/bin/pg_dumpall" <<'EOF'
#!/bin/sh
printf 'CREATE ROLE tactic;\n'
EOF
cat > "$test_dir/bin/psql" <<'EOF'
#!/bin/sh
while [ "$#" -gt 0 ]; do
    if [ "$1" = -c ]; then shift; query=$1; fi
    shift
done
case "$query" in
    *'SELECT DISTINCT code FROM project'*) printf 'admin\ncomplex\nniki_friends\n' ;;
    *'SELECT datname FROM pg_database'*) printf 'postgres\nsthpw\nniki_friends\n' ;;
    *'FROM pg_database'*) printf '1\n' ;;
    *'FROM pg_stat_activity'*) printf '%s\n' "${FAKE_ACTIVE:-0}" ;;
    *) exit 1 ;;
esac
EOF
cat > "$test_dir/bin/pg_dump" <<'EOF'
#!/bin/sh
while [ "$#" -gt 0 ]; do
    if [ "$1" = -d ]; then shift; database=$1; fi
    shift
done
printf 'DB:%s\n' "$database"
[ "${FAKE_DUMP_FAIL:-0}" != 1 ] || [ "$database" != niki_friends ]
EOF
cat > "$test_dir/bin/pg_restore" <<'EOF'
#!/bin/sh
if [ "$1" = -l ]; then
    sed -n 's/^DB:/;     dbname: /p' "$2"
else
    IFS= read -r database
    printf '%s\n' "${database#DB:}" >> "$FAKE_RESTORE_LOG"
fi
EOF
cat > "$test_dir/bin/id" <<'EOF'
#!/bin/sh
[ "$1" = -u ] && printf '0\n'
EOF
cat > "$test_dir/bin/runuser" <<'EOF'
#!/bin/sh
[ "$1" = -u ] && [ "$2" = postgres ] && [ "$3" = -- ]
pwd > "$FAKE_RUNUSER_MARKER"
shift 3
exec "$@"
EOF
chmod +x "$test_dir/bin/"*

PATH="$test_dir/bin:$PATH" FAKE_RUNUSER_MARKER="$test_dir/runuser.called" PGUSER= PGHOST= PGHOSTADDR= PGSERVICE= sh "$script_dir/side_tools/tactic_db/backup_tactic.sh" "$test_dir/with space"
[ "$(sed -n '1p' "$test_dir/runuser.called")" = / ]
set -- "$test_dir/with space"/tactic_*.tar.gz
[ -f "$1" ]
archive=$1
[ "$(tar -xOzf "$archive" databases.txt)" = "$(printf 'sthpw\nniki_friends')" ]
[ "$(tar -xOzf "$archive" db/sthpw.dump)" = 'DB:sthpw' ]
[ "$(tar -xOzf "$archive" db/niki_friends.dump)" = 'DB:niki_friends' ]
[ "$(tar -xOzf "$archive" globals.sql)" = 'CREATE ROLE tactic;' ]
[ "$(tar -xOzf "$archive" skipped-projects.txt)" = "$(printf 'admin\ncomplex')" ]
if tar -tzf "$archive" | grep -Fx db/admin.dump > /dev/null; then
    printf 'Missing admin database must not be dumped\n' >&2
    exit 1
fi
if tar -tzf "$archive" | grep -Fx db/complex.dump > /dev/null; then
    printf 'Missing complex database must not be dumped\n' >&2
    exit 1
fi

if PATH="$test_dir/bin:$PATH" FAKE_RUNUSER_MARKER="$test_dir/runuser.called" FAKE_DUMP_FAIL=1 PGUSER= PGHOST= PGHOSTADDR= PGSERVICE= sh "$script_dir/side_tools/tactic_db/backup_tactic.sh" "$test_dir/failed"; then
    printf 'Expected a failed dump to fail the backup\n' >&2
    exit 1
fi
[ -z "$(ls -A "$test_dir/failed")" ]

if PATH="$test_dir/bin:$PATH" FAKE_RUNUSER_MARKER="$test_dir/runuser.called" FAKE_RESTORE_LOG="$test_dir/restore.log" PGUSER= PGHOST= PGHOSTADDR= PGSERVICE= sh "$script_dir/side_tools/tactic_db/restore_tactic.sh" "$archive"; then
    printf 'Expected restore without --replace to refuse existing databases\n' >&2
    exit 1
fi
[ ! -f "$test_dir/restore.log" ]

if PATH="$test_dir/bin:$PATH" FAKE_RUNUSER_MARKER="$test_dir/runuser.called" FAKE_RESTORE_LOG="$test_dir/restore.log" FAKE_ACTIVE=1 PGUSER= PGHOST= PGHOSTADDR= PGSERVICE= sh "$script_dir/side_tools/tactic_db/restore_tactic.sh" "$archive" --replace; then
    printf 'Expected restore with active connections to fail\n' >&2
    exit 1
fi
[ ! -f "$test_dir/restore.log" ]

PATH="$test_dir/bin:$PATH" FAKE_RUNUSER_MARKER="$test_dir/runuser.called" FAKE_RESTORE_LOG="$test_dir/restore.log" PGUSER= PGHOST= PGHOSTADDR= PGSERVICE= sh "$script_dir/side_tools/tactic_db/restore_tactic.sh" "$archive" --replace
[ "$(sed -n 'p' "$test_dir/restore.log")" = "$(printf 'sthpw\nniki_friends')" ]
