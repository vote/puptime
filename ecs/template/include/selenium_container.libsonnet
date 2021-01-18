{
  for_env(env)::
    [
      {
        image: 'selenium/standalone-chrome:3.141.59-20200525',
        name: 'selenium',
        essential: true,
        dependsOn: [
          {
            containerName: 'log_router',
            condition: 'START',
          },
        ],
        portMappings: [
          {
            containerPort: 4444,
          },
        ],
        logConfiguration: {
          logDriver: 'awsfirelens',
          options: {
            Name: 'datadog',
            host: 'http-intake.logs.datadoghq.com',
            dd_service: 'uptime-datadog',
            dd_source: 'selenium',
            dd_message_key: 'log',
            dd_tags: 'env:' + env,
            TLS: 'on',
            Host: 'http-intake.logs.datadoghq.com',
            provider: 'ecs',
          },
          secretOptions: [
            {
              valueFrom: 'arn:aws:ssm:us-west-2:719108811834:parameter/general.datadogkey',
              name: 'apikey',
            },
          ],
        },
      },
    ],
}
