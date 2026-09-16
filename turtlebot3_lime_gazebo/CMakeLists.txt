################################################################################
# Set minimum required version of cmake, project name and compile options
################################################################################
cmake_minimum_required(VERSION 3.8)
project(turtlebot3_lime_gazebo)

################################################################################
# Find ament packages and libraries for ament and system dependencies
################################################################################
find_package(ament_cmake REQUIRED)

################################################################################
# Install
################################################################################
install(
  DIRECTORY
    config
    launch
    models
    urdf
    worlds
  DESTINATION share/${PROJECT_NAME}/
)

################################################################################
# Macro for ament package
################################################################################
ament_package()
