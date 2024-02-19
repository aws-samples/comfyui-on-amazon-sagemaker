import boto3

client = boto3.client("sagemaker-runtime")

def invoke_from_prompt(prompt_file):
    print(f"prompt: {prompt_file}")

    # read the prompt data from json file
    with open(prompt_file) as prompt_file:
      prompt_text = prompt_file.read()

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
    # invoke_from_prompt("test_prompt_1.json")
    invoke_from_prompt("test_prompt_2.json")
