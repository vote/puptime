#!/bin/bash

pip install awscli

eval $(aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/e6b7u9l0)
docker build --build-arg TAG_ARG=${TRAVIS_TAG} --build-arg BUILD_ARG=${TRAVIS_BUILD_NUMBER} -t puptime .
docker tag puptime:latest public.ecr.aws/e6b7u9l0/puptime:${TRAVIS_TAG}
docker push public.ecr.aws/e6b7u9l0/puptime/puptime:${TRAVIS_TAG}


curl https://sentry.io/api/0/organizations/${SENTRY_ORG}/releases/ \
  -X POST \
  -H "Authorization: Bearer ${SENTRY_AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "
{
    \"version\": \"puptime@${TRAVIS_TAG}\",
    \"refs\": [{
        \"repository\":\"vote/puptime\",
        \"commit\":\"${TRAVIS_COMMIT}\"
    }],
    \"projects\":[\"uptime\"]
}"
