# !/bin/bash

if [ "$(docker ps -aq -f name=kmatrix2_run)" ]; then
    echo "Stopping and removing existing container kmatrix2_run..."
    docker rm -f kmatrix2_run
else
    echo "No existing container kmatrix2_run found."
fi

# (Optional) Add the mapping path corresponding to the model in the startup command, so that you do not need to re-download the model when restarting the container (for the KMatrix_v2 model path, refer to root_config.py)
# For example:
# -v /netcache/huggingface/Llama-2-7b-chat-hf/:/app/KMatrix_v2/dir_model/generator/Llama-2-7b-chat-hf \


# Note that the port number should not conflict with other services.
docker run -idt --gpus all \
    -p 8010:8010 \
    -p 8020:8020 \
    -v $(pwd):/app/KMatrix_v2/ \
    --name kmatrix2_run kmatrix2:v1 \
    /bin/bash '/app/KMatrix_v2/startup.sh'


# Enter the container for debugging
# docker exec -it kmatrix2_run /bin/bash