#!/bin/sh
# Run a throwaway Forgejo against this theme.
#
#   ./dev.sh            start on http://localhost:3000
#   ./dev.sh reset      delete the instance and start over
#
# Needs: brew install forgejo. Everything it writes lives in .dev/, which is
# gitignored; nothing here touches a real instance.
set -e

DIR=$(cd "$(dirname "$0")" && pwd)
FORGEJO=${FORGEJO:-/opt/homebrew/opt/forgejo/bin/forgejo}
THEME=${THEME:-dataverket-auto}

[ -x "$FORGEJO" ] || { echo "forgejo not found at $FORGEJO - brew install forgejo" >&2; exit 1; }

if [ "$1" = reset ]; then rm -rf "$DIR/.dev"; fi

if [ ! -f "$DIR/.dev/conf/app.ini" ]; then
  mkdir -p "$DIR/.dev/conf" "$DIR/.dev/data" "$DIR/.dev/repos"
  cat > "$DIR/.dev/conf/app.ini" <<EOF
APP_NAME = Dataverket
RUN_MODE = prod
WORK_PATH = $DIR/.dev

[server]
HTTP_PORT = 3000
ROOT_URL  = http://localhost:3000/
OFFLINE_MODE = true

[database]
DB_TYPE = sqlite3
PATH    = $DIR/.dev/data/forgejo.db

[repository]
ROOT = $DIR/.dev/repos

[security]
INSTALL_LOCK   = true
SECRET_KEY     = $("$FORGEJO" generate secret SECRET_KEY)
INTERNAL_TOKEN = $("$FORGEJO" generate secret INTERNAL_TOKEN)

[ui]
DEFAULT_THEME = $THEME
THEMES = dataverket-auto,dataverket-light,dataverket-dark,forgejo-auto,forgejo-light,forgejo-dark

[log]
LEVEL = Warn
EOF
  echo "created .dev/conf/app.ini"
fi

python3 "$DIR/make-theme.py"

exec "$FORGEJO" web \
  --config "$DIR/.dev/conf/app.ini" \
  --work-path "$DIR/.dev" \
  --custom-path "$DIR"
