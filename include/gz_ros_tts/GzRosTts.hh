#pragma once

// ============================================================
//  GzRosTts.hh
//  Gazebo Harmonic (gz-sim 8) + ROS 2 Jazzy — Ubuntu 24.04
//
//  NOTE: Zero Gazebo Classic headers here.
//  Uses pure gz-sim System plugin interface.
// ============================================================

#include <memory>

// gz-sim System interface  (NOT gazebo/ModelPlugin.hh)
#include <gz/sim/System.hh>

namespace gz_ros_tts
{

class GzRosTtsPrivate;   // forward-declare PIMPL

/// \brief Gazebo Harmonic TTS System Plugin
///
/// Subscribes to a ROS 2 std_msgs/msg/String topic and speaks
/// the received text using an offline TTS engine
/// (espeak-ng / festival / piper).
///
/// SDF snippet inside <model>:
/// \code{.xml}
///   <plugin filename="gz_ros_tts" name="gz_ros_tts::GzRosTts">
///     <topic>/robot/speak</topic>
///     <tts_engine>espeak</tts_engine>
///     <voice>en</voice>
///     <rate>150</rate>
///   </plugin>
/// \endcode
class GzRosTts
  : public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
{
public:
  GzRosTts();
  ~GzRosTts() override;

  /// Called once when the plugin is loaded.
  void Configure(
    const gz::sim::Entity & _entity,
    const std::shared_ptr<const sdf::Element> & _sdf,
    gz::sim::EntityComponentManager & _ecm,
    gz::sim::EventManager & _eventMgr) override;

  /// Called every simulation step — checks pending speech queue.
  void PreUpdate(
    const gz::sim::UpdateInfo & _info,
    gz::sim::EntityComponentManager & _ecm) override;

private:
  std::unique_ptr<GzRosTtsPrivate> impl_;
};

}  // namespace gz_ros_tts
