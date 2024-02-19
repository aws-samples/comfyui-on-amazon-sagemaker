#!/bin/bash -x
# script to create a model artifact folder for ComfyUI

# modify variables for your environment
TARGET_DIR="model-data"
TARGET_FILE="model-data.tgz"
S3_PATH="s3://<YOUR AWS BUCKET>/model-data-comfyui-sd.tgz"

# initialize empty folder structure
mkdir -p ${TARGET_DIR}
mkdir -p ${TARGET_DIR}/checkpoints
mkdir -p ${TARGET_DIR}/clip
mkdir -p ${TARGET_DIR}/clip_vision
mkdir -p ${TARGET_DIR}/configs
mkdir -p ${TARGET_DIR}/controlnet
mkdir -p ${TARGET_DIR}/embeddings
mkdir -p ${TARGET_DIR}/loras
mkdir -p ${TARGET_DIR}/upscale_models
mkdir -p ${TARGET_DIR}/vae

# download models that you want to include
wget -nc 'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors' -P ${TARGET_DIR}/checkpoints
wget -nc 'https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.ckpt' -P ${TARGET_DIR}/checkpoints

# tar gzip the folder and upload to S3
# gzip in tar is slow, use pigz to speed up compression on multiple cores
tar -cv -C ${TARGET_DIR} . | pigz -1 > ${TARGET_FILE}
# tar -czvf ${TARGET_FILE} -C ${TARGET_DIR} .
aws s3 cp ${TARGET_FILE} ${S3_PATH}
