#!/bin/bash
cd sentry_onpremise && SENTRY_PYTHON3=1 ./install.sh
sudo docker-compose -f docker-compose.yml up -d
cd ../microservice
sudo docker-compose up -d

