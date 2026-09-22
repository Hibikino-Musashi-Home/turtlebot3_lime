cmake_minimum_required(VERSION 3.5)
project(turtlebot3_lime_teleop)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(control_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rclcpp_action REQUIRED)

# ROS 2 distribution
if("$ENV{ROS_DISTRO}" STREQUAL "humble")
  set(ROS_DISTRO_HUMBLE TRUE)
else()
  find_package(moveit_msgs REQUIRED)
endif()

add_executable(teleop_keyboard src/teleop_keyboard.cpp)

if(ROS_DISTRO_HUMBLE)
  target_compile_definitions(
    teleop_keyboard PRIVATE ROS_DISTRO_HUMBLE
  )
else()
  target_compile_definitions(
    teleop_keyboard PRIVATE ROS_DISTRO_JAZZY_OR_LATER
  )
endif()

target_include_directories(teleop_keyboard PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:include>
)

ament_target_dependencies(
  teleop_keyboard
  "rclcpp"
  "geometry_msgs"
  "nav_msgs"
  "control_msgs"
  "sensor_msgs"
  "std_srvs"
  "rclcpp_action"
)

if(NOT ROS_DISTRO_HUMBLE)
  ament_target_dependencies(
    teleop_keyboard
    "moveit_msgs"
  )
endif()

install(TARGETS teleop_keyboard
  DESTINATION lib/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
