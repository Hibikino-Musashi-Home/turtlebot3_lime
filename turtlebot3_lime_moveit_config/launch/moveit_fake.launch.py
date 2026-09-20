#!/usr/bin/env python3
#
# Copyright 2020 ROBOTIS CO., LTD.
# Copyright 2026 Hibikino-Musashi@Home
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors: Hye-jong KIM
# Modified Contents:
#   - Add prefix, use_rviz, fake_sensor_commands, and use_sim_time arguments.
#   - Pass fake hardware settings to RViz and move_group and make RViz optional.
#   - Remove the embedded fake hardware bringup launch.
#   - Add an option to enable or disable the occupancy map monitor.
# Modified Maintainers: Fujino Tomoaki


from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import ThisLaunchFileDir


def generate_launch_description():
    ld = LaunchDescription()

    launch_dir = ThisLaunchFileDir()

    # Launch Configurations
    prefix = LaunchConfiguration('prefix')
    use_rviz = LaunchConfiguration('use_rviz')
    fake_sensor_commands = LaunchConfiguration('fake_sensor_commands')
    use_occupancy_map_monitor = LaunchConfiguration('use_occupancy_map_monitor')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Launch Arguments
    declare_prefix = DeclareLaunchArgument(
        'prefix',
        default_value='',
        description='Prefix of the joint and link names.',
    )

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Whether to execute RViz2.',
    )

    declare_fake_sensor_commands = DeclareLaunchArgument(
        'fake_sensor_commands',
        default_value='false',
        description='Enable fake command interfaces for sensors.',
    )

    declare_use_occupancy_map_monitor = DeclareLaunchArgument(
        'use_occupancy_map_monitor',
        default_value='false',
        description='Enable the MoveIt occupancy map monitor.',
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true.',
    )


    ld.add_action(declare_prefix)
    ld.add_action(declare_use_rviz)
    ld.add_action(declare_fake_sensor_commands)
    ld.add_action(declare_use_occupancy_map_monitor)
    ld.add_action(declare_use_sim_time)

    # RViz
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_dir, '/moveit_rviz.launch.py']),
        launch_arguments={
            'prefix': prefix,
            'use_gazebo': 'false',
            'use_fake_hardware': 'true',
            'fake_sensor_commands': fake_sensor_commands,
            'use_sim_time': use_sim_time,
        }.items(),
        condition=IfCondition(use_rviz),
    )
    ld.add_action(rviz_launch)

    # Move Group
    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_dir, '/move_group.launch.py']),
        launch_arguments={
            'prefix': prefix,
            'use_gazebo': 'false',
            'use_fake_hardware': 'true',
            'fake_sensor_commands': fake_sensor_commands,
            'use_occupancy_map_monitor': use_occupancy_map_monitor,
            'use_sim_time': use_sim_time,
        }.items(),
    )
    ld.add_action(move_group_launch)

    return ld
