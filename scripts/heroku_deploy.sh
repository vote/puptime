#!/bin/bash

echo "Logging in to Heroku container registry..."
HEROKU_API_KEY=${HEROKU_API_KEY} /usr/local/bin/heroku container:login
echo "Done."

echo "Building containers and pushing to Heroku..."
HEROKU_API_KEY=${HEROKU_API_KEY} /usr/local/bin/heroku container:push --recursive --app=voteamerica-uptime
echo "Done."

echo "Releasing containers..."
HEROKU_API_KEY=${HEROKU_API_KEY} /usr/local/bin/heroku container:release web worker --app=voteamerica-uptime
echo "Done."

echo "Running migrations..."
HEROKU_API_KEY=${HEROKU_API_KEY} /usr/local/bin/heroku run python manage.py migrate
echo "Done."

echo "Notifiying Sentry..."
curl https://sentry.io/api/0/organizations/${SENTRY_ORG}/releases/ \
  -X POST \
  -H "Authorization: Bearer ${SENTRY_AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "
{
    \"version\": \"turnout@${TRAVIS_TAG}\",
    \"refs\": [{
        \"repository\":\"vote/turnout\",
        \"commit\":\"${TRAVIS_COMMIT}\"
    }],
    \"projects\":[\"turnout\"]
}"
