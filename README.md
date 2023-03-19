# Automated Nerf Turret - Injury Imminent

## Introduction
This project is an automated Nerf turret designed to track and engage targets using a thermal camera. The turret is equipped with PID controlled motors for precise aiming and features adjustable flywheels for ball pitching. It is intended for use in various settings, such as office environments, home security, or just for fun.

## Hardware Design
The automated Nerf turret consists of the following hardware components:

- STM32 Nucleo board with MicroPython and the pyboard library
- Thermal camera for target tracking
- One motor with encoder and PID control for turret yaw 
- Two 3D-printed brushless flywheels and ESCs for launching Nerf Rival balls
- Servo for controlling the firing pin
- ESP32 for thermal camera processing
- Various electronic components such as switches, resistors, capacitors, etc.

![Turret Image](IMG_20230315_005736.jpg)

## Software Design
The software for the automated Nerf turret is written in MicroPython and utilizes tasks to manage different components of the system. It includes tasks for controlling the yaw motor, flywheels, firing pin, and camera tracking.

Additionally, we developed a custom camera driver for the thermal camera using an ESP32 microcontroller written in C++. This driver enables us to achieve a refresh rate of up to 35 fps, significantly higher than the initial 2 fps, in theory enabling real-time tracking. To view the camera output in real-time and adjust parameters, we created a custom program using the Tauri desktop app framework, with UI elements and
control created using Svelte and Typescript. Debug communication between the ESP32 and computer (for image viewing and tuning) was done using the WebSerial API. 

Communication between the ESP32 and the STM32 Nucleo board is established through a UART connection. This allows the Nucleo board to receive error values from the camera for target tracking and control in a simple
CSV format.

![State diagram](state_diagram.png)

## Results
We conducted several tests to evaluate the performance of the automated Nerf turret:

**Pitching**: 
    We experimented with varying the speed differential of the flywheels to apply a spin on the Nerf balls, causing them to pitch up or down. This allowed us to fine-tune the pitching mechanism and achieve the desired trajectory.

**Yaw Tuning**: 
    We adjusted the PID values for the yaw control to ensure that the turret could track targets in real-time and fire accurately. Through a series of iterative tests, we optimized the PID parameters for smooth and responsive tracking.

**Final Testing**: 
    We performed several end-to-end tests of the entire system to validate its functionality. These tests demonstrated that the turret could successfully track targets, adjust its aim, and fire Nerf balls with precision.

Overall, the automated Nerf turret performed well during the tests, with accurate targeting, responsive tracking, and adjustable pitching. Further improvements can be made to enhance the system's performance and adapt it to various use cases.

## Lessons Learned and Recommendations
Throughout the development of the automated Nerf turret, we encountered several challenges and gained valuable insights that could benefit future iterations or similar projects:

**Tight belt for precise control**: We discovered that maintaining minimal backlash in the yaw control system was essential for achieving precise target tracking. A loose gearbox in the original design reduced the overall accuracy of the system and caused issues with PID. This backlash was remedied by replacing the original motor with a motor, belt, and encoder extracted from an inkjet printer.

**Benefits of using ESP32**: Integrating the ESP32 microcontroller for the camera driver proved to be highly beneficial. Not only did it allow us to achieve a higher frame rate, but it also provided valuable experience in communication between different microcontrollers and working with multiple programming languages. This experience could be applied to other projects requiring seamless integration of various components.

**Lightweight design and motor performance**: Our design focused on keeping the turret lightweight, which significantly reduced the load on the motors. This enabled the motors to move the turret effectively and efficiently without any issues. Future designs should continue to prioritize weight management and consider the performance limitations of the chosen motors.

By addressing these lessons learned and building upon our experiences, future iterations of the automated Nerf turret or similar projects can be improved and optimized for better performance and functionality.

## Additional Files
(Provide links to additional files as appropriate, such as code files, images, videos, or other resources related to the project.)
Camera Driver: https://github.com/DominicChm/mlx-viewer