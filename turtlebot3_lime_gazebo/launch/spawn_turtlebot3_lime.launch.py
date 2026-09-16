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
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Launch configuration variables specific to simulation
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    z_pose = LaunchConfiguration('z_pose')
    roll = LaunchConfiguration('roll')
    pitch = LaunchConfiguration('pitch')
    yaw = LaunchConfiguration('yaw')

    # Declare the launch arguments
    declare_x_position_cmd = DeclareLaunchArgument(
        'x_pose',
        default_value='0.0',
        description='Specify the x position of the robot',
    )

    declare_y_position_cmd = DeclareLaunchArgument(
        'y_pose',
        default_value='0.0',
        description='Specify the y position of the robot',
    )

    declare_z_position_cmd = DeclareLaunchArgument(
        'z_pose',
        default_value='0.01',
        description='Specify the z position of the robot',
    )

    declare_roll_cmd = DeclareLaunchArgument(
        'roll',
        default_value='0.0',
        description='Specify the roll orientation of the robot',
    )

    declare_pitch_cmd = DeclareLaunchArgument(
        'pitch',
        default_value='0.0',
        description='Specify the pitch orientation of the robot',
    )

    declare_yaw_cmd = DeclareLaunchArgument(
        'yaw',
        default_value='0.0',
        description='Specify the yaw orientation of the robot',
    )

    # Spawn TurtleBot3 Lime
    start_gazebo_ros_spawner_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name',
            'turtlebot3_lime',
            '-topic',
            'robot_description',
            '-x',
            x_pose,
            '-y',
            y_pose,
            '-z',
            z_pose,
            '-R',
            roll,
            '-P',
            pitch,
            '-Y',
            yaw,
        ],
        output='screen',
    )

    # Get the ros_gz_bridge parameter file
    bridge_params = os.path.join(
        get_package_share_directory('turtlebot3_lime_gazebo'),
        'config',
        'turtlebot3_lime_bridge.yaml',
    )

    # Start ros_gz_bridge
    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ],
        output='screen',
    )

    # Start ros2_control controller spawners
    start_controller_spawner_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare('turtlebot3_lime_gazebo'),
                    'launch',
                    'controller_spawner.launch.py',
                ]
            )
        )
    )

    ld = LaunchDescription()

    start_controllers = RegisterEventHandler(
        OnProcessExit(
            target_action=start_gazebo_ros_spawner_cmd,
            on_exit=[
                start_controller_spawner_cmd,
            ],
        )
    )

    # Declare the launch options
    ld.add_action(declare_x_position_cmd)
    ld.add_action(declare_y_position_cmd)
    ld.add_action(declare_z_position_cmd)
    ld.add_action(declare_roll_cmd)
    ld.add_action(declare_pitch_cmd)
    ld.add_action(declare_yaw_cmd)

    # Add the actions
    ld.add_action(start_gazebo_ros_spawner_cmd)
    ld.add_action(start_gazebo_ros_bridge_cmd)
    ld.add_action(start_controllers)

    return ld
