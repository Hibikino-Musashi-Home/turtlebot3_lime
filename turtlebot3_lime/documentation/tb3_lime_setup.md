# TurtleBot3 Friends: Lime

![TB3 Lime](./img/bg.png)

## Gazebo 環境での動作検証

|                     Gazebo 環境 + Rviz                      |
| :--------------------------------------------------------: |
| ![moveit_navigation](./img/moveit_navigation.gif?raw=true) |

## セットアップ手順（Quick Start Guide）

Lime のベースである [TurtleBot3 with OpenMANIPULATOR](https://emanual.robotis.com/docs/en/platform/turtlebot3/manipulation/) から変更点があります．以下の手順を参考にしてください．

### 1. Jetson Orin Nano の環境設定

#### 1.1. Jetson Orin Nano のセットアップについて

Turtlebot3 Lime を利用するには，Jetson Orin Nano に Jetpack 6.x をインストールする必要があります．

1. Ubuntu 22.04 がインストールされた PC（以下，リモート PC）を用意してください．
2. [SDK Manager](https://developer.nvidia.com/sdk-manager) をインストールしてください．
3. [公式のインストールガイド](https://docs.nvidia.com/sdk-manager/install-with-sdkm-jetson/index.html) に従って，Jetpack 6.x をインストールしてください．

#### 1.2. ROS 2 Humble / Jazzy のインストール

使用する Ubuntu のバージョンに応じて，ROS 2 をインストールします．

| Ubuntu           | ROS 2        |
| ---------------- | ------------ |
| Ubuntu 22.04 LTS | ROS 2 Humble |
| Ubuntu 24.04 LTS | ROS 2 Jazzy  |

ROS 2 のインストール方法については，[ROS 2 Humble 公式インストールガイド](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html) または [ROS 2 Jazzy 公式インストールガイド](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html) を参照してください．

まず，Ubuntu Universe リポジトリが有効になっていることを確認します．

```bash
sudo apt install -y software-properties-common
sudo add-apt-repository universe
```

使用している Ubuntu のバージョンに応じて `ROS_DISTRO` を設定します．

Ubuntu 22.04 LTS の場合：

```bash
export ROS_DISTRO=humble
```

Ubuntu 24.04 LTS の場合：

```bash
export ROS_DISTRO=jazzy
```

ROS 2 の APT リポジトリを追加します．

```bash
sudo apt update && sudo apt install -y curl gnupg lsb-release

sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

ROS 2 Desktop をインストールします．

```bash
sudo apt update
sudo apt install -y ros-${ROS_DISTRO}-desktop

echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

ROS 2 のビルドに必要なツールをインストールします．

```bash
sudo apt install -y python3-colcon-common-extensions python3-pip
```

ワークスペースを作成します．

```bash
mkdir -p ~/turtlebot3_ws/src
cd ~/turtlebot3_ws
colcon build --symlink-install
. install/setup.bash
```

ワークスペースおよび ROS 2 Domain ID を設定します．

```bash
echo '. ~/turtlebot3_ws/install/setup.bash' >> ~/.bashrc
echo 'export ROS_DOMAIN_ID=30 # TURTLEBOT3' >> ~/.bashrc

source ~/.bashrc
```

#### 1.3. Intel RealSense SDK 2.0 のインストール

Intel RealSense SDK 2.0 で CUDA を有効化するために，Jetson Orin Nano でビルドしてインストールします．

```bash
sudo apt install -y git libssl-dev libusb-1.0-0-dev pkg-config libgtk-3-dev
cd ~/Downloads/
git clone https://github.com/IntelRealSense/librealsense.git -b v2.55.1
cd ./librealsense/
sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo cp config/99-realsense-d4xx-mipi-dfu.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
mkdir build && cd build
cmake .. -DBUILD_EXAMPLES=true -DCMAKE_BUILD_TYPE=release -DFORCE_RSUSB_BACKEND=true -DBUILD_WITH_CUDA=true && make -j$(($(nproc)-1)) && sudo make install
```

#### 1.4. Realsense D435i のセットアップ

Realsense D435i 内部のファームウェアのバージョンを Intel RealSense SDK 2.0 のバージョンと合わせる必要があります．

[Realsense 公式サイト](https://dev.realsenseai.com/docs/firmware-releases-d400/) から，
Version-5.16.0.1 を `Downloads` フォルダにダウンロードしてください．

Realsense D435i 内臓ファームウェアを Jetson Orin Nano から書き込みます

```bash
cd ~/Downloads/
unzip ./Signed_Image_UVC_5_16_0_1.zip
rs-fw-update -f ./Signed_Image_UVC_5_16_0_1.bin
```

#### 1.5. realsense-ros のインストール

ROS で Intel Realsense SDK 2.0 を読み込むために，realsense-ros をインストールします．

```bash
cd ~/turtlebot3_ws/src
git clone https://github.com/IntelRealSense/realsense-ros -b 4.55.1
cd ~/turtlebot3_ws
sudo apt install -y python3-rosdep
sudo rosdep init
rosdep update
```

一度，ターミナルに入り直してください．

```bash
cd ~/turtlebot3_ws
rosdep install -i --from-path src --rosdistro $ROS_DISTRO --skip-keys=librealsense2 -y
cd ~/turtlebot3_ws && colcon build --symlink-install && . install/setup.bash
```

#### 1.6. その他の必要な ROS2 パッケージのインストール

その他の必要な ROS2 パッケージをインストールします．

```bash
sudo apt install -y ros-humble-cartographer ros-humble-cartographer-ros ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-dynamixel-sdk ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-gripper-controllers ros-humble-moveit ros-humble-moveit-servo
cd ~/turtlebot3_ws/src
git clone -b humble-devel https://github.com/ROBOTIS-JAPAN-GIT/turtlebot3_lime.git
git clone https://github.com/ldrobotSensorTeam/ldlidar_stl_ros2.git
cd ~/turtlebot3_ws && colcon build --symlink-install && . install/setup.bash
```

#### 1.7. OpenCR に権限を付与する

OpenCR と通信するために，権限を付与します．

```bash
sudo curl -sSL https://raw.githubusercontent.com/ROBOTIS-GIT/turtlebot3/refs/heads/humble/turtlebot3_bringup/script/99-turtlebot3-cdc.rules -o /etc/udev/rules.d/99-turtlebot3-cdc.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

#### 1.8. OpenCR のセットアップ

OpenCR を Jetson Orin Nano を通して，セットアップを行います

```bash
sudo dpkg --add-architecture armhf
sudo apt update
sudo apt install -y libc6:armhf
export OPENCR_PORT=/dev/ttyACM0
export OPENCR_MODEL=lime
cd ~/Downloads/
rm -rf ./opencr_update.tar.bz2
wget https://github.com/ROBOTIS-JAPAN-GIT/OpenCR_jp_custom/releases/download/ros2v1.0.1/opencr_update_jp_custom.tar.bz2
tar -xvf opencr_update_jp_custom.tar.bz2
cd ./opencr_update
./update.sh $OPENCR_PORT $OPENCR_MODEL.opencr
```

### 2. リモート PC の環境設定

#### 2.1. リモート PC のセットアップについて

リモート PC 側にも必要な ROS 2 パッケージや，ドライバをインストールする必要があります．

#### 2.2. ROS 2 Humble のインストール

- ROS 2 がインストールされている場合

  ワークスペースを作成します．

  ```bash
  mkdir -p ~/turtlebot3_ws/src
  cd ~/turtlebot3_ws && colcon build --symlink-install && . install/setup.bash
  ```

  ワークスペースや ROS_DOMAIN を設定します．

  ```bash
  echo '. ~/turtlebot3_ws/install/setup.bash' >> ~/.bashrc
  echo 'export ROS_DOMAIN_ID=30 #TURTLEBOT3' >> ~/.bashrc
  source ~/.bashrc
  ```

- ROS 2 がインストールされていない場合
    <details>

    <summary><a href="#12-ros-2-humble-のインストール">1.2. ROS 2 Humble のインストール</a>と同様です．</summary>
    <a href="[#12-ros-2-humble-のインストール](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debians.html))">ROS 公式のインストールガイド</a>に従って，ROS 2 Humble をインストールします．
    まず，Ubuntu Universe リポジトリが有効になっていることを確認します．

  ```bash
  sudo apt install -y software-properties-common
  sudo add-apt-repository universe
  ```

  ROS 2 Humble をインストールします．

  ```bash
  sudo apt update && sudo apt -y install curl gnupg lsb-release
  sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
  sudo apt update
  sudo apt install -y ros-humble-desktop
  echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
  source ~/.bashrc
  sudo apt install -y python3-colcon-common-extensions python3-pip
  ```

  ワークスペースを作成します．

  ```bash
  mkdir -p ~/turtlebot3_ws/src
  cd ~/turtlebot3_ws && colcon build --symlink-install && . install/setup.bash
  ```

  ワークスペースや ROS_DOMAIN を設定します．

  ```bash
  echo '. ~/turtlebot3_ws/install/setup.bash' >> ~/.bashrc
  echo 'export ROS_DOMAIN_ID=30 #TURTLEBOT3' >> ~/.bashrc
  source ~/.bashrc
  ```

    </details>

#### 2.3. その他の必要な ROS2 パッケージのインストール

その他の必要な ROS2 パッケージをインストールします．

```bash
sudo apt update
sudo apt install -y ros-humble-cartographer ros-humble-cartographer-ros ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-dynamixel-sdk ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-gripper-controllers ros-humble-moveit ros-humble-moveit-servo ros-humble-gazebo-* ros-humble-realsense2-camera-msgs ros-humble-realsense2-description
cd ~/turtlebot3_ws/src
git clone -b humble-devel https://github.com/ROBOTIS-JAPAN-GIT/turtlebot3_lime.git
git clone -b foxy-devel https://github.com/pal-robotics/realsense_gazebo_plugin.git
cd ~/turtlebot3_ws && colcon build --symlink-install && . install/setup.bash
```

Gazebo のセットアップを毎回読み込むように設定します．

```bash
echo 'source /usr/share/gazebo/setup.sh' >> ~/.bashrc
source ~/.bashrc
```

### 3. 実機での動かし方

#### 3.1. セットアップ（この操作は，動かす際に必ず行ってください）

**必ず，Jetson Orin Nano とリモート PC の時刻を同期してください．両方をインターネットに接続すれば，時刻が同期されます．**

Jetson Orin Nano に ssh 接続して，ドライバを立ち上げます．

```bash
ros2 launch turtlebot3_lime_bringup hardware.launch.py
```

**MoveIt 2 実行中に bringup を終了しないでください．中断する場合は先に moveit を終了してください．**

MoveIt Servo を起動します．

```bash
ros2 launch turtlebot3_lime_moveit_config servo.launch.py
```

#### 3.2. 地図を作る (SLAM)

リモート PC 側で SLAM を立ち上げます．

```bash
ros2 launch turtlebot3_lime_cartographer cartographer.launch.py
```

リモート PC 側でテレオペを実行します．

```bash
ros2 run turtlebot3_lime_teleop turtlebot3_lime_teleop
```

キーボードから以下の操作ができます．

| Key       | Operation                      |
| --------- | ------------------------------ |
| `1` / `q` | Joint1 を正方向 / 負方向に回転 |
| `2` / `w` | Joint2 を正方向 / 負方向に回転 |
| `3` / `e` | Joint3 を正方向 / 負方向に回転 |
| `4` / `r` | Joint4 を正方向 / 負方向に回転 |
| `5` / `t` | Joint5 を正方向 / 負方向に回転 |
| `6` / `y` | Joint6 を正方向 / 負方向に回転 |
| `o` / `p` | グリッパーを開く / 閉じる      |
| `i`       | TurtleBot3 を前進              |
| `k`       | TurtleBot3 を後退              |
| `j`       | TurtleBot3 を左旋回            |
| `l`       | TurtleBot3 を右旋回            |
| `Space`   | TurtleBot3 を停止              |
| `Esc`     | テレオペを終了                 |

リモート PC 側でマップを保存します．

```bash
ros2 run nav2_map_server map_saver_cli -f ~/map
```

#### 3.3. Navigation 2

リモート PC で Navigation 2 を実行します．

```bash
ros2 launch turtlebot3_lime_navigation2 navigation2.launch.py map_yaml_file:=$HOME/map.yaml
```

#### 3.4. MoveIt 2

**MoveIt 2 実行中に bringup を終了しないでください．中断する場合は先に moveit を終了してください．**

リモート PC で Move Group と RViz2 を起動します．

```bash
ros2 launch turtlebot3_lime_moveit_config moveit_core.launch.py
```

#### 3.5. Navigation 2 と MoveIt 2 を同時に実行する

リモート PC で以下のコマンドを実行します．

```bash
ros2 launch turtlebot3_lime_bringup moveit_navigation.launch.py map_yaml_file:=$HOME/map.yaml
```

#### 3.6. Realsense D435i のドライバを実行する

Jetson Orin Nano に ssh 接続して，ドライバを立ち上げます．

```bash
ros2 launch realsense2_camera rs_launch.py
```

### 4. Fake Hardware での動かし方

#### 4.1. セットアップ

この操作は，動かす際に全てリモート PC で行ってください．

Fake Hardware を起動します．

```bash
ros2 launch turtlebot3_lime_bringup fake.launch.py
```

MoveIt Servo を起動します．

```bash
ros2 launch turtlebot3_lime_moveit_config servo.launch.py use_fake_hardware:=true
```

#### 4.2. MoveIt 2

Fake Hardware 用 Move Group と RViz2 を起動します．

```bash
ros2 launch turtlebot3_lime_moveit_config moveit_fake.launch.py
```

### 5. シミュレーションの動かし方

#### 5.1. セットアップ

この操作は，動かす際に全てリモート PC で行ってください．

Gazebo を起動します．

```bash
ros2 launch turtlebot3_lime_gazebo turtlebot3_world.launch.py
```

MoveIt Servo を起動します．

```bash
ros2 launch turtlebot3_lime_moveit_config servo.launch.py use_sim_time:=true use_gazebo:=true
```

#### 5.2. 地図を作る (SLAM)

![cartographer](./img/cartographer.gif?raw=true)

SLAM を立ち上げます．

```bash
ros2 launch turtlebot3_lime_cartographer cartographer.launch.py use_sim_time:=true
```

テレオペを実行します．Gazebo では Servo と同じシミュレーション時刻を使うため，`use_sim_time:=true` を指定します．時刻が一致しないと，アーム指令のタイムアウトが正常に判定されません．

```bash
ros2 run turtlebot3_lime_teleop turtlebot3_lime_teleop --ros-args -p use_sim_time:=true
```

キーボードから以下の操作ができます．

| Key       | Operation                      |
| --------- | ------------------------------ |
| `1` / `q` | Joint1 を正方向 / 負方向に回転 |
| `2` / `w` | Joint2 を正方向 / 負方向に回転 |
| `3` / `e` | Joint3 を正方向 / 負方向に回転 |
| `4` / `r` | Joint4 を正方向 / 負方向に回転 |
| `5` / `t` | Joint5 を正方向 / 負方向に回転 |
| `6` / `y` | Joint6 を正方向 / 負方向に回転 |
| `o` / `p` | グリッパーを開く / 閉じる      |
| `i`       | TurtleBot3 を前進              |
| `k`       | TurtleBot3 を後退              |
| `j`       | TurtleBot3 を左旋回            |
| `l`       | TurtleBot3 を右旋回            |
| `Space`   | TurtleBot3 を停止              |
| `Esc`     | テレオペを終了                 |

マップを保存します．

```bash
ros2 run nav2_map_server map_saver_cli -f ~/map
```

#### 5.3. Navigation 2

![navigation](./img/navigation.gif?raw=true)

Navigation 2 を起動します．

```bash
ros2 launch turtlebot3_lime_navigation2 navigation2.launch.py use_sim_time:=true map_yaml_file:=$HOME/map.yaml
```

#### 5.4. MoveIt 2

![moveit](./img/moveit.gif?raw=true)

Gazebo 用 Move Group と RViz2 を起動します．

```bash
ros2 launch turtlebot3_lime_moveit_config moveit_gazebo.launch.py
```

#### 5.5. Navigation 2 と MoveIt 2 を同時に実行する

![moveit_navigation](./img/moveit_navigation.gif?raw=true)

以下のコマンドを実行します．

```bash
ros2 launch turtlebot3_lime_bringup moveit_navigation.launch.py use_sim_time:=true use_gazebo:=true map_yaml_file:=$HOME/map.yaml
```

## TurtleBot3 with OpenMANIPULATOR の ROBOTIS e-Manual

- [TurtleBot3 with OpenMANIPULATOR](https://emanual.robotis.com/docs/en/platform/turtlebot3/manipulation/)

## TurtleBot3 に関するオープンソース関連

- [turtlebot3_manipulation](https://github.com/ROBOTIS-GIT/turtlebot3_manipulation/tree/humble-devel)
- [turtlebot3](https://github.com/ROBOTIS-GIT/turtlebot3)
- [turtlebot3_jp_custom](https://github.com/ROBOTIS-JAPAN-GIT/turtlebot3_jp_custom)
- [turtlebot3_msgs](https://github.com/ROBOTIS-GIT/turtlebot3_msgs)
- [turtlebot3_simulations](https://github.com/ROBOTIS-GIT/turtlebot3_simulations)
- [turtlebot3_simulations_jp_custom](https://github.com/ROBOTIS-JAPAN-GIT/turtlebot3_simulations_jp_custom)
- [dynamixel_sdk](https://github.com/ROBOTIS-GIT/DynamixelSDK)
- [OpenCR-Hardware](https://github.com/ROBOTIS-GIT/OpenCR-Hardware)
- [OpenCR](https://github.com/ROBOTIS-GIT/OpenCR)

## TurtleBot3 に関するドキュメントと動画

- [ROBOTIS e-Manual for TurtleBot3 with OpenMANIPULATOR](https://emanual.robotis.com/docs/en/platform/turtlebot3/manipulation/)
- [ROBOTIS e-Manual for TurtleBot3](http://turtlebot3.robotis.com/)
- [ROBOTIS e-Manual for Dynamixel SDK](http://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/)
- [Website for TurtleBot Series](http://www.turtlebot.com/)
- [e-Book for TurtleBot3](https://community.robotsource.org/t/download-the-ros-robot-programming-book-for-free/51/)
- [Videos for TurtleBot3](https://www.youtube.com/playlist?list=PLRG6WP3c31_XI3wlvHlx2Mp8BYqgqDURU)
