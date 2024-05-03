#!/bin/bash

SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

prod=`python -c "import toml, os; print(toml.load(os.path.join('$SCRIPTPATH','config.toml'))['app']['prod']);"`
workers=4

echo "Running server with 4 workers"

if [ "$prod" == "False" ]; then
	python $SCRIPTPATH/run.py
else
	port=`python -c "import toml, os; print(toml.load(os.path.join('$SCRIPTPATH','config.toml'))['app']['port']);"`
	ssl=`python -c "import toml, os; print(toml.load(os.path.join('$SCRIPTPATH','config.toml'))['app']['ssl']);"`
	secret_key=`python -c "import context; print(context.generate_secret_key(32));"`
	gunicorn_cmd="run:build_app(app={\"secret_key\":\"$secret_key\"})"
	if [ "$ssl" == "False" ]; then
		gunicorn -w $workers -b 0.0.0.0:$port $gunicorn_cmd
	else
		ssl_cert=`python -c "import toml, os; print(toml.load(os.path.join('$SCRIPTPATH','config.toml'))['app']['ssl_cert']);"`
		ssl_key=`python -c "import toml, os; print(toml.load(os.path.join('$SCRIPTPATH','config.toml'))['app']['ssl_key']);"`
		if [ ! -f "$ssl_cert" ]; then
			echo "Cannot find the ssl certificate file mnetionned in the config file. Aborting execution."
			echo "SSL Cert location: $ssl_cert"
			exit 1
		fi
		if [ ! -f "$ssl_key" ]; then
			echo "Cannot find the ssl key file mnetionned in the config file. Aborting execution."
			echo "SSL Key location: $ssl_key"
			exit 1
		fi
		gunicorn -w $workers -b 0.0.0.0:$port --certfile=$ssl_cert --keyfile=$ssl_key $gunicorn_cmd
	fi
fi
