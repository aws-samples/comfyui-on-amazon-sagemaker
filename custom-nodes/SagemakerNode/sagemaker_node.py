import boto3
import json
import base64
import io
from PIL import Image
import numpy as np
import torch

runtime = boto3.client('runtime.sagemaker')
ENDPOINT = "flux-image-generator-endpoint"

class Text2ImageNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "a beautiful landscape"})
            },
            "optional": {
                "negative_prompt": ("STRING", {"multiline": True, "default": ""}),
                "guidance_scale": ("FLOAT", {"default": 3.5, "min": 0.0, "max": 20.0, "step": 0.1}),
                "height": ("INT", {"default": 768, "min": 384, "max": 1536, "step": 64}),
                "width": ("INT", {"default": 1360, "min": 384, "max": 2048, "step": 64}),
                "num_inference_steps": ("INT", {"default": 3, "min": 1, "max": 50, "step": 1}),
                "seed": ("INT", {"default": -1})
            }
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "text_to_image"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def text_to_image(self, prompt, negative_prompt, guidance_scale, height, width, num_inference_steps, seed):
        # Create the payload with all parameters
        payload = {
            "prompt": prompt
        }
        
        # Only add optional parameters that are provided
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
            
        if guidance_scale != 3.5:
            payload["guidance_scale"] = guidance_scale
        
        if height != 768:
            payload["height"] = height
        
        if width != 1360:
            payload["width"] = width
        
        if num_inference_steps != 3:
            payload["num_inference_steps"] = num_inference_steps
        
        if seed != -1:
            payload["seed"] = seed


        # Make the direct call
        response = runtime.invoke_endpoint(
            EndpointName=ENDPOINT,
            ContentType="application/json",
            Body=json.dumps(payload)
        )
        print(response)
        try:
            response_body = response["Body"].read().decode("utf-8")
            print("Response Body:", response_body)
            
            # Parse JSON from the response body
            response_data = json.loads(response_body)
            
            # Check if 'image' is in the parsed response
            if "image" not in response_data:
                raise KeyError("'image' key not found in the response")
            
            # Extract the base64-encoded image
            base64_img = response_data["image"]
            
            # Decode the base64 string
            img_bytes = base64.b64decode(base64_img)
            
            # Create a BytesIO object from the decoded bytes
            img_buffer = io.BytesIO(img_bytes)
            
            # Open the image using PIL
            img = Image.open(img_buffer)
            img.save("output_image.png")
            # Convert to numpy array with correct shape for save_images
            output_array = np.array(img)
            if len(output_array.shape) == 2:
                output_array = np.stack([output_array] * 3, axis=-1)
            
            # Convert to float32 and normalize to 0-1 range
            output_array = output_array.astype(np.float32) / 255.0
            
            # Create tensor in format expected by save_images: [B, H, W, C]
            output_tensor = torch.from_numpy(output_array)
            if len(output_tensor.shape) == 3:
                output_tensor = output_tensor.unsqueeze(0)  # Add batch dimension
            
            return (output_tensor,)

        except Exception as e:
            print(f"Error: {e}")


NODE_CLASS_MAPPINGS = {"Text2ImageNode": Text2ImageNode}
