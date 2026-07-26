"""
demo.launch.py
Gazebo Harmonic + ROS 2 Jazzy — Ubuntu 24.04

Classic difference:
  Classic → from launch_ros.actions import Node; gazebo_ros GazeboServer
  Harmonic → ros_gz_sim GzServer / GzClient (or IncludeLaunchDescription)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    pkg_share = get_package_share_directory("gz_ros_tts")
    world_file = os.path.join(pkg_share, "worlds", "tts_demo.sdf")

    # ── Args ──────────────────────────────────────────────────
    tts_engine_arg = DeclareLaunchArgument(
        "tts_engine",
        default_value="espeak",
        description="TTS engine: espeak | festival | piper",
    )

    # ── Launch gz sim (Harmonic) ──────────────────────────────
    # ros_gz_sim provides GzServer / GzClient in Jazzy.
    # We use ExecuteProcess for maximum clarity; alternatively
    # use IncludeLaunchDescription with ros_gz_sim/launch/gz_sim.launch.py
    gz_sim = ExecuteProcess(
        cmd=["gz", "sim", world_file],
        output="screen",
    )

    # ── ros_gz_bridge: relay gz-transport ↔ ROS 2 ─────────────
    # Only needed if you want to echo Gazebo topics in ROS.
    # The TTS plugin uses rclcpp directly, so bridge is optional.
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="ros_gz_bridge",
        arguments=[
            # Example: bridge clock topic
            "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
        ],
        output="screen",
    )

    return LaunchDescription([
        tts_engine_arg,
        gz_sim,
        ros_gz_bridge,
    ])
