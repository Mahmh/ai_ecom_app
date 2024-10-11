#!/bin/bash
cd src

serve_web() {
    cd client
    if [ "$1" = "prod" ]; then
        # run in production mode
        if mkdir out/; then
            rm -r out/
            echo 'Please add `output: 'export'` in `next.config.mjs` and execute `npm run build` before running the production server.'
        else
            npx serve@latest out
        fi
    else
        # run in developer mode
        npm run dev
    fi
    cd ..
}

serve_db() {
    sudo docker-compose up & sleep 10 && cd db/scripts && python3 add_data_to_db.py && echo 'Added data to DB.'
    cd ../..
}

serve_api() {
    cd server/api
    python3 main.py
    cd ../..
}

sudo echo -n ''
serve_db & serve_api & serve_web $1