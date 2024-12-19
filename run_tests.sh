#!/bin/bash
sh run.sh &
sudo docker buildx build -t src-tests -f ./tests.Dockerfile .
sudo docker run --name tests_c --env-file ./.env --network ai_ecom_app_net --rm src-tests
sh clean_up.sh