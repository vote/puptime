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
    puptimeContainer.common('puptimeworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'worker',
      command: ['/app/ops/worker_launch.sh', 'default,usvf'],
    },
    puptimeContainer.common('puptimeworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'workerbulk',
      command: ['/app/ops/worker_launch.sh', 'tokens'],
    },
    puptimeContainer.common('puptimeworker', 'celery', '/app/ops/worker_health.sh || exit 1') + {
      name: 'workerhigh',
      command: ['/app/ops/worker_launch.sh', 'high-pri'],
    },
  ] + datadogContainers.for_env(env),
  memory: '4096',
  requiresCompatibilities: ['FARGATE'],
  networkMode: 'awsvpc',
  cpu: '1024',
}
