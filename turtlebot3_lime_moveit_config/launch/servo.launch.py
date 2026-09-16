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
#   - Generate the robot description with prefix, Gazebo, and fake hardware xacro arguments.
#   - Replace use_sim with separate use_gazebo and use_sim_time arguments for Servo.
# Modified Maintainers: Fujino Tomoaki

import os

import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command
from launch.substitutions import FindExecutable
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ld = LaunchDescription()

    # Launch Configurations
    prefix = LaunchConfiguration('prefix')
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_fake_hardware = LaunchConfiguration('use_fake_hardware')
    fake_sensor_commands = LaunchConfiguration('fake_sensor_commands')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Launch Arguments
    declare_prefix = DeclareLaunchArgument(
        'prefix',
        default_value='',
        description='Prefix of the joint and link names.',
    )

    declare_use_gazebo = DeclareLaunchArgument(
        'use_gazebo',
        default_value='false',
        description='Use Gazebo Sim ros2_control hardware.',
    )

    declare_use_fake_hardware = DeclareLaunchArgument(
        'use_fake_hardware',
        default_value='false',
        description='Use fake ros2_control hardware.',
    )

    declare_fake_sensor_commands = DeclareLaunchArgument(
        'fake_sensor_commands',
        default_value='false',
        description='Enable fake command interfaces for sensors.',
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true.',
    )

    ld.add_action(declare_prefix)
    ld.add_action(declare_use_gazebo)
    ld.add_action(declare_use_fake_hardware)
    ld.add_action(declare_fake_sensor_commands)
    ld.add_action(declare_use_sim_time)

    # Robot description
    robot_description_content = Command(
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
            'prefix:=',
            prefix,
            ' ',
            'use_gazebo:=',
            use_gazebo,
            ' ',
            'use_fake_hardware:=',
            use_fake_hardware,
            ' ',
            'fake_sensor_commands:=',
            fake_sensor_commands,
        ]
    )
    robot_description = {'robot_description': robot_description_content}

    # Robot description Semantic config
    robot_description_semantic_path = os.path.join(
        get_package_share_directory('turtlebot3_lime_moveit_config'),
        'config',
        'turtlebot3_lime.srdf',
    )
    try:
        with open(robot_description_semantic_path, 'r') as file:
            robot_description_semantic_config = file.read()
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None

    robot_description_semantic = {'robot_description_semantic': robot_description_semantic_config}

    # kinematics yaml
    kinematics_yaml_path = os.path.join(
        get_package_share_directory('turtlebot3_lime_moveit_config'),
        'config',
        'kinematics.yaml',
    )
    with open(kinematics_yaml_path, 'r') as file:
        kinematics_yaml = yaml.safe_load(file)

    # Get parameters for the Servo node
    servo_yaml_path = os.path.join(
        get_package_share_directory('turtlebot3_lime_moveit_config'),
        'config',
        'moveit_servo.yaml',
    )
    try:
        with open(servo_yaml_path, 'r') as file:
            servo_params = {'moveit_servo': yaml.safe_load(file)}
    except EnvironmentError:  # parent of IOError, OSError *and* WindowsError where available
        return None

    # Launch as much as possible in components
    servo_node = Node(
        package='moveit_servo',
        executable='servo_node_main',
        parameters=[
            {'use_gazebo': use_gazebo},
            {'use_sim_time': use_sim_time},
            servo_params,
            robot_description,
            robot_description_semantic,
            kinematics_yaml,
        ],
    )
    ld.add_action(servo_node)

    return ld
