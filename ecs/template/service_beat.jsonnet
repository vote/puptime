local datadogContainers = import 'include/datadog_containers.libsonnet';
local puptimeContainer = import 'include/puptime_container.libsonnet';
local env = std.extVar('env');
local capitalEnv = std.asciiUpper(env[0]) + env[1:];
local cpu = std.extVar('cpu');
local memory = std.extVar('memory');

{
  executionRoleArn: 'arn:aws:iam::719108811834:role/Puptime-ECS-' + capitalEnv,
  taskRoleArn: 'arn:aws:iam::719108811834:role/Puptime-ECS-' + capitalEnv + '-TaskRole',
  containerDefinitions: [
    puptimeContainer.common('puptimebeat', 'celerybeat', '/app/ops/beat_health.sh || exit 1') + {
      name: 'beat',
      command: ['/app/ops/beat_launch.sh'],
    },
  ] + datadogContainers.for_env(env),
  memory: '2048',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '1024',
}
