i2btech.ops.cwdashboard
=======================

Create AWS Cloudwatch Dashboards

Requirements
------------

- AWS Command Line Interface installed, it's used to create Cloudwatch dashboard using a JSON file

Role Variables
--------------

- `dashboard_name`: Dashboard name
- `dashboard_region`: Region where resouces are located
- `dashboard_metrics.ecs.cluster`: Name of ECS Cluster that will be monitored
- `dashboard_metrics.ecs.services.name`: Name of ECS services that run inside ECS Cluster
- `dashboard_metrics.ecs.services.label`: Label of ECS services that will be used in the graph
- `dashboard_metrics.rds`: List of DB identifier that will be monitored
- `dashboard_metrics.alb`: List of resource ID of ALB that will be monitored (app/__name__/__random_id__)
- `dashboard_metrics.redis`: List IDs of Redis clusters that will be monitored
- `dashboard_metrics.nlb`: List of resource ID of NLB that will be monitored (net/__name__/__random_id__)
- `dashboard_metrics.ec2_asg`: List IDs of AutoScalingGroups that will be monitored
- `dashboard_metrics.asg_cpu_credits`: List IDs of AutoScalingGroups that will be monitored

Dependencies
------------

None

Example Playbook
----------------

```yaml
- hosts: localhost
  connection: local
  gather_facts: false
  become: false

  vars_files:

    - vars/vars.yml

  roles:

    - role: i2btech.ops.cwdashboard
      dashboard_name: "{{ doid }}"
      dashboard_region: "{{ aws_region }}"
      dashboard_metrics:
        ecs:
          - cluster: "cluster-name-1"
            services:
              - name: "service-1"
                label: "Service 1"
          - cluster: "cluster-name-2"
            services:
              - name: "service-2"
                label: "Service 2"
        rds:
          - "db-id"
        alb:
          - "app/alb-1/3ggfg4fgf"
          - "app/alb-2/ldkcjih"
        redis:
          - cluster: "cluster-id"
            nodes:
              - name: "001"
              - name: "002"
              - name: "003"
        asg_cpu_credits:
          - "autoscalinggroup-1"
          - "autoscalinggroup-2"
        ec2_asg:
          - "autoscalinggroup-1"
          - "autoscalinggroup-2"
        nlb:
          - "app/alb-1/3ggfg4fgf"
          - "app/alb-2/ldkcjih"
```

License
-------

BSD

Author Information
------------------

IT <it@i2btech.com>

Links
-----

- [json definition](https://docs.aws.amazon.com/AmazonCloudWatch/latest/APIReference/CloudWatch-Dashboard-Body-Structure.html)
- [Cache Redis metrics AWS](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/CacheMetrics.Redis.html)
- [ALB metrics AWS](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html)
- [EC2 metrics AWS](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/viewing_metrics_with_cloudwatch.html)

TODO
---

- improves location of widgets `AutoScalingGroups-CPUCredits`, they need to be place side by side and not one on top of the other.
