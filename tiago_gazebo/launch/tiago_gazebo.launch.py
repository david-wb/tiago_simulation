# Copyright (c) 2024 PAL Robotics S.L. All rights reserved.
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

import os
from os import environ, pathsep
from ament_index_python.packages import get_package_prefix

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable

from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

from launch_pal.include_utils import include_scoped_launch_py_description

from launch_ros.actions import Node
from launch_pal.arg_utils import LaunchArgumentsBase
from launch_pal.robot_arguments import TiagoArgs
from dataclasses import dataclass


@dataclass(frozen=True)
class LaunchArguments(LaunchArgumentsBase):

    base_type: DeclareLaunchArgument = TiagoArgs.base_type
    camera_model: DeclareLaunchArgument = TiagoArgs.camera_model
    laser_model: DeclareLaunchArgument = TiagoArgs.laser_model
    has_screen: DeclareLaunchArgument = TiagoArgs.has_screen
    wrist_model: DeclareLaunchArgument = TiagoArgs.wrist_model
    ft_sensor: DeclareLaunchArgument = TiagoArgs.ft_sensor
    end_effector: DeclareLaunchArgument = TiagoArgs.end_effector
    arm_type: DeclareLaunchArgument = TiagoArgs.arm_type

    navigation: DeclareLaunchArgument = DeclareLaunchArgument(
        name='navigation',
        default_value='False',
        description='Specify if launching Navigation2')

    moveit: DeclareLaunchArgument = DeclareLaunchArgument(
        name='moveit',
        default_value='True',
        description='Specify if launching MoveIt 2')

    world_name: DeclareLaunchArgument = DeclareLaunchArgument(
        name='world_name',
        default_value='pal_office',
        description="Specify world name, we'll convert to full path")

    public_sim: DeclareLaunchArgument = DeclareLaunchArgument(
        name='public_sim',
        default_value='False',
        description="Enable public simulation")


def generate_launch_description():

    # Create the launch description and populate
    ld = LaunchDescription()
    launch_arguments = LaunchArguments()

    launch_arguments.add_to_launch_description(ld)

    declare_actions(ld, launch_arguments)

    return ld


def declare_actions(launch_description: LaunchDescription,
                    launch_args: LaunchArguments):
    robot_name = 'tiago'
    packages = ['tiago_description', 'pmb2_description',
                'pal_hey5_description', 'pal_gripper_description',
                'pal_robotiq_description']

    model_path = get_model_paths(packages)

    gazebo_model_path_env_var = SetEnvironmentVariable(
        'GAZEBO_MODEL_PATH', model_path)

    gazebo = include_scoped_launch_py_description(
        pkg_name='pal_gazebo_worlds',
        paths=['launch', 'pal_gazebo.launch.py'],
        env_vars=[gazebo_model_path_env_var],
        launch_arguments={
            "world_name":  launch_args.world_name,
            "model_paths": packages,
            "resource_paths": packages,
        })

    launch_description.add_action(gazebo)

    navigation = include_scoped_launch_py_description(
        pkg_name='tiago_2dnav',
        paths=['launch', 'tiago_nav_bringup.launch.py'],
        condition=IfCondition(LaunchConfiguration('navigation')))

    launch_description.add_action(navigation)

    move_group = include_scoped_launch_py_description(
        pkg_name='tiago_moveit_config',
        paths=['launch', 'move_group.launch.py'],
        launch_arguments={
            "robot_name": robot_name,
            "use_sim_time": 'True'},
        condition=IfCondition(LaunchConfiguration('moveit')))

    launch_description.add_action(move_group)

    robot_spawn = include_scoped_launch_py_description(
        pkg_name='tiago_gazebo',
        paths=['launch', 'tiago_spawn.launch.py'],
        launch_arguments={
            'robot_name': robot_name,
            'base_type': launch_args.base_type}
    )

    launch_description.add_action(robot_spawn)

    tiago_bringup = include_scoped_launch_py_description(
        pkg_name='tiago_bringup', paths=['launch', 'tiago_bringup.launch.py'],
        launch_arguments={
            'use_sim_time': 'True',
            "laser_model": launch_args.laser_model,
            "camera_model": launch_args.camera_model,
            "base_type": launch_args.base_type,
            "wrist_model": launch_args.wrist_model,
            "ft_sensor": launch_args.ft_sensor,
            "end_effector": launch_args.end_effector,
            "has_screen": launch_args.has_screen}
    )

    launch_description.add_action(tiago_bringup)

    tuck_arm = Node(package='tiago_gazebo',
                    executable='tuck_arm.py',
                    emulate_tty=True,
                    output='both')

    launch_description.add_action(tuck_arm)

    return


def get_model_paths(packages_names):
    model_paths = ''
    for package_name in packages_names:
        if model_paths != '':
            model_paths += pathsep

        package_path = get_package_prefix(package_name)
        model_path = os.path.join(package_path, 'share')

        model_paths += model_path

    if 'GAZEBO_MODEL_PATH' in environ:
        model_paths += pathsep + environ['GAZEBO_MODEL_PATH']

    return model_paths


def get_resource_paths(packages_names):
    resource_paths = ''
    for package_name in packages_names:
        if resource_paths != '':
            resource_paths += pathsep

        package_path = get_package_prefix(package_name)
        resource_paths += package_path

    if 'GAZEBO_RESOURCE_PATH' in environ:
        resource_paths += pathsep + environ['GAZEBO_RESOURCE_PATH']

    return resource_paths
