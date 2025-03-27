# ComfyUI AWS Integration Nodes

This repository contains custom nodes for ComfyUI that integrate with AWS services for AI image generation:

1. **Bedrock Node**: Image-to-image generation using Amazon Bedrock and Stable Diffusion

![ComfyUI Bedrock Node Example](imgs/comfy-custom.png)
2. **SageMaker Node**: Text-to-image generation using FP8 Flux Dev 1 diffusion pipeline

![ComfyUI SageMaker Node Example](imgs/sagemaker_node.png)

Both nodes seamlessly integrate with your ComfyUI workflows, allowing you to leverage AWS's powerful AI infrastructure directly within the ComfyUI interface.

## Features

### Bedrock Node
- Image-to-image generation using Stability AI's SD3 model through Amazon Bedrock
- Automatic image resizing to meet model requirements
- Support for customizable prompt and strength parameters

### SageMaker Node
- Text-to-image generation using FP8 Flux Dev 1 diffusion pipeline
- Custom FP8-optimized model deployment
- Flexible parameter customization

## Prerequisites

- An AWS account with access to Amazon Bedrock and SageMaker
- Proper AWS credentials configured
- Python 3.x
- ComfyUI installed

## Installation

1. Configure your AWS credentials through one of these methods:
   - AWS CLI (`aws configure`)
   - Environment variables
   - AWS credentials file

2. Add both node folders to the ComfyUI `custom_nodes` directory

## Usage

### Bedrock Node

1. Launch ComfyUI
2. Find the "Image2ImageNode" in the node browser under the "image" category
3. Connect the node to your workflow with:
   - Input image
   - Text prompt
   - Strength value (0-1)

#### Parameters
- **image**: Input image tensor
- **prompt**: Text description for the desired image modification
- **strength**: Float value between 0 and 1 determining how much to modify the original image (default: 0.75)

### SageMaker Node

1. Deploy the FP8 Flux Dev 1 model using the provided notebook
2. Launch ComfyUI
3. Find the SageMaker "Text@Image" node in the node browser
4. Connect the node to your workflow with:
   - Text prompt
   - Optional parameters

#### Model Deployment
There was no full pipeline available that leveraged the flux1dev transformer in FP8, so I created one and made it available here: [Jlonge4/flux-dev-fp8](https://huggingface.co/Jlonge4/flux-dev-fp8). This is important as using hugging face diffusers `from_single_file` download option will create symlinks, rendering your `model.tar.gz` unusable for deployment.

To deploy the model:
1. Run the `deploy_flux_dev-pipe.ipynb` notebook
2. A g5.8xlarge instance is recommended for deployment
3. Once deployed, the endpoint can be used directly by the SageMaker node

## Notes

### Bedrock Node
- Automatically handles image resizing to meet the model's requirements (minimum 640px, maximum 1536px)
- Images are processed maintaining aspect ratio
- Uses the `stability.sd3-large-v1:0` model from Amazon Bedrock

### SageMaker Node
- Be mindful of the 60 second timeout for SageMaker inference endpoints
- The single FP8 safetensors file I used to create my pipeline / HF repo is found here: [Comfy-Org/flux1-dev](https://huggingface.co/Comfy-Org/flux1-dev).