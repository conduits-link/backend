# AWS Readme

For maximum flexibility, we want the option to deploy our own LLM - most likely Meta's LLaMA 2 - onto Amazon SageMaker, AWS's AI service. This folder contains the IaC (infrastructure-as-code) resources to automate this process as desired.

See below for a step-by-step guide on how to deploy LLaMA 2 onto AWS from scratch.

## Contents

* [Creating a containerised AI model](#creating-a-containerised-ai-model)
  * [Download LLaMA](#download-llama)
  * [Build Docker image](#build-docker-image)
  * [Run Docker container and model](#run-docker-container-and-model)
* [AWS setup](#aws-setup)
  * [Deploy AWS instances](#deploy-aws-instances)
  * [Push containerised AI model to AWS](#push-containerised-ai-model-to-aws)
  * [Run ML pipeline](#run-ml-pipeline)
  * [Invoke endpoint](#invoke-endpoint)
  * [Cleanup](#cleanup)

## Creating a containerised AI model

First of all, install [Docker](https://docs.docker.com/engine/install/).

### Download LLaMA

In this tutorial, we download Meta's LLaMA 2. You may also wish to consider deploying a different Open LLM, for example one taken from the Hugging Face [Open LLM Leaderboards](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard).

* In terminal, navigate to [AWS/llama](AWS/llama), our slightly modified copy of the Meta LLaMA repo.

* Request a LLaMA download link [here](https://ai.meta.com/resources/models-and-libraries/llama-downloads/).
* Ensure you have `wget` and `md5sum` installed.
* Inside AWS/llama, run
  ```bash
  ./download.sh
  ```
  Note: for some reason I had to run
  ```bash
  . download.sh
  ```
  instead.
  
* Paste the download link from the email you requested and select which model you wish to download. For our purposes here, make sure it is one of the "chat" models.

### Build Docker image

We can now build the Docker image.

* Start the Docker daemon, by either:
  * opening Docker Desktop.
  * running `sudo systemctl start docker` in a Linux terminal.
  * running `dockerd` or `sudo dockerd`.
  See [here](https://docs.docker.com/config/daemon/start/) for more details.

* Build the Docker image. In terminal, navigate to to the LLaMA folder containing the Dockerfile discussed above, and run
    ```bash
    docker build -t llama-image .
    ```
    where the string `llama-image` can be whatever name you like.

    Note that this will take a while - ~600 seconds on my laptop.

**Note:** as mentioned above, this repo contains some slightly modified LLaMA code. Here are the modifications:  
  
* [AWS/llama/custom_chat_completion.py](AWS/llama/custom_chat_completion.py) has been added to allow you to send LLaMA custom prompts as follows:
    ```bash
    torchrun --nproc_per_node 1 custom_chat_completion.py \
      --ckpt_dir llama-2-7b-chat/ \ # Specify the model version you downloaded here.
      --tokenizer_path tokenizer.model \
      --max_seq_len 512 --max_batch_size 6
      --user_message "Tell me about Noteworthy, the LLM-based text editor."
    ```
  
* [AWS/llama/Dockerfile](AWS/llama/Dockerfile) specifies how to build the container.
  * To avoid incurring unnecessary AWS ECR expenses, we have removed as many files from the original LLaMA repo as possible. The Dockerfile copies all files from this folder, then removes the license (which we are required to host in the repo), and download.sh, neither of which are necessary to run the model.

  * We also set the entrypoint of the model as the custom_chat_completion.py file defined above, so we can send prompts to our model.

  * It is also possible to configure the entrypoint with more arguments, so that we have to specify fewer arguments when calling the model.

### Run Docker container and model

* Once you have built the image, find it in the terminal and run:

  ```bash
  docker run -it --name llama-container llama-image
  ```
  where `llama-container` can be whatever name you like, and `llama-image` should match with the name you chose for the image above.

  This will start a new container that will accept commands and keep running until you stop it. 
  
    * `-it` stands for "interactive" and "terminal", allowing you to interact with the container's CLI.

* Now the container is running, you can send it prompts via the endpoint with:

  ```bash
  docker run -it --name llama-container llama-image \
  --ckpt_dir llama-2-7b/ \ # Specify the model version you downloaded here.
  --tokenizer_path tokenizer.model \
  --max_seq_len 128 --max_batch_size 4 
  --user_message "Tell me about Noteworthy, the LLM-based text editor."
  ```

* When you're done, stop your container with:

  ```bash
  docker stop llama-container
  ```

## AWS setup

Now we've created our containerised AI model, we're ready to deploy it on AWS, as disussed below. See [this Amazon article](https://aws.amazon.com/blogs/machine-learning/deploy-and-manage-machine-learning-pipelines-with-terraform-using-amazon-sagemaker/) for more details on this process.

First of all, [install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli).

### Deploy AWS instances

With Terraform installed, the following can be run to deploy the AWS Sagemaker instances specified in [terraform.tfvars](infrastructure/terraform.tfvars).

[**Warning:** This _will_ cost you money if you're not careful! Make sure to [clean up](#cleanup) when you're done.]

```bash
export AWS_PROFILE=<your_aws_cli_profile_name>
cd terraform/infrastructure
terraform init
terraform plan
terraform apply
```

### Push containerised AI model to AWS

We must now push the containerised AI model we built [above](#creating-a-containerised-ai-model) to Amazon ECR ("Elastic Container Registry"). From here, our SageMaker instance can access our AI model.

To do this, first [create an ECR repo](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-create.html), then run:

```bash
cd location/of/your/container
export AWS_PROFILE=<your_aws_cli_profile_name>
aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin <account_number>.dkr.ecr.eu-west-1.amazonaws.com
docker build -t ml-training .
docker tag ml-training:latest <account_number>.dkr.ecr.eu-west-1.amazonaws.com/<ecr_repository_name>:latest
docker push <account_number>.dkr.ecr.eu-west-1.amazonaws.com/<ecr_repository_name>
```
with the appropriate details substituted into the angled brackets above.

### Run ML Pipeline

We now go to AWS Step Functions, a visual workflow tool, to run the ML pipeline. From here we can:

* Run our AI model.

* Train our AI model on data stored in an S3 bucket.

* Create an endpoint so we can access our model for inference.

### Invoke endpoint

Finally, we can run a Python script using Boto3, AWS's Python SDK, to invoke the endpoint of our AI model. For example:

```py
import boto3
from io import StringIO
import pandas as pd

client = boto3.client('sagemaker-runtime')

endpoint_name = 'Your endpoint name' # Your endpoint name.
content_type = "text/csv"   # The MIME type of the input data in the request body.

payload = pd.DataFrame([[1.5,0.2,4.4,2.6]])
csv_file = StringIO()
payload.to_csv(csv_file, sep=",", header=False, index=False)
payload_as_csv = csv_file.getvalue()

response = client.invoke_endpoint(
    EndpointName=endpoint_name, 
    ContentType=content_type,
    Body=payload_as_csv
    )

label = response['Body'].read().decode('utf-8')
print(label)
```

In other words, we can finally send our model data (e.g. a question), and it will send stuff back (e.g. an answer).

### Cleanup

When we're done, we must destroy all of our AWS infrastructure, else we will incur (substantial!) additional costs.

1. On the Amazon S3 console, delete the training set and all the models we trained.

    (The models can also be deleted from the AWS CLI.)

2. Delete the SageMaker endpoints, endpoint configuration, and models created via Step Functions - either via the SageMaker console or the AWS CLI.

3. Destroy our infrastructure:
    ```bash
    cd terraform/infrastructure
    terraform destroy
    ```
