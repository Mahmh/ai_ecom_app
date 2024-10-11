#!/bin/bash
stop_web_server() {
    # Find the PID of the server
    PID=$(ps aux | grep "next" | grep -v 'grep' | awk '{print $2}')
    # Kill the process
    if [ -z "$PID" ]; then
        echo "Next.js web server is not running."
    else
        sudo kill -15 $PID
        echo "Next.js web server (PID $PID) has been stopped."
    fi
}

stop_api_server() {
    local PORT=8000

    # Find the process ID (PID) using the port
    PID=$(sudo lsof -t -i :$PORT)

    # Check if a process is found
    if [ -z "$PID" ]; then
        echo "API server is not running on port $PORT."
        return 1
    fi

    # Kill the process
    sudo kill -15 $PID
    echo "API server running on port $PORT has been stopped."
}

stop_db_container() {
    cd src
    sudo docker-compose down --rmi all -v
    echo "Stopped DB container."
    cd ..
}

stop_web_server
stop_api_server
stop_db_container