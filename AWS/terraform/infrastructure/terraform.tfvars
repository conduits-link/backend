project_name = "noteworthy-llm"
region = "eu-west-1"

# AWS Free Tier allows use of of ml.m4.xlarge or ml.m5.xlarge only (both 16GB memory).

# Estimated LLaMA 2 model specs:
# https://github.com/facebookresearch/llama/issues/79
#
#   7B:  ~13GB file size. 16GB memory.
#
#   13B: ~25GB file size. 
#        16-32GB memory depending on reports.

# Free tier: 50 hours of training
training_instance_type = "ml.m5.xlarge"

# Free tier: 125 hours of inference
inference_instance_type = "ml.m5.xlarge"

# Set to 26 for LLaMA 2 13B.
volume_size_sagemaker = 14 

## Should not be changed with the current folder structure
handler_path  = "../../src/lambda_function"
handler       = "config_lambda.lambda_handler"

