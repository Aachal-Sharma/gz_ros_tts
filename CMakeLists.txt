cmake_minimum_required(VERSION 3.22)
project(gz_ros_tts)

# ── C++17 required for gz-sim 8 ──────────────────────────────
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# ════════════════════════════════════════════════════════════
# Dependencies
# Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic
#
# Key difference from Classic:
#   Classic → find_package(gazebo_ros_pkgs)
#   Harmonic → vendor packages (gz_sim_vendor, gz_transport_vendor)
# ════════════════════════════════════════════════════════════

find_package(ament_cmake REQUIRED)

# ── ROS 2 packages ───────────────────────────────────────────
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# ── Gazebo Harmonic via vendor packages ──────────────────────
# gz_sim_vendor  ships gz-sim 8  (Harmonic)
# gz_plugin_vendor ships gz-plugin
# These vendor packages are part of ROS 2 Jazzy — no separate
# apt install needed beyond ros-jazzy-ros-gz
find_package(gz_sim_vendor REQUIRED)
find_package(gz-sim REQUIRED)          # version-free target from vendor

find_package(gz_plugin_vendor REQUIRED)
find_package(gz-plugin REQUIRED)

find_package(gz_common_vendor REQUIRED)
find_package(gz-common REQUIRED)

# ════════════════════════════════════════════════════════════
# Plugin shared library
# ════════════════════════════════════════════════════════════

add_library(${PROJECT_NAME} SHARED
  src/GzRosTts.cc
)

target_include_directories(${PROJECT_NAME} PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

# Link against gz-sim (vendor-provided, version-free targets)
target_link_libraries(${PROJECT_NAME}
  gz-sim::gz-sim            # replaces gazebo::gazebo from Classic
  gz-plugin::gz-plugin      # replaces GZ_REGISTER_MODEL_PLUGIN
  gz-common::gz-common
)

# ROS 2 ament targets
ament_target_dependencies(${PROJECT_NAME}
  rclcpp
  std_msgs
)

# ════════════════════════════════════════════════════════════
# Install
# ════════════════════════════════════════════════════════════

install(TARGETS ${PROJECT_NAME}
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(DIRECTORY include/
  DESTINATION include
)

install(DIRECTORY launch worlds
  DESTINATION share/${PROJECT_NAME}
)

# ── Let gz-sim discover the plugin ────────────────────────────
# This is the Harmonic equivalent of gazebo_ros plugin path setup
ament_environment_hooks(
  "${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in"
)

ament_package()
