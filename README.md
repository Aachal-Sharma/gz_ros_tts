# gz_ros_tts — Gazebo Harmonic TTS Plugin

> **Ubuntu 24.04 · ROS 2 Jazzy · Gazebo Harmonic (gz-sim 8)**
> Zero Gazebo Classic dependency.

---

## Platform

| OS | ROS 2 | Gazebo | Status |
|----|-------|--------|--------|
| Ubuntu 24.04 | Jazzy | Harmonic (gz-sim 8) | ✅ Target |

---

## Key Differences from Gazebo Classic

| | Gazebo Classic | Gazebo Harmonic (this pkg) |
|---|---|---|
| Plugin base class | `gazebo::ModelPlugin` | `gz::sim::System` (ISystemConfigure) |
| Plugin registration | `GZ_REGISTER_MODEL_PLUGIN` | `GZ_ADD_PLUGIN` |
| Plugin filename in SDF | `libgazebo_ros_tts.so` | `gz_ros_tts` |
| ROS bridge package | `gazebo_ros_pkgs` | `ros_gz` (vendor packages) |
| CMake dependency | `find_package(gazebo)` | `find_package(gz_sim_vendor)` |
| Plugin path env | `GAZEBO_PLUGIN_PATH` | `GZ_SIM_SYSTEM_PLUGIN_PATH` |
| espeak command | `espeak` | `espeak-ng` (Ubuntu 24.04) |

---

## Install

```bash
chmod +x install.sh
./install.sh
```

Or manually:

```bash
sudo apt install ros-jazzy-ros-gz espeak-ng

cd ~/ros2_ws
colcon build --packages-select gz_ros_tts
source install/setup.bash
```

---

## Usage

### 1. Launch the demo world

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch gz_ros_tts demo.launch.py
```

### 2. Make the robot speak

```bash
# English
ros2 topic pub --once /robot/speak std_msgs/msg/String \
  '{data: "Hello, I am a Harmonic robot!"}'

# Hindi (espeak-ng ke saath)
ros2 topic pub --once /robot/speak std_msgs/msg/String \
  '{data: "Namaste, main robot hoon"}'
```

### 3. Python example

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class RobotVoice(Node):
    def __init__(self):
        super().__init__('robot_voice')
        self.pub = self.create_publisher(String, '/robot/speak', 10)

    def say(self, text: str):
        msg = String()
        msg.data = text
        self.pub.publish(msg)
```

---

## SDF Plugin Block (your URDF/SDF)

```xml
<model name="my_robot">
  <!-- ... links ... -->

  <plugin
    filename="gz_ros_tts"
    name="gz_ros_tts::GzRosTts">
    <topic>/robot/speak</topic>
    <tts_engine>espeak</tts_engine>   <!-- espeak | festival | piper -->
    <voice>en</voice>                  <!-- en, hi, fr, de, es ... -->
    <rate>150</rate>                   <!-- words per minute -->
  </plugin>
</model>
```

---

## TTS Engines

| Engine | Quality | Ubuntu 24.04 Install |
|--------|---------|----------------------|
| espeak-ng | Fast | `sudo apt install espeak-ng` |
| festival | Medium | `sudo apt install festival` |
| piper | Best | `pip install piper-tts` |

> **Note:** Ubuntu 24.04 ships `espeak-ng`, not `espeak`.
> The plugin automatically calls `espeak-ng` when engine is set to `espeak`.

---

## Plugin Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `topic` | `/robot/speak` | ROS 2 topic (std_msgs/String) |
| `tts_engine` | `espeak` | espeak / festival / piper |
| `voice` | `en` | Language/voice code |
| `rate` | `150` | Words per minute |

---

## Package Structure

```
gz_ros_tts/
├── include/gz_ros_tts/
│   └── GzRosTts.hh       # gz::sim::System interface
├── src/
│   └── GzRosTts.cc       # ISystemConfigure + ISystemPreUpdate
├── launch/
│   └── demo.launch.py    # ros_gz_sim launch (NOT gazebo_ros)
├── worlds/
│   └── tts_demo.sdf      # Harmonic SDF world (sdf version="1.9")
├── hooks/
│   └── gz_ros_tts.dsv.in # GZ_SIM_SYSTEM_PLUGIN_PATH hook
├── CMakeLists.txt         # gz_sim_vendor + gz_plugin_vendor
├── package.xml            # Jazzy deps, no gazebo_ros_pkgs
├── install.sh
└── README.md
```

---

## License

Apache-2.0
