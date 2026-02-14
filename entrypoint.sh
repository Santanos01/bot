#!/bin/sh
set -e

python -m app.utils.db_wait
python -m app.utils.db_init
alembic upgrade head
exec python -m app.main
