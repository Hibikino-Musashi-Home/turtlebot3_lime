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
# Maintainers: Tomoaki Fujino

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

ROS_DISTRO = os.environ.get('ROS_DISTRO')


def generate_launch_description():
    use_rviz = LaunchConfiguration('use_rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = LaunchConfiguration('map_yaml_file')
    params_file = LaunchConfiguration('params_file')
    default_bt_xml_filename = LaunchConfiguration('default_bt_xml_filename')
    autostart = LaunchConfiguration('autostart')
    use_composition = LaunchConfiguration('use_composition')
    use_respawn = LaunchConfiguration('use_respawn')

    default_map_yaml_file = PathJoinSubstitution(
        [
            FindPackageShare('turtlebot3_lime_navigation2'),
            'map',
            'turtlebot3_world.yaml',
        ]
    )

    if ROS_DISTRO == 'humble':
        default_params_file = PathJoinSubstitution(
            [
                FindPackageShare('turtlebot3_lime_navigation2'),
                'param',
                ROS_DISTRO,
                'turtlebot3.yaml',
            ]
        )
    else:
        default_params_file = PathJoinSubstitution(
            [
                FindPackageShare('turtlebot3_lime_navigation2'),
                'param',
                'turtlebot3.yaml',
            ]
        )

    default_bt_xml_file = PathJoinSubstitution(
        [
            FindPackageShare('nav2_bt_navigator'),
            'behavior_trees',
            'navigate_w_replanning_and_recovery.xml',
        ]
    )

    nav2_launch_file_dir = PathJoinSubstitution(
        [
            FindPackageShare('nav2_bringup'),
            'launch',
        ]
    )

    rviz_config_file = PathJoinSubstitution(
        [
            FindPackageShare('turtlebot3_lime_navigation2'),
            'rviz',
            'navigation2.rviz',
        ]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'use_rviz',
                default_value='true',
                description='Whether execute rviz2',
            ),
            DeclareLaunchArgument(
                'use_sim_time',
                default_value='false',
                description='Use simulation (Gazebo) clock if true.',
            ),
            DeclareLaunchArgument(
                'map_yaml_file',
                default_value=default_map_yaml_file,
                description='Full path to map file to load',
            ),
            DeclareLaunchArgument(
                'params_file',
                default_value=default_params_file,
                description='Full path to the ROS2 parameters file to use for all launched nodes',
            ),
            DeclareLaunchArgument(
                'default_bt_xml_filename',
                default_value=default_bt_xml_file,
                description='Full path to the behavior tree xml file to use',
            ),
            DeclareLaunchArgument(
                'autostart',
                default_value='true',
                description='Automatically startup the nav2 stack',
            ),
            DeclareLaunchArgument(
                'use_composition',
                default_value='True',
                description='Whether to use composed bringup',
            ),
            DeclareLaunchArgument(
                'use_respawn',
                default_value='false',
                description=(
                    'Whether to respawn if a node crashes. Applied when composition is disabled.'
                ),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource([nav2_launch_file_dir, '/bringup_launch.py']),
                launch_arguments={
                    'map': map_yaml_file,
                    'use_sim_time': use_sim_time,
                    'params_file': params_file,
                    'default_bt_xml_filename': default_bt_xml_filename,
                    'autostart': autostart,
                    'use_composition': use_composition,
                    'use_respawn': use_respawn,
                }.items(),
            ),
            Node(
                package='rviz2',
                executable='rviz2',
                name='rviz2',
                arguments=['-d', rviz_config_file],
                parameters=[
                    {'use_sim_time': use_sim_time},
                ],
                output='screen',
                condition=IfCondition(use_rviz),
            ),
        ]
    )
