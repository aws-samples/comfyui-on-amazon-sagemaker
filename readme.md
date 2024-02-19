# ComfyUI on SageMaker
This project demonstrate how to pack ComfyUI into SageMaker and serve as SageMaker inference endpoint.


## 1. Inference code image
This section describes the Docker container that runs your inference code for hosting services. Read [AWS documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html) for more details.

### Highlights of image
 - ComfyUI is running in container and listening on `127.0.0.1:8188`. The inference code will access to the local ComfyUI server by REST api and WebSocket.
 - The container has read-only access to `/opt/ml/model`, which SageMaker copies the model artifacts from S3 location to this directory. `extra_model_paths.yaml` of ComfyUI is configured to load models (such as CheckPoint, VAE, LoRA) from this path.
 - The container has a Flask server listening on port 8080 and accept `POST` requests to `/invocations` and `GET` requests to `/ping` endpoints.
 - Health Check (`GET` requests to `/ping`) is to check whether the local ComfyUI is still running and responding.
 - Inference Requests (`POST` requests to `/invocations`) is implemented by passing the payload to ComfyUI server. The payload is the same as used by ComfyUI GUI, in which the network traffics inspected in DevTools of browser.
   - Inference result is the image itself. If `Accept` header of the inference requests indicate jpeg is supported (e.g., `*/*`, `image/jpeg`), the output image will be converted to jpeg, else leave default as png.
 - Environment variables supported:
   - `JPEG_QUALITY` - Set between 0 to 95 for jpeg quality (default 90)
   - `DEBUG_HEADER` - Set to `true` to print HTTP header of requests in CloudWatch log
 

### How to build
You can build the image using an EC2. You may use AMI `Deep Learning OSS Nvidia Driver AMI GPU PyTorch 2.0.1 (Amazon Linux 2)` but other AMI may also work.

1. Install and configure docker properly for your user.
```sh
# install docker if it does not come with AMI
sudo yum install -y docker
sudo systemctl enable docker.service
sudo systemctl start docker.service

# Add your user to the docker group, so you can run docker commands without sudo
sudo usermod -a -G docker $(whoami)
# Log out and log back in so that your group membership is re-evaluated
```

2. Modify variables for your environment and path, then run it. Switch to the `image` folder.
```sh
# modify variables for your environment
# you need to create ECR repositories in advance
export AWS_DEFAULT_REGION="ap-southeast-1"
export IMAGE_REGISTRY='<YOUR AWS ACCOUNT>.dkr.ecr.ap-southeast-1.amazonaws.com'
export IMAGE_INFERENCE='<YOUR AWS ACCOUNT>.dkr.ecr.ap-southeast-1.amazonaws.com/comfyui-inference:latest'
export IMAGE_GUI='<YOUR AWS ACCOUNT>.dkr.ecr.ap-southeast-1.amazonaws.com/comfyui-gui:latest'
export LOCAL_MODEL_PATH="${HOME}/comfyui-on-sagemaker/model/model-data"
cd ~/comfyui-on-sagemaker/image
```

3. Build and push inference image.
```sh
# login to ECR
aws ecr get-login-password --region "${AWS_DEFAULT_REGION}" | docker login --username AWS --password-stdin "${IMAGE_REGISTRY}"

# build and push image for sagemaker inference
docker build -t ${IMAGE_INFERENCE} . -f Dockerfile.inference
docker push ${IMAGE_INFERENCE}
```

4. (optional) You can run the image locally for development use. Note it requires model data to set up first.
```sh
# local run of inference image for development purpose
docker run --rm --gpus all --volume ${LOCAL_MODEL_PATH}:/opt/ml/model --publish 8080:8080 ${IMAGE_INFERENCE}
```

### ComfyUI GUI
To run ComfyUI with GUI, you can build and run the standalone image. This image install ComfyUI in a container, so you can use it for testing and tuning image generation workload. The initial part of the Dockerfile is the same as the inference image, so most layers are shared.

1. You can build and push the standalone image.
```sh
# build and push image for ComfyUI standalone run with GUI
docker build -t ${IMAGE_GUI} . -f Dockerfile.gui
docker push ${IMAGE_GUI}
```

2. Run the image then you can browse to port 8188 for ComfyUI GUI. Note it requires model data to set up first.
``` sh
# local run of ComfyUI with GUI for development purpose
docker run --rm --gpus all --volume ${LOCAL_MODEL_PATH}:/opt/program/ComfyUI/models -p 8188:8188 ${IMAGE_GUI}
```

## 2. Model data

ComfyUI loads models from its folder `ComfyUI\models`, and supports loading extra search paths by configuring `extra_model_paths.yaml`. We pack all the necessary models into a tar gzipped file and upload to S3. Then these files will be copied to `/opt/ml/model` by SageMaker, and can be used by ComfyUI inside inference container.

### How to build
A sample build script is provided in `model/build.sh`, which download models from HuggingFace, create tar gzipped file and upload to S3. Modify it to fit your needs.
```sh
cd ~/comfyui-on-sagemaker/model

# sample build script to download model and upload to S3 for ComfyUI use in SageMaker
# modify variables for your environment and models you want to download
bash -x ./build.sh
```

## 3. SageMaker endpoint
After you pushed inference container to ECR and uploaded model data to S3, you can deploy model and endpoint in SageMaker for real-time inference. Refer to [AWS documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints-deploy-models.html) for more details. You can also read [AWS documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints-test-endpoints.html) on how to invoke endpoint for real-time inference of generating image.

## References
 - https://github.com/aws/amazon-sagemaker-examples
 - https://github.com/awslabs/stable-diffusion-aws-extension
 - https://github.com/aws-samples/sagemaker-stablediffusion-quick-kit
 - https://github.com/aws-samples/comfyui-on-eks
