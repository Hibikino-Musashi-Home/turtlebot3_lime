#!/usr/bin/env python3
#
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
# Authors: Tomoaki Fujino

import os

from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    ros_distro = os.environ.get('ROS_DISTRO')

    if ros_distro == 'humble':
        cmd_vel_topic = 'cmd_vel_unstamped'
    else:
        cmd_vel_topic = 'cmd_vel'

    controller_manager_config = PathJoinSubstitution(
        [
            FindPackageShare('turtlebot3_lime_hardware'),
            'config',
            'hardware_controller_manager.yaml',
        ]
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager',
            '/controller_manager',
            '--param-file',
            controller_manager_config,
        ],
        output='screen',
    )

    diff_drive_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'diff_drive_controller',
            '--controller-manager',
            '/controller_manager',
            '--param-file',
            controller_manager_config,
            '--controller-ros-args',
            (
                f'--ros-args '
                f'--remap /diff_drive_controller/{cmd_vel_topic}:=/cmd_vel '
                f'--remap /diff_drive_controller/odom:=/odom'
            ),
        ],
        output='screen',
    )

    arm_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'arm_controller',
            '--controller-manager',
            '/controller_manager',
            '--param-file',
            controller_manager_config,
        ],
        output='screen',
    )

    gripper_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'gripper_controller',
            '--controller-manager',
            '/controller_manager',
            '--param-file',
            controller_manager_config,
        ],
        output='screen',
    )

    imu_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'imu_broadcaster',
            '--controller-manager',
            '/controller_manager',
            '--param-file',
            controller_manager_config,
            '--controller-ros-args',
            '--ros-args --remap /imu_broadcaster/imu:=/imu',
        ],
        output='screen',
    )

    if ros_distro != 'humble':
        battery_state_broadcaster_spawner = Node(
            package='controller_manager',
            executable='spawner',
            arguments=[
                'battery_state_broadcaster',
                '--controller-manager',
                '/controller_manager',
                '--param-file',
                controller_manager_config,
                '--controller-ros-args',
                '--ros-args --remap /battery_state_broadcaster/battery_state:=/battery_state',
            ],
            output='screen',
        )

    controller_spawners = [
        diff_drive_controller_spawner,
        imu_broadcaster_spawner,
        arm_controller_spawner,
        gripper_controller_spawner,
    ]

    if ros_distro != 'humble':
        controller_spawners.insert(
            2,
            battery_state_broadcaster_spawner,
        )

    start_controllers = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=controller_spawners,
        )
    )

    ld = LaunchDescription()

    ld.add_action(joint_state_broadcaster_spawner)
    ld.add_action(start_controllers)

    return ld
