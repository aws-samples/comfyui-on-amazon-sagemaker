# Development Guide

## Model Data
ComfyUI loads models from folder `ComfyUI/models`, and supports loading extra search paths by configuring `extra_model_paths.yaml`. We pack all the necessary model files into a tar gzipped file and upload to S3. Then these files will be copied to `/opt/ml/model` by SageMaker, and can be used by ComfyUI inside inference container.

### How to prepare model data
The model prepare script can be found at [model/build.sh](model/build.sh), which downloads models from HuggingFace, creates tar gzipped file and uploads to S3. The model files are installed to `model/model-artifact`. Customize it to prepare your models.
```sh
cd ./model
./build.sh
```
*Note [model/build.sh](model/build.sh) is executed by [deploy.sh](deploy.sh) too.*


## Inference Image
This section describes the container that runs your inference code for hosting services. Read [AWS documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/your-algorithms-inference-code.html) for how SageMaker works.

### Highlights
 - ComfyUI is running in container and listening on `127.0.0.1:8188`. The inference code will access to the local ComfyUI server by REST api and WebSocket.
 - The container has read-only access to `/opt/ml/model`, which SageMaker copies the model artifacts from S3 location to this directory. `extra_model_paths.yaml` of ComfyUI is configured to load models (such as CheckPoint, VAE, LoRA) from this path.
 - The container has a Flask server listening on port 8080 and accept `POST` requests to `/invocations` and `GET` requests to `/ping` endpoints.
 - Health Check (`GET` requests to `/ping`) is to check whether the local ComfyUI is still running and responding.
 - Inference Requests (`POST` requests to `/invocations`) is implemented by passing the payload to ComfyUI server. The payload is the same as used by ComfyUI GUI, in which the network traffics inspected in DevTools of browser.
   - Inference result is the image itself. If `Accept` header of the inference requests indicate jpeg is supported (e.g., `*/*`, `image/jpeg`), the output image will be converted to jpeg, else leave default as png.
 - Environment variables supported:
   - `JPEG_QUALITY` - Set between 0 to 95 for jpeg quality (default 90)
   - `DEBUG_HEADER` - Set to `true` to print HTTP header of requests in CloudWatch log
 
## Local run of ComfyUI GUI
Follow the following to build and run ComfyUI locally with GUI. The image install ComfyUI same way as inference image does, so you can use it for model testing and tuning image workflow. The initial part of the Dockerfile is the same as the inference image, so most layers are shared.


1. Build the image.
```sh
# run inside comfyui-on-amazon-sagemaker folder
export IMAGE_GUI="comfyui-gui:latest"
export LOCAL_MODEL_PATH="${PWD}/model/model-artifact"
docker build -t ${IMAGE_GUI} ./image -f ./image/Dockerfile.gui
```

2. Run the container. Note it requires model data to [prepared](./DEVELOPMENT.md#how-to-prepare-model-data) in advance.
```sh
docker run --rm --gpus all --volume ${LOCAL_MODEL_PATH}:/opt/ml/model --publish 8188:8188 ${IMAGE_GUI}
```

3. Open a browser and browse to `http://<EC2_IP>:8188`. Make sure the inbound rules of EC2 security group allows port 8188 from your browser.

## Workflow File

### How to download it from ComfyUI
Turn on **Enable Dev mode Options** from the ComfyUI settings (settings icon in the bottom right menu), then you will see **Save (API format)** button appear. Click **Save (API format)** button to download the json file. Replace the positive prompt text to `POSITIVE_PROMT_PLACEHOLDER`, and negative prompt to `NEGATIVE_PROMPT_PLACEHOLDER` which allows the lambda function to replace with during invocation. Then put the json file inside [lambda/workflow/](lambda/workflow/) folder. 

### Lambda Function
Source code of Lambda function is in [lambda/lambda_function.py](lambda/lambda_function.py). In this project the lambda function is invoked by lambda function URL, but you can integrate with API Gateway or ALB for your application. You can find the full request and response payloads from [AWS documentation](https://docs.aws.amazon.com/lambda/latest/dg/urls-invocation.html#urls-payloads).

This is the sample event for lambda function URL. Only `body` field is used.
```json
{
  "body": "{\"positive_prompt\": \"hill happy dog\",\"negative_prompt\": \"hill\",\"prompt_file\": \"workflow_api.json\",\"seed\": 123}"
    }
```

Here are the fields in the body:
| Key             | Value                                                                                                         | Optional                                                             |
|-----------------|---------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| positive_prompt | Text to replace `POSITIVE_PROMT_PLACEHOLDER` in prompt                      |                                                                      |
| negative_prompt | Text to replace `NEGATIVE_PROMPT_PLACEHOLDER` in prompt                     |                                                                      |
| prompt_file     | Workflow file in lambda/workflow/                                                | Yes. Default value: `workflow_api.json`                             |
| seed            | Seed integer | Yes. If not specified, a random seed will be used. |


## CloudFormation
CloudFormation template can be found at [cloudformation/template.yml](cloudformation/template.yml). [deploy.sh](deploy.sh) passes parameters to CloudFormation template. 

### Specify ComfyUI Version
Check the commit ID or tag version on [ComfyUI repository](https://github.com/comfyanonymous/ComfyUI), then update `COMFYUI_GIT_REF` in [deploy.sh](deploy.sh#L23).

### SageMaker Model
To create or update the SageMaker model you will need the ECR url and the model S3 path, refer to [AWS documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints-deploy-models.html) for more details about model deployment. You can also read [AWS documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/realtime-endpoints-test-endpoints.html) on how to invoke endpoint for real-time inference of generating image. You can pass the new values for `ModelVersion`, `ModelDataS3Key`, and `ModelEcrImage` and update the CloudFormation stack.

### SageMaker Instance Type
The default instance type is `ml.g5.xlarge`. Change to `ml.g4dn.xlarge` for lower cost or `ml.g5.xlarge` is not available in your AWS region.

### SageMaker Auto Scaling
By default it is disabled, you can set `SageMakerAutoScaling` to enable it. You can also uncomment the followings to define the schedule actions to set dynamic max and min by schedule.
```yaml
  ComfyUIScalableTarget:
    Type: "AWS::ApplicationAutoScaling::ScalableTarget"
    DependsOn: ComfyUIEndpoint
    Condition: EnableAutoScaling
    Properties:
      MaxCapacity: 3
      MinCapacity: 1
      ResourceId: !Sub "endpoint/${ComfyUIEndpoint.EndpointName}/variant/${AppName}-${ModelVersion}"
      ScalableDimension: sagemaker:variant:DesiredInstanceCount
      ServiceNamespace: sagemaker
      # Optional: Uncomment below to define autoscaling capacity according to schedule
      # ScheduledActions:
      #   - ScheduledActionName: scheduled-action-at-1800-utc
      #     ScalableTargetAction:
      #       MaxCapacity: 1
      #       MinCapacity: 1
      #     Schedule: cron(0 18 * * ? *)
      #   - ScheduledActionName: scheduled-action-at-0400-utc
      #     ScalableTargetAction:
      #       MaxCapacity: 3
      #       MinCapacity: 1
      #     Schedule: cron(0 4 * * ? *)
```
### Lambda Function URL Auth
By default AWS_IAM auth is enabled, and you need to [sign your request](https://docs.aws.amazon.com/AmazonS3/latest/API/sig-v4-authenticating-requests.html) with IAM to protect your endpoint. You may set `LambdaUrlAuthType` to NONE for testing but it's not recommended. Alternatively, you can disable the lambda function URL and put the lambda function under api gateway or ALB, or even invoke the sagemaker endpoint directly from your current backend.
