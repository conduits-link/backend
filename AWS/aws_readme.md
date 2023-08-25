# AWS Readme

For maximum flexibility, we want the option to deploy our own LLM - most likely Meta's LLaMA 2 - onto Amazon SageMaker, AWS's AI service. This folder contains the IaC (infrastructure-as-code) resources to automate this process as desired.

See [this Amazon article](https://aws.amazon.com/blogs/machine-learning/deploy-and-manage-machine-learning-pipelines-with-terraform-using-amazon-sagemaker/) for more details, very roughly sketched out below.

## Setup

### Deploy AWS instances

With Terraform installed, the following can be run to deploy the AWS Sagemaker instances specified in [terraform.tfvars](infrastructure/terraform.tfvars).

[**Warning:** This _will_ cost you money if you're not careful!!]

```bash
export AWS_PROFILE=<your_aws_cli_profile_name>
cd terraform/infrastructure
terraform init
terraform plan
terraform apply
```

### Push containerised AI model to AWS

We must now create a Docker image containing our AI model and push it to Amazon ECR - their Elastic Container Registry. From here, our SageMaker instance can access our AI model.

### Run ML Pipeline

We now go to AWS Step Functions, a visual workflow tool, to run the ML pipeline (which can including training the AI model if desired).

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

When we're done, we must destroy all of our AWS infrastructure, else we will incur additional costs.

* Firstly, our AI container in ECR is stored in AWS storage - S3, along with any training data we may have uploaded.

* Secondly, our endpoints, which were created in Step Functions rather than Terraform, must be destroyed.

* Thirdly, our AWS infrastructure must be destroyed. Fortunately, thanks to Terraform, this is the easy part.

1. On the Amazon S3 console, delete the training set and all the models we trained.

  (The models can also be deleted from the AWS CLI.)

2. Delete the SageMaker endpoints, endpoint configuration, and models created via Step Functions - either via the SageMaker console or the AWS CLI.

3. Destroy our infrastructure:
    ```bash
    cd terraform/infrastructure
    terraform destroy
    ```