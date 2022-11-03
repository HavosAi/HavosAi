# HavosAi

## Local run

Local inference pipeline run via notebook, for example for can refer to `notebooks/Sample data processing.ipynb`

## AWS Sagemaker pipeline

Sagemaker pipeline is an inference pipeline, all models are trained locally and then stored in S3.
In S3 except models, we store input data, all aditional data (e.g. mappings) and ootput.

Pipeline assummes that we specify input file (csv) which contains `title` and `abstract`.
<br>

* Code for building AWS Sagemaker pipeline is stored in `aws_pipeline/create_pipeline.ipynb`.
* Within `aws_pipeline/create_pipeline.ipynb` notebook we create Docker file, build docker and push it to AWS ECR (Elactic Container Registry). Docker file can be found in the root and called `SageMaker_Pipeline.Dockerfile`.
* Apart from it we define each step with input, output and processing script. Then they are united under one pipeline and pipeline is registered.
* Script for each step is created in `aws_pipeline/create_pipeline_steps.ipynb`.

<br>
Pipeline has a linear structure and each step takes as input config file where defined running flag for each step. Inside each step this flag is checked, if it False (no need to run) we just return input dataframe. Each step saves the intermidiate results in AWS, it comes in handy if we want to rerun pipeline starting from particular step. 
