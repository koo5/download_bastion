#!/usr/bin/env fish

function e; or status --is-interactive; or exit 1; end

virtualenv -p /usr/bin/python3 venv ;e
. ./venv/bin/activate.fish ;e

python3 -m pip install --no-cache-dir -r requirements-dev.txt ;e
python3 -m pip install --no-cache-dir -e ../workers ;e

pip install -e ../common/libs/remoulade/[rabbitmq,redis,postgres]
