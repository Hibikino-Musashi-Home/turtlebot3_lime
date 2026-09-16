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

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch Configurations
    prefix = LaunchConfiguration('prefix')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    # Launch Arguments
    declare_prefix = DeclareLaunchArgument(
        'prefix',
        default_value='',
        description='Prefix of the joint and link names.',
    )

    declare_x_pose = DeclareLaunchArgument(
        'x_pose',
        default_value='-2.0',
        description='Initial x position of the robot.',
    )

    declare_y_pose = DeclareLaunchArgument(
        'y_pose',
        default_value='-0.5',
        description='Initial y position of the robot.',
    )

    declare_z_pose = DeclareLaunchArgument(
        'z_pose',
        default_value='0.01',
        description='Initial z position of the robot.',
    )

    declare_roll = DeclareLaunchArgument(
        'roll',
        default_value='0.0',
        description='Initial roll orientation of the robot.',
    )

    declare_pitch = DeclareLaunchArgument(
        'pitch',
        default_value='0.0',
        description='Initial pitch orientation of the robot.',
    )

    declare_yaw = DeclareLaunchArgument(
        'yaw',
        default_value='0.0',
        description='Initial yaw orientation of the robot.',
    )

    # Gazebo Sim
    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py',
                ]
            )
        ),
        launch_arguments={
            'gz_args': [
                '-r -s -v2 ',
                PathJoinSubstitution(
                    [
                        FindPackageShare('turtlebot3_lime_gazebo'),
                        'worlds',
                        'turtlebot3_house.world',
                    ]
                ),
            ],
            'on_exit_shutdown': 'true',
        }.items(),
    )

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare('ros_gz_sim'),
                    'launch',
                    'gz_sim.launch.py',
                ]
            )
        ),
        launch_arguments={
            'gz_args': '-g -v2 ',
        }.items(),
    )

    # Robot state publisher
    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare('turtlebot3_lime_gazebo'),
                    'launch',
                    'robot_state_publisher.launch.py',
                ]
            )
        ),
        launch_arguments={
            'prefix': prefix,
        }.items(),
    )

    # Spawn TurtleBot3 Lime
    spawn_turtlebot_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare('turtlebot3_lime_gazebo'),
                    'launch',
                    'spawn_turtlebot3_lime.launch.py',
                ]
            )
        ),
        launch_arguments={
            'x_pose': x_pose,
            'y_pose': y_pose,
            'z_pose': z_pose,
            'roll': roll,
            'pitch': pitch,
            'yaw': yaw,
        }.items(),
    )

    # Gazebo Sim resource path
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.pathsep.join(
            [
                os.path.dirname(
                    get_package_share_directory('turtlebot3_lime_gazebo')
                ),
                os.path.dirname(
                    get_package_share_directory('turtlebot3_lime_description')
                ),
                os.path.dirname(
                    get_package_share_directory('realsense2_description')
                ),
            ]
        ),
    )

    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_prefix)
    ld.add_action(declare_x_pose)
    ld.add_action(declare_y_pose)
    ld.add_action(declare_z_pose)
    ld.add_action(declare_roll)
    ld.add_action(declare_pitch)
    ld.add_action(declare_yaw)

    # Add the commands to the launch description
    ld.add_action(set_env_vars_resources)
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(spawn_turtlebot_cmd)

    return ld
