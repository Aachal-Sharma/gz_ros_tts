#!/bin/bash
# ============================================================
#  install.sh — Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic
#  One-shot setup script
# ============================================================
set -e

echo "=== [1/4] System update ==="
sudo apt update

echo ""
echo "=== [2/4] ROS 2 Jazzy + Gazebo Harmonic packages ==="
# ros-jazzy-ros-gz includes:
#   gz_sim_vendor, gz_plugin_vendor, gz_common_vendor (via transitive deps)
#   ros_gz_bridge, ros_gz_sim
sudo apt install -y \
    ros-jazzy-ros-gz \
    ros-jazzy-ros-gz-bridge \
    ros-jazzy-gz-ros2-control

echo ""
echo "=== [3/4] TTS engines ==="

# Ubuntu 24.04 ships espeak-ng (NOT espeak).
# 'espeak' command is symlinked to espeak-ng.
sudo apt install -y espeak-ng

# Optional: Festival
# sudo apt install -y festival

# Optional: Piper (pip install; needs a voice .onnx file)
# pip install piper-tts

echo ""
echo "=== [4/4] Build gz_ros_tts ==="
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"   # assume src/gz_ros_tts

source /opt/ros/jazzy/setup.bash

cd "$WS_ROOT"
colcon build --packages-select gz_ros_tts --symlink-install
source install/setup.bash

echo ""
echo "=============================="
echo "  Installation complete!"
echo "  Run: ros2 launch gz_ros_tts demo.launch.py"
echo "  Test: ros2 topic pub --once /robot/speak std_msgs/msg/String '{data: \"Hello from Harmonic!\"}'"
echo "=============================="
