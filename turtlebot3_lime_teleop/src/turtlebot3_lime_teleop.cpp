// Copyright 2022 ROBOTIS CO., LTD.
// Copyright 2026 Hibikino-Musashi@Home
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// Author: Hye-jong KIM, Sungho Woo
// Modified Date: January 6th, 2025
// Modified Contents: Number of axes changed to 6 axes
// Modified Authors: Masaya Shoji, Keisuke Nagashima
// Modified Contents:
//   Added ROS 2 Humble and Jazzy support for MoveIt Servo and keyboard auto-repeat handling
//   for continuous arm joint control
// Modified Authors: Tomoaki Fujino

#include <algorithm>
#include <memory>

#include "turtlebot3_lime_teleop/turtlebot3_lime_teleop.hpp"

// KeyboardReader
KeyboardReader::KeyboardReader()
    : kfd(0) {
    // get the console in raw mode
    tcgetattr(kfd, &cooked);
    struct termios raw;
    memcpy(&raw, &cooked, sizeof(struct termios));
    raw.c_lflag &= ~(ICANON | ECHO);
    // Setting a new line, then end of file
    raw.c_cc[VEOL] = 1;
    raw.c_cc[VEOF] = 2;
    tcsetattr(kfd, TCSANOW, &raw);
}

void KeyboardReader::readOne(char *c) {
    int rc = read(kfd, c, 1);
    if (rc < 0) {
        throw std::runtime_error("read failed");
    }
}

void KeyboardReader::shutdown() {
    tcsetattr(kfd, TCSANOW, &cooked);
}

// KeyboardServo

KeyboardServo::KeyboardServo()
    : publish_joint_(false),
      joint_key_repeating_(false) {
    nh_ = rclcpp::Node::make_shared("servo_keyboard_input");

#ifdef ROS_DISTRO_HUMBLE
    servo_start_client_ =
        nh_->create_client<std_srvs::srv::Trigger>(
            "/servo_node/start_servo");

    servo_stop_client_ =
        nh_->create_client<std_srvs::srv::Trigger>(
            "/servo_node/stop_servo");
#else
    servo_pause_client_ =
        nh_->create_client<std_srvs::srv::SetBool>(
            "/servo_node/pause_servo");

    servo_command_type_client_ =
        nh_->create_client<moveit_msgs::srv::ServoCommandType>(
            "/servo_node/switch_command_type");
#endif

#ifdef ROS_DISTRO_HUMBLE
    base_twist_pub_ =
        nh_->create_publisher<geometry_msgs::msg::Twist>(
            BASE_TWIST_TOPIC, ROS_QUEUE_SIZE);
#else
    base_twist_pub_ =
        nh_->create_publisher<geometry_msgs::msg::TwistStamped>(
            BASE_TWIST_TOPIC, ROS_QUEUE_SIZE);
#endif

    joint_pub_ = nh_->create_publisher<control_msgs::msg::JointJog>(ARM_JOINT_TOPIC, ROS_QUEUE_SIZE);
    client_ = rclcpp_action::create_client<control_msgs::action::GripperCommand>(nh_, "gripper_controller/gripper_cmd");

    cmd_vel_ = geometry_msgs::msg::Twist();
}

KeyboardServo::~KeyboardServo() {
    stop_moveit_servo();
}

