#!/usr/bin/env python3
#
# Copyright 2024 ROBOTIS JAPAN CO., LTD.
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
# Authors: Keisuke Nagashima
# Modified Contents:
#   - Add use_gazebo and use_sim_time arguments for MoveIt and navigation configuration.
#   - Add use_rviz to control MoveIt and navigation RViz launches.
#   - Forward simulation time to MoveIt, navigation, and MoveIt RViz.
# Modified Maintainers: Tomoaki Fujino

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ld = LaunchDescription()

    use_rviz = LaunchConfiguration('use_rviz')
    use_gazebo = LaunchConfiguration('use_gazebo')
    use_occupancy_map_monitor = LaunchConfiguration('use_occupancy_map_monitor')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_use_rviz = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='Launch RViz2 if true.',
    )

    declare_use_gazebo = DeclareLaunchArgument(
        'use_gazebo',
        default_value='false',
        description='Use Gazebo simulation if true.',
    )

    declare_use_occupancy_map_monitor = DeclareLaunchArgument(
        'use_occupancy_map_monitor',
        default_value='false',
        description='Enable the MoveIt occupancy map monitor.',
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true.',
    )

    ld.add_action(declare_use_rviz)
    ld.add_action(declare_use_gazebo)
    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_use_occupancy_map_monitor)

    # Moveit 2 RViz
    moveit_launch_dir = PathJoinSubstitution(
        [FindPackageShare('turtlebot3_lime_moveit_config'), 'launch'],
    )
    moveit_rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([moveit_launch_dir, '/moveit_rviz.launch.py']),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
        condition=IfCondition(use_rviz),
    )
    ld.add_action(moveit_rviz_launch)

    # Moveit 2
    moveit_launch_dir = PathJoinSubstitution(
        [FindPackageShare('turtlebot3_lime_moveit_config'), 'launch'],
    )
    move_group_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([moveit_launch_dir, '/move_group.launch.py']),
        launch_arguments={
            'use_gazebo': use_gazebo,
            'use_fake_hardware': 'false',
            'fake_sensor_commands': 'false',
            'use_occupancy_map_monitor': use_occupancy_map_monitor,
            'use_sim_time': use_sim_time,
        }.items(),
    )
    ld.add_action(move_group_launch)

    # Navigation 2
    nav2_launch_dir = PathJoinSubstitution(
        [FindPackageShare('turtlebot3_lime_navigation2'), 'launch'],
    )
    map_yaml_file = LaunchConfiguration('map_yaml_file')

    nav2_map_file_arg = DeclareLaunchArgument(
        'map_yaml_file',
        default_value=PathJoinSubstitution(
            [
                FindPackageShare('turtlebot3_lime_navigation2'),
                'map',
                'turtlebot3_world.yaml',
            ]
        ),
    )
    ld.add_action(nav2_map_file_arg)

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([nav2_launch_dir, '/navigation2.launch.py']),
        launch_arguments={
            'map_yaml_file': map_yaml_file,
            'use_sim_time': use_sim_time,
            'use_rviz': use_rviz,
        }.items(),
    )

    ld.add_action(nav2_launch)

    return ld
