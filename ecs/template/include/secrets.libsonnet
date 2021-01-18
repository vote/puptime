{
  for_env(env)::
    [
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.database_url',
        name: 'DATABASE_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.redis_url',
        name: 'REDIS_URL',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.secret_key',
        name: 'SECRET_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.allowed_hosts',
        name: 'ALLOWED_HOSTS',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.primary_origin',
        name: 'PRIMARY_ORIGIN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/general.datadogkey',
        name: 'DD_API_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.sentry_dsn',
        name: 'SENTRY_DSN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.digitalocean_key',
        name: 'DIGITALOCEAN_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.proxy_ssh_key',
        name: 'PROXY_SSH_KEY',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.proxy_ssh_key_id',
        name: 'PROXY_SSH_KEY_ID',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.aws_proxy_role_arn',
        name: 'AWS_PROXY_ROLE_ARN',
      },
      {
        valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/uptime.' + env + '.snapshot_bucket',
        name: 'SNAPSHOT_BUCKET',
      },
    ],
}
