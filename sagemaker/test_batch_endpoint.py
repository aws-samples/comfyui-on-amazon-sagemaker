import json
import boto3
import random

client = boto3.client("sagemaker-runtime")

def update_seed(prompt_dict):
    # set the seed for our KSampler node
    for i in prompt_dict:
        if "inputs" in prompt_dict[i]:
            if "seed" in prompt_dict[i]["inputs"]:
                prompt_dict[i]["inputs"]["seed"] = random.randint(0, 1e10)
    return prompt_dict

def invoke_from_prompt(prompt_file):
    print(f"prompt: {prompt_file}")

    # read the prompt data from json file
    with open(prompt_file) as prompt_file:
      prompt_text = prompt_file.read()

    prompt_dict = json.loads(prompt_text)
    prompt_dict = update_seed(prompt_dict)
    prompt_text = json.dumps(prompt_dict)
    

    endpoint_name = "comfyui-endpoint"
    content_type = "application/json"
    accept = "*/*"
    payload = prompt_text
    response = client.invoke_endpoint(
        EndpointName=endpoint_name, ContentType=content_type, Accept=accept, Body=payload
    )

    print(response)
    # print(response["Body"].read())

if __name__ == "__main__":
    #invoke_from_prompt("test_prompt_1.json")
    invoke_from_prompt("test_prompt_2.json")
    invoke_from_prompt("test_prompt_2.json")
    invoke_from_prompt("test_prompt_2.json")
    invoke_from_prompt("test_prompt_2.json")
    invoke_from_prompt("test_prompt_2.json")
