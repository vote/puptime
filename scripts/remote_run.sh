#!/bin/bash
# DO NOT EDIT THIS FILE. It is auto-generated from the template in
# ecs/template/remote_run.jsonnet
set -euo pipefail

REGION=${REGION:-us-west-2}
ENVIRONMENT=${ENVIRONMENT:-staging}
DOCKER_REPO_NAME=${DOCKER_REPO_NAME:-puptime}
DEBUG=${DEBUG:-true}
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r ".Account")

if [ $1 ]; then

  echo "Logging into ECR"
  if aws --version | grep -q aws-cli/1; then
    eval $(aws ecr get-login --no-include-email --region $REGION)
  else
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
  fi

fi

echo "Account ID: $ACCOUNT_ID"
export DATABASE_URL=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.database_url | jq '.Parameter["Value"]' -r)
export REDIS_URL=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.redis_url | jq '.Parameter["Value"]' -r)
export SECRET_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.secret_key | jq '.Parameter["Value"]' -r)
export ALLOWED_HOSTS=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.allowed_hosts | jq '.Parameter["Value"]' -r)
export PRIMARY_ORIGIN=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.primary_origin | jq '.Parameter["Value"]' -r)
export DD_API_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name general.datadogkey | jq '.Parameter["Value"]' -r)
export DIGITALOCEAN_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.digitalocean_key | jq '.Parameter["Value"]' -r)
export PROXY_SSH_KEY=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.proxy_ssh_key | jq '.Parameter["Value"]' -r)
export PROXY_SSH_KEY_ID=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.proxy_ssh_key_id | jq '.Parameter["Value"]' -r)
export AWS_PROXY_ROLE_ARN=$(aws ssm get-parameter --region $REGION --with-decryption --name turnout.$ENVIRONMENT.aws_proxy_role_arn | jq '.Parameter["Value"]' -r)

echo "Parameters Acquired"


if aws sts get-caller-identity | grep -q assumed-role; then
  echo 'using EC2 credentials'
else
  AWS_CRED_DETAILS=$(aws sts get-session-token --duration-seconds 86400)
  export AWS_ACCESS_KEY_ID=$(echo $AWS_CRED_DETAILS | jq '.Credentials["AccessKeyId"]' -r)
  export AWS_SECRET_ACCESS_KEY=$(echo $AWS_CRED_DETAILS | jq '.Credentials["SecretAccessKey"]' -r)
  export AWS_DEFAULT_REGION=$REGION
  echo "AWS Credentials Acquired"
fi


if [ $1 ]; then

IMAGE=$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$DOCKER_REPO_NAME:$1

else

echo "Building From Local"
docker build --cache-from voteamerica/puptime-ci-cache:latest --build-arg TAG_ARG=local --build-arg BUILD_ARG=0 -t puptime_full .
IMAGE=puptime_full:latest

fi

echo "Running Image $IMAGE"

if [ "$2" ]; then
  docker run \
    -e DATABASE_URL \
    -e REDIS_URL \
    -e SECRET_KEY \
    -e ALLOWED_HOSTS \
    -e PRIMARY_ORIGIN \
    -e DD_API_KEY \
    -e DIGITALOCEAN_KEY \
    -e PROXY_SSH_KEY \
    -e PROXY_SSH_KEY_ID \
    -e AWS_PROXY_ROLE_ARN \
-e DEBUG=$DEBUG \
-p 8000:8000 \
$IMAGE \
/bin/bash -c "$2"
else
  docker run -i -t \
    -e DATABASE_URL \
    -e REDIS_URL \
    -e SECRET_KEY \
    -e ALLOWED_HOSTS \
    -e PRIMARY_ORIGIN \
    -e DD_API_KEY \
    -e DIGITALOCEAN_KEY \
    -e PROXY_SSH_KEY \
    -e PROXY_SSH_KEY_ID \
    -e AWS_PROXY_ROLE_ARN \
-e DEBUG=$DEBUG \
-p 8000:8000 \
$IMAGE \
/bin/bash
fi
