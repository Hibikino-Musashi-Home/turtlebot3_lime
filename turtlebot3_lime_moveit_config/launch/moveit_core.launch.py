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
#   - Add prefix and use_rviz arguments and make the RViz launch conditional.
#   - Pass explicit real hardware and wall clock settings to RViz and move_group.
#   - Resolve included launch files relative to this launch file.
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

    ld.add_action(declare_prefix)
    ld.add_action(declare_use_rviz)

    # RViz
    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_dir, '/moveit_rviz.launch.py']),
        launch_arguments={
            'prefix': prefix,
            'use_gazebo': 'false',
            'use_fake_hardware': 'false',
            'fake_sensor_commands': 'false',
            'use_sim_time': 'false',
        }.items(),
        condition=IfCondition(use_rviz),
    )
    ld.add_action(rviz_launch)

    # move_group
    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([launch_dir, '/move_group.launch.py']),
        launch_arguments={
            'prefix': prefix,
            'use_gazebo': 'false',
            'use_fake_hardware': 'false',
            'fake_sensor_commands': 'false',
            'use_sim_time': 'false',
        }.items(),
    )
    ld.add_action(move_group_launch)

    return ld
