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
# Author: Tomoaki Fujino

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
    publish_frequency = LaunchConfiguration('publish_frequency')

    # Launch Arguments
    declare_prefix = DeclareLaunchArgument(
        'prefix',
        default_value='',
        description='Prefix of the joint and link names.',
    )

    declare_publish_frequency = DeclareLaunchArgument(
        'publish_frequency',
        default_value='30.0',
        description='Frequency at which joint states are published to TF.',
    )

    ld.add_action(declare_prefix)
    ld.add_action(declare_publish_frequency)

    # Robot description
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name='xacro')]),
            ' ',
            PathJoinSubstitution(
                [
                    FindPackageShare('turtlebot3_lime_gazebo'),
                    'urdf',
                    'turtlebot3_lime.urdf.xacro',
                ]
            ),
            ' ',
            'prefix:=',
            prefix,
        ]
    )
    robot_description = {'robot_description': robot_description_content}

    # Robot state publisher
    rsp_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        respawn=True,
        output='screen',
        parameters=[
            robot_description,
            {'publish_frequency': publish_frequency},
            {'use_sim_time': True},
        ],
    )
    ld.add_action(rsp_node)

    return ld
