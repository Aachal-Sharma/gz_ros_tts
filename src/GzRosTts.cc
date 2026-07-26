// ============================================================
//  GzRosTts.cc
//  Gazebo Harmonic (gz-sim 8) + ROS 2 Jazzy — Ubuntu 24.04
//
//  Classic APIs used: NONE
//  Replaces: gazebo::ModelPlugin, gazebo::transport, gazebo_ros
//  Uses:     gz::sim::System, rclcpp subscription
// ============================================================

#include <gz/sim/System.hh>
#include "gz_ros_tts/GzRosTts.hh"

// ── Standard library ────────────────────────────────────────
#include <atomic>
#include <cstdlib>
#include <mutex>
#include <queue>
#include <string>
#include <thread>

// ── gz-sim (Harmonic) ───────────────────────────────────────
// All headers come from gz-sim8, provided via gz_sim_vendor
#include <gz/plugin/Register.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/sim/EventManager.hh>
#include <gz/sim/System.hh>
#include "gz_ros_tts/GzRosTts.hh"
#include <gz/common/Console.hh>

// ── ROS 2 (Jazzy) ───────────────────────────────────────────
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

namespace gz_ros_tts
{

// ============================================================
// Private implementation (PIMPL)
// ============================================================
class GzRosTtsPrivate
{
public:
  // ROS 2
  rclcpp::Node::SharedPtr node_;
  rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_;
  rclcpp::executors::SingleThreadedExecutor::SharedPtr executor_;
  std::thread spin_thread_;

  // TTS config (read from SDF)
  std::string topic_      = "/robot/speak";
  std::string tts_engine_ = "espeak";
  std::string voice_      = "en";
  int         rate_       = 150;

  // Speech queue — callback fills, PreUpdate drains
  std::queue<std::string> speech_queue_;
  std::mutex              queue_mutex_;

  // Prevent overlapping speech calls
  std::atomic<bool> speaking_{false};

  // ── helpers ──────────────────────────────────────────────

  /// Build the shell command for the chosen TTS engine
  std::string BuildCmd(const std::string & text) const
  {
    if (tts_engine_ == "festival") {
      // festival reads from stdin
      return "echo \"" + text + "\" | festival --tts &";
    } else if (tts_engine_ == "piper") {
      // piper-tts: echo text | piper --model <voice>.onnx --output_raw | aplay
      // Users must have the voice model downloaded.
      return "echo \"" + text + "\" | "
             "piper --model " + voice_ + ".onnx --output_raw 2>/dev/null | "
             "aplay -r 22050 -f S16_LE -t raw - &";
    } else {
      // espeak-ng (default) — Ubuntu 24.04 ships espeak-ng, not espeak
      return "espeak-ng -v " + voice_ +
             " -s " + std::to_string(rate_) +
             " \"" + text + "\" &";
    }
  }

  /// Speak a single text string in a detached thread
  void Speak(const std::string & text)
  {
    if (text.empty()) { return; }
    speaking_ = true;
    std::thread([this, text]() {
      std::string cmd = BuildCmd(text);
      gzmsg << "[GzRosTts] Speaking: " << text << "\n";
      std::system(cmd.c_str());   // NOLINT — intentional shell call
      speaking_ = false;
    }).detach();
  }

  /// ROS 2 subscription callback
  void OnSpeakMsg(const std_msgs::msg::String::SharedPtr msg)
  {
    if (msg->data.empty()) { return; }
    std::lock_guard<std::mutex> lock(queue_mutex_);
    speech_queue_.push(msg->data);
    gzmsg << "[GzRosTts] Queued: \"" << msg->data << "\"\n";
  }
};

// ============================================================
// GzRosTts
// ============================================================

GzRosTts::GzRosTts()
: impl_(std::make_unique<GzRosTtsPrivate>())
{}

GzRosTts::~GzRosTts()
{
  // Stop the ROS executor cleanly
  if (impl_->executor_) {
    impl_->executor_->cancel();
  }
  if (impl_->spin_thread_.joinable()) {
    impl_->spin_thread_.join();
  }
}

// ── ISystemConfigure ────────────────────────────────────────
void GzRosTts::Configure(
  const gz::sim::Entity & /*_entity*/,
  const std::shared_ptr<const sdf::Element> & _sdf,
  gz::sim::EntityComponentManager & /*_ecm*/,
  gz::sim::EventManager & /*_eventMgr*/)
{
  // ── 1. Parse SDF parameters ──────────────────────────────
  if (_sdf->HasElement("topic")) {
    impl_->topic_ = _sdf->Get<std::string>("topic");
  }
  if (_sdf->HasElement("tts_engine")) {
    impl_->tts_engine_ = _sdf->Get<std::string>("tts_engine");
  }
  if (_sdf->HasElement("voice")) {
    impl_->voice_ = _sdf->Get<std::string>("voice");
  }
  if (_sdf->HasElement("rate")) {
    impl_->rate_ = _sdf->Get<int>("rate");
  }

  gzmsg << "[GzRosTts] Config:"
        << "  topic="      << impl_->topic_
        << "  engine="     << impl_->tts_engine_
        << "  voice="      << impl_->voice_
        << "  rate="       << impl_->rate_
        << "\n";

  // ── 2. Boot ROS 2 node ───────────────────────────────────
  if (!rclcpp::ok()) {
    // gz-sim may not have called rclcpp::init; do it ourselves.
    rclcpp::init(0, nullptr);
  }

  impl_->node_ = std::make_shared<rclcpp::Node>("gz_ros_tts_node");

  // ── 3. Create subscription ───────────────────────────────
  impl_->sub_ = impl_->node_->create_subscription<std_msgs::msg::String>(
    impl_->topic_,
    rclcpp::QoS(10),
    [this](const std_msgs::msg::String::SharedPtr msg) {
      impl_->OnSpeakMsg(msg);
    });

  // ── 4. Spin the executor in a background thread ──────────
  impl_->executor_ =
    std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
  impl_->executor_->add_node(impl_->node_);

  impl_->spin_thread_ = std::thread([this]() {
    impl_->executor_->spin();
  });

  gzmsg << "[GzRosTts] Subscribed to ROS 2 topic: "
        << impl_->topic_ << "\n";
}

// ── ISystemPreUpdate ─────────────────────────────────────────
void GzRosTts::PreUpdate(
  const gz::sim::UpdateInfo & _info,
  gz::sim::EntityComponentManager & /*_ecm*/)
{
  // Skip while paused or already speaking
  if (_info.paused || impl_->speaking_) { return; }

  std::lock_guard<std::mutex> lock(impl_->queue_mutex_);
  if (!impl_->speech_queue_.empty()) {
    std::string text = impl_->speech_queue_.front();
    impl_->speech_queue_.pop();
    impl_->Speak(text);
  }
}

}  // namespace gz_ros_tts

// ── gz-plugin registration ────────────────────────────────
// This macro replaces GZ_REGISTER_MODEL_PLUGIN from Classic
GZ_ADD_PLUGIN(
  gz_ros_tts::GzRosTts,
  gz::sim::System,
  gz_ros_tts::GzRosTts::ISystemConfigure,
  gz_ros_tts::GzRosTts::ISystemPreUpdate)

GZ_ADD_PLUGIN_ALIAS(gz_ros_tts::GzRosTts, "gz_ros_tts::GzRosTts")
