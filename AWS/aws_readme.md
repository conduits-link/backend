# AWS Readme

For maximum flexibility, we want the option to deploy our own LLM - most likely Meta's LLaMA 2 - onto Amazon SageMaker, AWS's AI service. This folder contains the IaC (infrastructure-as-code) resources to automate this process as desired.

See below for a step-by-step guide on how to deploy LLaMA 2 onto AWS from scratch.

## Setup

* [Creating a containerised AI model](#cleanup)
* [AWS setup](#aws-setup)

### Creating a containerised AI model

First of all, install [Docker](https://docs.docker.com/engine/install/).

#### Downloading LLaMA

In this tutorial, we download vanilla Meta LLaMA 2. You may also wish to consider downloading a different Open LLM, for example one taken from the Hugging Face [Open LLM Leaderboards](https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard).

* Clone [this](https://github.com/facebookresearch/llama) Meta LLaMA repo.
* Request a LLaMA download link [here](https://ai.meta.com/resources/models-and-libraries/llama-downloads/).
* Ensure you have `wget` and `md5sum` installed.
* Inside the repo, run
  ```
  ./download.sh
  ```
  Note: for some reason I had to run
  ```
  . download.sh
  ```
  instead.
  
* Paste the download link from the email you requested and select which model you wish to download.

#### Create Docker image

Todo.

### AWS setup

Now we've created our containerised AI model, we're ready to deploy it on AWS, as disussed below. See [this Amazon article](https://aws.amazon.com/blogs/machine-learning/deploy-and-manage-machine-learning-pipelines-with-terraform-using-amazon-sagemaker/) for more details on this process.

First of all, [install Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli).

#### Deploy AWS instances

With Terraform installed, the following can be run to deploy the AWS Sagemaker instances specified in [terraform.tfvars](infrastructure/terraform.tfvars).

[**Warning:** This _will_ cost you money if you're not careful!]

```bash
export AWS_PROFILE=<your_aws_cli_profile_name>
cd terraform/infrastructure
terraform init
terraform plan
terraform apply
```

#### Push containerised AI model to AWS

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

#### Run ML Pipeline

We now go to AWS Step Functions, a visual workflow tool, to run the ML pipeline. From here we can:

* Run our AI model.

* Train our AI model on data stored in an S3 bucket.

* Create an endpoint so we can access our model for inference.

#### Invoke endpoint

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

#### Cleanup

When we're done, we must destroy all of our AWS infrastructure, else we will incur (substantial!) additional costs.

1. On the Amazon S3 console, delete the training set and all the models we trained.

    (The models can also be deleted from the AWS CLI.)

2. Delete the SageMaker endpoints, endpoint configuration, and models created via Step Functions - either via the SageMaker console or the AWS CLI.

3. Destroy our infrastructure:
    ```bash
    cd terraform/infrastructure
    terraform destroy
    ```
