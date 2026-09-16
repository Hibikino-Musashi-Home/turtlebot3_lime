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
#   - Add use_sim_time and select OMPL adapters according to ROS_DISTRO.
#   - Load joint limits and pass kinematics under robot_description_kinematics.
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

ROS_DISTRO = os.environ.get('ROS_DISTRO')


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
        default_value='false',
        description='Use simulation clock if true.',
    )

    ld.add_action(declare_prefix)
    ld.add_action(declare_use_gazebo)
    ld.add_action(declare_use_fake_hardware)
    ld.add_action(declare_fake_sensor_commands)
    ld.add_action(declare_use_sim_time)

    # Rviz config save file
    rviz_config = os.path.join(
        get_package_share_directory("turtlebot3_lime_moveit_config"),
        "config",
        "moveit.rviz",
    )

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

    robot_description = {
        'robot_description': robot_description_content,
    }

    # Robot description Semantic config
    robot_description_semantic_path = os.path.join(
        get_package_share_directory('turtlebot3_lime_moveit_config'),
        'config',
        'turtlebot3_lime.srdf',
    )
    with open(robot_description_semantic_path, 'r') as file:
        robot_description_semantic_config = file.read()

    robot_description_semantic = {'robot_description_semantic': robot_description_semantic_config}

    # Planning Functionality
    if ROS_DISTRO == 'humble':
        ompl_planning_pipeline_config = {
            'move_group': {
                'planning_plugin': 'ompl_interface/OMPLPlanner',
                'request_adapters': (
                    'default_planner_request_adapters/AddTimeOptimalParameterization '
                    'default_planner_request_adapters/FixWorkspaceBounds '
                    'default_planner_request_adapters/FixStartStateBounds '
                    'default_planner_request_adapters/FixStartStateCollision '
                    'default_planner_request_adapters/FixStartStatePathConstraints'
                ),
                'start_state_max_bounds_error': 0.1,
            }
        }
    else:
        ompl_planning_pipeline_config = {
            'move_group': {
                'planning_plugins': [
                    'ompl_interface/OMPLPlanner',
                ],
                'request_adapters': [
                    'default_planning_request_adapters/ResolveConstraintFrames',
                    'default_planning_request_adapters/ValidateWorkspaceBounds',
                    'default_planning_request_adapters/CheckStartStateBounds',
                    'default_planning_request_adapters/CheckStartStateCollision',
                ],
                'response_adapters': [
                    'default_planning_response_adapters/AddTimeOptimalParameterization',
                    'default_planning_response_adapters/ValidateSolution',
                    'default_planning_response_adapters/DisplayMotionPath',
                ],
                'start_state_max_bounds_error': 0.1,
            }
        }

    ompl_planning_yaml_path = os.path.join(
        get_package_share_directory('turtlebot3_lime_moveit_config'),
        'config',
        'ompl_planning.yaml',
    )
    with open(ompl_planning_yaml_path, 'r') as file:
        ompl_planning_yaml = yaml.safe_load(file)
    ompl_planning_pipeline_config['move_group'].update(ompl_planning_yaml)

    # kinematics yaml
    kinematics_yaml_path = os.path.join(
        get_package_share_directory('turtlebot3_lime_moveit_config'),
        'config',
        'kinematics.yaml',
    )
    with open(kinematics_yaml_path, 'r') as file:
        kinematics_yaml = yaml.safe_load(file)

    robot_description_kinematics = {
        'robot_description_kinematics': kinematics_yaml,
    }

    # Robot description planning
    joint_limits_yaml_path = os.path.join(
        get_package_share_directory('turtlebot3_lime_moveit_config'),
        'config',
        'joint_limits.yaml',
    )
    with open(joint_limits_yaml_path, 'r') as file:
        joint_limits_yaml = yaml.safe_load(file)

    robot_description_planning = {
        'robot_description_planning': joint_limits_yaml,
    }

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='log',
        arguments=['-d', rviz_config],
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            ompl_planning_pipeline_config,
            {'use_sim_time': use_sim_time},
        ],
    )
    ld.add_action(rviz_node)

    return ld
