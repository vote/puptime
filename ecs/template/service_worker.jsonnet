local datadogContainers = import 'include/datadog_containers.libsonnet';
local puptimeContainer = import 'include/puptime_container.libsonnet';
local seleniumContainer = import 'include/selenium_container.libsonnet';
local env = std.extVar('env');
local capitalEnv = std.asciiUpper(env[0]) + env[1:];
local cpu = std.extVar('cpu');
local memory = std.extVar('memory');

{
  executionRoleArn: 'arn:aws:iam::719108811834:role/Uptime-ECS-General',
  taskRoleArn: 'arn:aws:iam::719108811834:role/Uptime-ECS-General-TaskRole',
  containerDefinitions: [
    puptimeContainer.common('puptimeworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'worker',
      command: ['/app/ops/worker_launch.sh', 'default,usvf'],
    },
  ] + seleniumContainer.for_env(env) + datadogContainers.for_env(env),
  memory: '4096',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '1024',
}
