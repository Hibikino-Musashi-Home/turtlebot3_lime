#ifndef TURTLEBOT3_LIME_TELEOP__TURTLEBOT3_LIME_TELEOP_HPP_
#define TURTLEBOT3_LIME_TELEOP__TURTLEBOT3_LIME_TELEOP_HPP_

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_action/rclcpp_action.hpp>
#include <std_srvs/srv/trigger.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <control_msgs/msg/joint_jog.hpp>
#include <control_msgs/msg/gripper_command.hpp>
#include <control_msgs/action/gripper_command.hpp>

#ifndef ROS_DISTRO_HUMBLE
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <std_srvs/srv/set_bool.hpp>
#include <moveit_msgs/srv/servo_command_type.hpp>
#endif

#include <signal.h>
#include <stdio.h>
#include <termios.h>
#include <unistd.h>

#include <chrono>
#include <mutex>
#include <string>

// Define used keys
#define KEYCODE_1 0x31
#define KEYCODE_2 0x32
#define KEYCODE_3 0x33
#define KEYCODE_4 0x34
#define KEYCODE_5 0x35
#define KEYCODE_6 0x36
#define KEYCODE_Q 0x71
#define KEYCODE_W 0x77
#define KEYCODE_E 0x65
#define KEYCODE_R 0x72
#define KEYCODE_T 0x74
#define KEYCODE_Y 0x79

#define KEYCODE_O 0x6F
#define KEYCODE_P 0x70

#define KEYCODE_J 0x6A
#define KEYCODE_K 0x6B
#define KEYCODE_L 0x6C
#define KEYCODE_I 0x69
#define KEYCODE_SPACE 0x20
#define KEYCODE_ESC 0x1B

// Some constants used in the Servo Teleop demo
const char BASE_TWIST_TOPIC[] = "cmd_vel";
const char ARM_JOINT_TOPIC[] = "/servo_node/delta_joint_cmds";
const char GRIPPER_TOPIC[] = "/gripper_controller/gripper_cmd";

const size_t ROS_QUEUE_SIZE = 10;
const double BASE_LINEAR_VEL_MAX = 0.483;  // m/s
const double BASE_LINEAR_VEL_STEP = 0.02;  // m/s

const double BASE_ANGULAR_VEL_MAX = 3.28;  // rad/s
const double BASE_ANGULAR_VEL_STEP = 0.2;  // rad/s
const char BASE_FRAME_ID[] = "base_link";

const double ARM_JOINT_VEL = 1.0;  // rad/s

// A class for reading the key inputs from the terminal
class KeyboardReader
{
public:
  KeyboardReader();
  void readOne(char * c);
  void shutdown();

private:
  int kfd;
  struct termios cooked;
};

// Converts key-presses to Twist or Jog commands for Servo, in lieu of a controller
class KeyboardServo
{
public:
  KeyboardServo();
  ~KeyboardServo();
  int keyLoop();

  void connect_moveit_servo();
  void start_moveit_servo();
  void stop_moveit_servo();
  void send_goal(float position);
private:

  void spin();
  void pub();
  void set_joint_command(const std::string & joint_name, double velocity);

  bool publish_joint_;
  bool joint_key_repeating_;

  std::chrono::steady_clock::time_point last_joint_input_time_;

  std::mutex joint_mutex_;
  std::mutex cmd_vel_mutex_;

  rclcpp::Node::SharedPtr nh_;

  rclcpp_action::Client<control_msgs::action::GripperCommand>::SharedPtr client_;

#ifdef ROS_DISTRO_HUMBLE
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr servo_start_client_;
  rclcpp::Client<std_srvs::srv::Trigger>::SharedPtr servo_stop_client_;
#else
  rclcpp::Client<std_srvs::srv::SetBool>::SharedPtr servo_pause_client_;
  rclcpp::Client<moveit_msgs::srv::ServoCommandType>::SharedPtr servo_command_type_client_;
#endif

#ifdef ROS_DISTRO_HUMBLE
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr base_twist_pub_;
#else
    rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr base_twist_pub_;
#endif
  rclcpp::Publisher<control_msgs::msg::JointJog>::SharedPtr joint_pub_;

  geometry_msgs::msg::Twist cmd_vel_;
  control_msgs::msg::JointJog joint_msg_;
  control_msgs::msg::GripperCommand gripper_cmd_;

  void goal_result_callback(const rclcpp_action::ClientGoalHandle<control_msgs::action::GripperCommand>::WrappedResult& result)
  {
    switch (result.code)
    {
      case rclcpp_action::ResultCode::SUCCEEDED:
        break;
      case rclcpp_action::ResultCode::ABORTED:
        break;
      case rclcpp_action::ResultCode::CANCELED:
        break;
      default:
        break;
    }
  }
};

KeyboardReader input;

void quit(int sig)
{
  (void)sig;
  input.shutdown();
  rclcpp::shutdown();
  exit(0);
}

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  KeyboardServo keyboard_servo;

  signal(SIGINT, quit);

  int rc = keyboard_servo.keyLoop();

  input.shutdown();
  rclcpp::shutdown();

  return rc;
}

#endif  // TURTLEBOT3_LIME_TELEOP__TURTLEBOT3_LIME_TELEOP_HPP_