int KeyboardServo::keyLoop() {
    char c;

    // Ros Spin
    std::thread{std::bind(&KeyboardServo::spin, this)}.detach();
    connect_moveit_servo();
    start_moveit_servo();

    puts("Reading from keyboard");
    puts("---------------------------");
    puts("Joint Control Keys:");
    puts("  1/q: Joint1 +/-");
    puts("  2/w: Joint2 +/-");
    puts("  3/e: Joint3 +/-");
    puts("  4/r: Joint4 +/-");
    puts("  5/t: Joint5 +/-");
    puts("  6/y: Joint6 +/-");
    puts("Use o|p to open/close the gripper.");
    puts("");
    puts("Command Control Keys:");
    puts("  i: Move up");
    puts("  k: Move down");
    puts("  l: Move right");
    puts("  j: Move left");
    puts("  space bar: Move stop");
    puts("---------------------------");
    puts("'ESC' to quit.\n");

    std::thread{std::bind(&KeyboardServo::pub, this)}.detach();

    RCLCPP_INFO(nh_->get_logger(), "====== command ======\n\n");

    bool servoing = true;
    while (servoing) {
        // get the next event from the keyboard
        try {
            input.readOne(&c);
        } catch (const std::runtime_error &) {
            perror("read():");
            return -1;
        }

        RCLCPP_INFO(nh_->get_logger(), "\x1b[999D\x1b[0K\x1b[3A");
        RCLCPP_INFO(nh_->get_logger(), "input:[%c] value: 0x%02X", c, c);

        switch (c) {
            // Command Control Keys
            case KEYCODE_I:
                cmd_vel_.linear.x =
                    std::min(
                        cmd_vel_.linear.x + BASE_LINEAR_VEL_STEP,
                        BASE_LINEAR_VEL_MAX);
                cmd_vel_.linear.y = 0.0;
                cmd_vel_.linear.z = 0.0;
                RCLCPP_INFO_STREAM(
                    nh_->get_logger(),
                    "\x1b[0K" << "LINEAR VEL : " << cmd_vel_.linear.x);
                break;

            case KEYCODE_K:
                cmd_vel_.linear.x =
                    std::max(
                        cmd_vel_.linear.x - BASE_LINEAR_VEL_STEP,
                        -BASE_LINEAR_VEL_MAX);
                cmd_vel_.linear.y = 0.0;
                cmd_vel_.linear.z = 0.0;
                RCLCPP_INFO_STREAM(
                    nh_->get_logger(),
                    "\x1b[0K" << "LINEAR VEL : " << cmd_vel_.linear.x);
                break;

            case KEYCODE_J:
                cmd_vel_.angular.x = 0.0;
                cmd_vel_.angular.y = 0.0;
                cmd_vel_.angular.z =
                    std::min(
                        cmd_vel_.angular.z + BASE_ANGULAR_VEL_STEP,
                        BASE_ANGULAR_VEL_MAX);
                RCLCPP_INFO_STREAM(
                    nh_->get_logger(),
                    "\x1b[0K" << "ANGULAR VEL : " << cmd_vel_.angular.z);
                break;

            case KEYCODE_L:
                cmd_vel_.angular.x = 0.0;
                cmd_vel_.angular.y = 0.0;
                cmd_vel_.angular.z =
                    std::max(
                        cmd_vel_.angular.z - BASE_ANGULAR_VEL_STEP,
                        -BASE_ANGULAR_VEL_MAX);
                RCLCPP_INFO_STREAM(
                    nh_->get_logger(),
                    "\x1b[0K" << "ANGULAR VEL : " << cmd_vel_.angular.z);
                break;

            case KEYCODE_SPACE:
                cmd_vel_ = geometry_msgs::msg::Twist();
                RCLCPP_INFO_STREAM(
                    nh_->get_logger(),
                    "\x1b[0K" << "STOP base");
                break;

            // Joint Control Keys
            case KEYCODE_1:
                set_joint_command("joint1", ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint1 +");
                break;
            case KEYCODE_2:
                set_joint_command("joint2", ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint2 +");
                break;
            case KEYCODE_3:
                set_joint_command("joint3", ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint3 +");
                break;
            case KEYCODE_4:
                set_joint_command("joint4", ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint4 +");
                break;
            case KEYCODE_5:
                set_joint_command("joint5", ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint5 +");
                break;
            case KEYCODE_6:
                set_joint_command("joint6", ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint6 +");
                break;
            case KEYCODE_Q:
                set_joint_command("joint1", -ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint1 -");
                break;
            case KEYCODE_W:
                set_joint_command("joint2", -ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint2 -");
                break;
            case KEYCODE_E:
                set_joint_command("joint3", -ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint3 -");
                break;
            case KEYCODE_R:
                set_joint_command("joint4", -ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint4 -");
                break;
            case KEYCODE_T:
                set_joint_command("joint5", -ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint5 -");
                break;
            case KEYCODE_Y:
                set_joint_command("joint6", -ARM_JOINT_VEL);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Joint6 -");
                break;
            case KEYCODE_O:
                send_goal(0.019);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Gripper Open");
                break;
            case KEYCODE_P:
                send_goal(-0.010);
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "Gripper Close");
                break;
            case KEYCODE_ESC:
                RCLCPP_INFO_STREAM(nh_->get_logger(), "\x1b[0K" << "quit");
                servoing = false;
                break;
            default:
                RCLCPP_WARN_STREAM(nh_->get_logger(), "\x1b[0K" << "Unassigned input : " << c);
                break;
        }
    }

    return 0;
}

void KeyboardServo::send_goal(float position) {
    auto goal_msg = control_msgs::action::GripperCommand::Goal();
    goal_msg.command.position = position;  // Set position
    goal_msg.command.max_effort = -1.0;    // Set max effort

    auto send_goal_options = rclcpp_action::Client<control_msgs::action::GripperCommand>::SendGoalOptions();
    send_goal_options.result_callback = std::bind(&KeyboardServo::goal_result_callback, this, std::placeholders::_1);

    // RCLCPP_INFO(nh_->get_logger(), "Sending goal");
    client_->async_send_goal(goal_msg, send_goal_options);
}

void KeyboardServo::connect_moveit_servo() {
#ifdef ROS_DISTRO_HUMBLE
    for (int i = 0; i < 10; i++) {
        if (servo_start_client_->wait_for_service(
                std::chrono::seconds(1))) {
            RCLCPP_INFO_STREAM(
                nh_->get_logger(),
                "SUCCESS TO CONNECT SERVO START SERVER");
            break;
        }

        RCLCPP_WARN_STREAM(
            nh_->get_logger(),
            "WAIT TO CONNECT SERVO START SERVER");

        if (i == 9) {
            RCLCPP_ERROR_STREAM(
                nh_->get_logger(),
                "fail to connect moveit_servo. "
                "please launch 'servo.launch' at "
                "'turtlebot3_lime_moveit_config' pkg.");
        }
    }

    for (int i = 0; i < 10; i++) {
        if (servo_stop_client_->wait_for_service(
                std::chrono::seconds(1))) {
            RCLCPP_INFO_STREAM(
                nh_->get_logger(),
                "SUCCESS TO CONNECT SERVO STOP SERVER");
            break;
        }

        RCLCPP_WARN_STREAM(
            nh_->get_logger(),
            "WAIT TO CONNECT SERVO STOP SERVER");

        if (i == 9) {
            RCLCPP_ERROR_STREAM(
                nh_->get_logger(),
                "fail to connect moveit_servo. "
                "please launch 'servo.launch' at "
                "'turtlebot3_lime_moveit_config' pkg.");
        }
    }
#else
    for (int i = 0; i < 10; i++) {
        if (servo_pause_client_->wait_for_service(
                std::chrono::seconds(1))) {
            RCLCPP_INFO_STREAM(
                nh_->get_logger(),
                "SUCCESS TO CONNECT SERVO PAUSE SERVER");
            break;
        }

        RCLCPP_WARN_STREAM(
            nh_->get_logger(),
            "WAIT TO CONNECT SERVO PAUSE SERVER");

        if (i == 9) {
            RCLCPP_ERROR_STREAM(
                nh_->get_logger(),
                "fail to connect moveit_servo. "
                "please launch 'servo.launch' at "
                "'turtlebot3_lime_moveit_config' pkg.");
        }
    }

    for (int i = 0; i < 10; i++) {
        if (servo_command_type_client_->wait_for_service(
                std::chrono::seconds(1))) {
            RCLCPP_INFO_STREAM(
                nh_->get_logger(),
                "SUCCESS TO CONNECT SERVO COMMAND TYPE SERVER");
            break;
        }

        RCLCPP_WARN_STREAM(
            nh_->get_logger(),
            "WAIT TO CONNECT SERVO COMMAND TYPE SERVER");

        if (i == 9) {
            RCLCPP_ERROR_STREAM(
                nh_->get_logger(),
                "fail to connect moveit_servo. "
                "please launch 'servo.launch' at "
                "'turtlebot3_lime_moveit_config' pkg.");
        }
    }
#endif
}

void KeyboardServo::start_moveit_servo() {
    RCLCPP_INFO_STREAM(
        nh_->get_logger(), "call 'moveit_servo' start srv.");

#ifdef ROS_DISTRO_HUMBLE
    auto future = servo_start_client_->async_send_request(
        std::make_shared<std_srvs::srv::Trigger::Request>());

    auto result = future.wait_for(std::chrono::seconds(1));
    if (result == std::future_status::ready) {
        RCLCPP_INFO_STREAM(
            nh_->get_logger(),
            "SUCCESS to start 'moveit_servo'");
        future.get();
    } else {
        RCLCPP_ERROR_STREAM(
            nh_->get_logger(),
            "FAIL to start 'moveit_servo', "
            "execute without 'moveit_servo'");
    }
#else
    auto command_type_request =
        std::make_shared<moveit_msgs::srv::ServoCommandType::Request>();

    command_type_request->command_type =
        moveit_msgs::srv::ServoCommandType::Request::JOINT_JOG;

    auto command_type_future =
        servo_command_type_client_->async_send_request(
            command_type_request);

    auto command_type_result =
        command_type_future.wait_for(std::chrono::seconds(1));

    if (command_type_result != std::future_status::ready) {
        RCLCPP_ERROR_STREAM(
            nh_->get_logger(),
            "FAIL to set 'moveit_servo' command type");
        return;
    }

    auto command_type_response = command_type_future.get();

    if (!command_type_response->success) {
        RCLCPP_ERROR_STREAM(
            nh_->get_logger(),
            "FAIL to set 'moveit_servo' command type");
        return;
    }

    RCLCPP_INFO_STREAM(
        nh_->get_logger(),
        "SUCCESS to set 'moveit_servo' command type to JOINT_JOG");

    auto request =
        std::make_shared<std_srvs::srv::SetBool::Request>();
    request->data = false;

    auto future =
        servo_pause_client_->async_send_request(request);

    auto result = future.wait_for(std::chrono::seconds(1));
    if (result == std::future_status::ready) {
        RCLCPP_INFO_STREAM(
            nh_->get_logger(),
            "SUCCESS to start 'moveit_servo'");
        future.get();
    } else {
        RCLCPP_ERROR_STREAM(
            nh_->get_logger(),
            "FAIL to start 'moveit_servo', "
            "execute without 'moveit_servo'");
    }
#endif
}

void KeyboardServo::stop_moveit_servo() {
    RCLCPP_INFO_STREAM(
        nh_->get_logger(), "call 'moveit_servo' END srv.");

#ifdef ROS_DISTRO_HUMBLE
    auto future = servo_stop_client_->async_send_request(
        std::make_shared<std_srvs::srv::Trigger::Request>());

    auto result = future.wait_for(std::chrono::seconds(1));
    if (result == std::future_status::ready) {
        RCLCPP_INFO_STREAM(
            nh_->get_logger(),
            "SUCCESS to stop 'moveit_servo'");
        future.get();
    }
#else
    auto request =
        std::make_shared<std_srvs::srv::SetBool::Request>();
    request->data = true;

    auto future =
        servo_pause_client_->async_send_request(request);

    auto result = future.wait_for(std::chrono::seconds(1));
    if (result == std::future_status::ready) {
        RCLCPP_INFO_STREAM(
            nh_->get_logger(),
            "SUCCESS to stop 'moveit_servo'");
        future.get();
    }
#endif
}

void KeyboardServo::pub() {
    // Allow enough time for the first keyboard auto-repeat event.
    constexpr auto INITIAL_INPUT_TIMEOUT =
        std::chrono::milliseconds(500);

    // After auto-repeat starts, use a short timeout so that the
    // joint stops quickly when the key is released.
    constexpr auto REPEAT_INPUT_TIMEOUT =
        std::chrono::milliseconds(60);

    while (rclcpp::ok()) {
        bool publish_joint = false;
        control_msgs::msg::JointJog joint_msg;

        {
            std::lock_guard<std::mutex> lock(joint_mutex_);

            if (publish_joint_) {
                const auto now = std::chrono::steady_clock::now();
                const auto elapsed =
                    std::chrono::duration_cast<std::chrono::milliseconds>(
                        now - last_joint_input_time_);

                // Use a longer timeout until keyboard auto-repeat starts.
                // Once auto-repeat is detected, use a shorter timeout
                // to stop the joint quickly after the key is released.
                const auto timeout =
                    joint_key_repeating_
                    ? REPEAT_INPUT_TIMEOUT
                    : INITIAL_INPUT_TIMEOUT;

                if (elapsed < timeout) {
                    joint_msg = joint_msg_;
                    publish_joint = true;
                } else {
                    // Stop publishing when keyboard input stops.
                    joint_msg = joint_msg_;
                    joint_msg.velocities.assign(
                        joint_msg.velocities.size(), 0.0);

                    publish_joint_ = false;
                    joint_key_repeating_ = false;
                    publish_joint = true;
                }
            }
        }

        // Publish outside the mutex to keep the critical section short.
        if (publish_joint) {
            joint_msg.header.stamp = nh_->now();
            joint_msg.header.frame_id = BASE_FRAME_ID;
            joint_pub_->publish(joint_msg);
        }
#ifdef ROS_DISTRO_HUMBLE
        base_twist_pub_->publish(cmd_vel_);
#else
        geometry_msgs::msg::TwistStamped cmd_vel_stamped;
        cmd_vel_stamped.header.stamp = nh_->now();
        cmd_vel_stamped.twist = cmd_vel_;
        base_twist_pub_->publish(cmd_vel_stamped);
#endif
        rclcpp::sleep_for(std::chrono::milliseconds(10));
    }
}

void KeyboardServo::set_joint_command(
    const std::string & joint_name,
    double velocity) {
    std::lock_guard<std::mutex> lock(joint_mutex_);

    const auto now = std::chrono::steady_clock::now();

    // If the same command is received again while it is active,
    // treat the input as keyboard auto-repeat.
    if (publish_joint_ &&
        joint_msg_.joint_names.size() == 1 &&
        joint_msg_.velocities.size() == 1 &&
        joint_msg_.joint_names[0] == joint_name &&
        joint_msg_.velocities[0] == velocity) {
        joint_key_repeating_ = true;
    } else {
        joint_key_repeating_ = false;
    }

    joint_msg_.joint_names.clear();
    joint_msg_.velocities.clear();
    joint_msg_.joint_names.push_back(joint_name);
    joint_msg_.velocities.push_back(velocity);

    last_joint_input_time_ = now;
    publish_joint_ = true;
}

void KeyboardServo::spin() {
    while (rclcpp::ok()) {
        rclcpp::spin_some(nh_);
    }
}