NAME="golmi_server"
HOST="127.0.0.1"
PORT=5000

docker build --tag "$NAME" -f dockerfile .
docker run \
    --network host \
    --restart unless-stopped \
    -e GOLMI_HOST=$HOST \
    -e GOLMI_PORT=$PORT \
    -d $NAME