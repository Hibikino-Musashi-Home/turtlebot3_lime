#!/usr/bin/env python3
#
# Copyright 2022 ROBOTIS CO., LTD.
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
# Author: Darby Lim
# Modified Contents:
#   - Replace base.launch.py with separate robot state publisher and controller spawner launches.
#   - Start ros2_control_node with the controller configuration from turtlebot3_lime_hardware.
#   - Fix fake hardware mode, default fake_sensor_commands to false, and remove the Raspberry Pi check.
#   - Remove the start_rviz, prefix, and use_fake_hardware launch arguments.
# Modified Maintainers: Tomoaki Fujino

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch.substitutions import FindExecutable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch.substitutions import ThisLaunchFileDir
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ld = LaunchDescription()

    # Launch Configurations
    fake_sensor_commands = LaunchConfiguration('fake_sensor_commands')

    # Launch Arguments
    declare_fake_sensor_commands = DeclareLaunchArgument(
        'fake_sensor_commands',
        default_value='false',
        description='Enable fake command interfaces for sensors.',
    )

    ld.add_action(declare_fake_sensor_commands)

    urdf_file = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [
                    FindPackageShare('turtlebot3_lime_description'),
                    'urdf',
                    'turtlebot3_lime.urdf.xacro',
                ]
            ),
            ' ',
            'use_gazebo:=false',
            ' ',
            'use_fake_hardware:=true',
            ' ',
            'fake_sensor_commands:=',
            fake_sensor_commands,
        ]
    )

    controller_manager_config = PathJoinSubstitution(
        [
            FindPackageShare('turtlebot3_lime_hardware'),
            'config',
            'hardware_controller_manager.yaml',
        ]
    )

    robot_state_publisher_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                ThisLaunchFileDir(),
                '/robot_state_publisher.launch.py',
            ]
        ),
        launch_arguments={
            'use_gazebo': 'false',
            'use_fake_hardware': 'true',
            'fake_sensor_commands': fake_sensor_commands,
            'use_sim_time': 'false',
        }.items(),
    )

    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[
            {'robot_description': urdf_file},
            controller_manager_config,
        ],
        output='both',
    )

    controller_spawner_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                ThisLaunchFileDir(),
                '/controller_spawner.launch.py',
            ]
        ),
    )

    ld.add_action(robot_state_publisher_launch)
    ld.add_action(control_node)
    ld.add_action(controller_spawner_launch)

    return ld
