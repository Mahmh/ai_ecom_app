#!/bin/bash
web_serve() {
    cd src/client/
    if [ "$1" = "prod" ]; then
        # run in production mode
        if mkdir out/; then
            rm -r out/
            echo 'Please run `npm run build` before running the production server`'
        else
            npx serve@latest out
        fi
    else
        # run in developer mode
        npm run dev
    fi
}

web_serve $1