#!/bin/bash
# script to create a model artifact for SageMaker inference

set -e # Exit on error
set -u # Exit on undefined variable
# set -x # Print commands

# target folder for downloading model artifact
TARGET_DIR="model-artifact"

# target file for tar-gzip archive of model artifact
TARGET_FILE="model-artifact.tgz"

show_usage() {
    echo "Usage: $0 [s3://path/to/s3/object]"
    exit 1
}
# s3 upload path (optional)
S3_PATH=""
if [ "$#" -gt 1 ]; then
    show_usage
elif [ "$#" -eq 1 ]; then
    if [[ "$1" == s3://* ]]; then
        S3_PATH="$1"
    else
        show_usage
    fi
fi

# initialize empty folder structure
mkdir -p "${TARGET_DIR}"
DIRS=(checkpoints clip clip_vision configs controlnet embeddings loras upscale_models vae gligen custom_nodes)
for dir in "${DIRS[@]}"
do
    mkdir -p "${TARGET_DIR}/${dir}"
done

# download models that you want to include
# stable-diffusion-xl-base-1.0 
wget -nc 'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors' -P "${TARGET_DIR}/checkpoints"

cd ${TARGET_DIR}/custom_nodes
[[ -e ComfyUI-Manager ]] || git clone https://github.com/ltdrdata/ComfyUI-Manager.git && (cd ComfyUI-Manager ; git reset --hard 90ae9af6ed2f80343defedb92ac61c79d4dbdc33)
cd -

if [ -z "${S3_PATH}" ]; then
    exit 0
fi
echo "Creating ${TARGET_FILE}..."
# tar gzip the folder and upload to S3
if [ -n "$(which pigz)" ]; then
    # use pigz to speed up compression on multiple cores
    tar -cv -C "${TARGET_DIR}" . | pigz -1 > "${TARGET_FILE}"
else
    # tar is slower
    tar -czvf ${TARGET_FILE} -C ${TARGET_DIR} .
fi
echo "Uploading ${S3_PATH}..."
aws s3 cp "${TARGET_FILE}" "${S3_PATH}"
