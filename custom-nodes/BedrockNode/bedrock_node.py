import boto3
import json
import base64
import io
from PIL import Image
import numpy as np
import torch

bedrock = boto3.client("bedrock-runtime", region_name="us-west-2")

class Image2ImageNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"image": ("IMAGE",),
                         "prompt": ("STRING", {"default": ""}), 
                         "strength": ("FLOAT", {"default": 0.75})}
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "image_to_image"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def image_to_image(self, image, prompt, strength):
        # Convert input image tensor to PIL Image
        input_array = image.cpu().numpy().squeeze()
        input_image = Image.fromarray(np.clip(255.0 * input_array, 0, 255).astype(np.uint8))
        
        # Get original dimensions and resize maintaining aspect ratio
        width, height = input_image.size
        target_width = min(max(width, 640), 1536)
        scale = target_width / width
        target_height = int(height * scale)
        
        # Ensure minimum dimensions
        if target_height < 640:
            target_height = 640
            target_width = int(width * (640 / height))
        
        input_image = input_image.resize((target_width, target_height), Image.LANCZOS)

        # Process with Bedrock API
        buffered = io.BytesIO()
        input_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        response = bedrock.invoke_model(
            modelId='stability.sd3-large-v1:0',
            body=json.dumps({
                'prompt': prompt,
                'image': img_str,
                'strength': strength,
                'mode': 'image-to-image'
            })
        )

        try:
            # Process response and convert to tensor
            output_body = json.loads(response["body"].read().decode("utf-8"))
            image_data = base64.b64decode(output_body["images"][0])
            output_image = Image.open(io.BytesIO(image_data))
            output_image.save("output_image.png")
            # Convert to numpy array with correct shape for save_images
            output_array = np.array(output_image)
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
            return (torch.zeros_like(image),)


NODE_CLASS_MAPPINGS = {"Image2ImageNode": Image2ImageNode}
