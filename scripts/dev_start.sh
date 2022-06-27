#!/bin/bash
cd ..

config=$(cat << EOL
database:
  database:
  hosts:
    - 127.0.0.1
  port: 5432
  dbname: calendar_db
  password: password
  user: calendar_admin
EOL
)

echo "Start with config"
echo "$config"

echo "$config" > ./dev_config.yaml


echo "command: PYTHON_PATH=$(pwd) python ./main.py -p=8000 -H=:: --reload --config=dev_config.yaml"
PYTHON_PATH=$(pwd) python ./main.py -p=8000 -H=:: --reload --config=dev_config.yaml
