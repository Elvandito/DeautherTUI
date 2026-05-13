#!/bin/bash
# Universal DeautherTUI Docker Launcher
# This script builds (if necessary) and runs the DeautherTUI inside a Docker container
# with the necessary host networking privileges to access physical Wi-Fi hardware.

IMAGE_NAME="deauther-tui-universal"

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed or not in PATH."
    echo "Please install Docker to run the universal container."
    exit 1
fi

echo "Checking for DeautherTUI Docker image..."

# Check if the image exists, if not build it
if [[ "$(docker images -q $IMAGE_NAME 2> /dev/null)" == "" ]]; then
    echo "Building universal Docker image (this will only happen once)..."
    docker build -t "$IMAGE_NAME" .
fi

echo "Launching DeautherTUI in Docker..."
# Run interactive, remove container on exit, use host network, and grant privileged access to hardware
exec docker run -it --rm --net host --privileged "$IMAGE_NAME"
