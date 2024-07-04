#!/bin/bash

docker-compose --project-name metrics down
docker-compose --project-name metrics build database
docker-compose --project-name metrics up -d database