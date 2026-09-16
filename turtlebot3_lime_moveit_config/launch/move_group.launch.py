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
#   - Separate use_gazebo from use_sim_time and select OMPL adapters according to ROS_DISTRO.
#   - Load joint limits and pass kinematics under robot_description_kinematics.
#   - Load 3D sensor settings and configure the OctoMap frame and resolution.
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

    moveit_config_dir = get_package_share_directory('turtlebot3_lime_moveit_config')

    # Launch Configurations
    prefix = LaunchConfiguration('prefix')
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_fake_hardware = LaunchConfiguration('use_fake_hardware')
    fake_sensor_commands = LaunchConfiguration('fake_sensor_commands')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Robot Description
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

    # Robot Description Semantic
    robot_description_semantic_path = os.path.join(
        moveit_config_dir,
        'config',
        'turtlebot3_lime.srdf',
    )

    with open(robot_description_semantic_path, 'r') as file:
        robot_description_semantic_config = file.read()

    robot_description_semantic = {
        'robot_description_semantic': robot_description_semantic_config,
    }

    # Robot Description Kinematics
    kinematics_yaml_path = os.path.join(
        moveit_config_dir,
        'config',
        'kinematics.yaml',
    )

    with open(kinematics_yaml_path, 'r') as file:
        kinematics_yaml = yaml.safe_load(file)

    robot_description_kinematics = {
        'robot_description_kinematics': kinematics_yaml,
    }

    # Robot Description Planning
    joint_limits_yaml_path = os.path.join(
        moveit_config_dir,
        'config',
        'joint_limits.yaml',
    )

    with open(joint_limits_yaml_path, 'r') as file:
        joint_limits_yaml = yaml.safe_load(file)

    robot_description_planning = {
        'robot_description_planning': joint_limits_yaml,
    }

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
        moveit_config_dir,
        'config',
        'ompl_planning.yaml',
    )

    with open(ompl_planning_yaml_path, 'r') as file:
        ompl_planning_yaml = yaml.safe_load(file)

    ompl_planning_pipeline_config['move_group'].update(ompl_planning_yaml)

    # Trajectory Execution
    trajectory_execution = {
        'moveit_manage_controllers': True,
        'trajectory_execution.allowed_execution_duration_scaling': 1.2,
        'trajectory_execution.allowed_goal_duration_margin': 0.5,
        'trajectory_execution.allowed_start_tolerance': 0.05,
    }

    # MoveIt Controllers
    moveit_controllers_yaml_path = os.path.join(
        moveit_config_dir,
        'config',
        'moveit_controllers.yaml',
    )

    with open(moveit_controllers_yaml_path, 'r') as file:
        moveit_controllers_yaml = yaml.safe_load(file)

    moveit_controllers = {
        'moveit_simple_controller_manager': moveit_controllers_yaml,
        'moveit_controller_manager': 'moveit_simple_controller_manager/MoveItSimpleControllerManager',
    }

    # 3D Sensors
    sensors_3d_yaml_path = os.path.join(
        moveit_config_dir,
        'config',
        'sensors_3d.yaml',
    )

    with open(sensors_3d_yaml_path, 'r') as file:
        sensors_3d_yaml = yaml.safe_load(file)

    occupancy_map_monitor_parameters = {
        **sensors_3d_yaml,
        'octomap_frame': 'odom',
        'octomap_resolution': 0.05,
    }

    # Planning Scene Monitor Parameters
    planning_scene_monitor_parameters = {
        'publish_planning_scene': True,
        'publish_geometry_updates': True,
        'publish_state_updates': True,
        'publish_transforms_updates': True,
        'publish_robot_description': True,
        'publish_robot_description_semantic': True,
    }

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

    # Move Group
    move_group_node = Node(
        package='moveit_ros_move_group',
        executable='move_group',
        output='screen',
        parameters=[
            robot_description,
            robot_description_semantic,
            robot_description_kinematics,
            robot_description_planning,
            ompl_planning_pipeline_config,
            trajectory_execution,
            moveit_controllers,
            planning_scene_monitor_parameters,
            occupancy_map_monitor_parameters,
            {'use_sim_time': use_sim_time},
        ],
    )
    ld.add_action(move_group_node)

    return ld
