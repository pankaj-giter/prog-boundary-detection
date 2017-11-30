POSTED_FILE=
SERVER_PATH="localhost:8000/localhost:8001"
if [ "$#" -ge 1 ]; then
    POSTED_FILE=$1
    if [ "$#" -gt 2 ]; then
        echo "Too many arguments. Only accepts up to 2 arguments."
        exit
    fi

    if [ "$#" -eq 2 ]; then
        SERVER_PATH=$2
    fi
fi
 

curl -v -X POST -H 'Connection: close' -H "Content-Type: application/binary" --data-binary @${POSTED_FILE} http://${SERVER_PATH}/tech-jam/${POSTED_FILE}
#curl http://${SERVER_PATH}/rek.txt
