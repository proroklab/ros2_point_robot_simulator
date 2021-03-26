import rclpy
import re

import numpy as np
from scipy.spatial.transform import Rotation as R

from rclpy.node import Node
from .simulated_robot import SimulatedRobotBase
from .simple_simulator import SimpleSimulator


class CrazyFlie(SimulatedRobotBase):
    MAX_V_LINEAR_X_M_S = 3.5
    MAX_V_LINEAR_Y_M_S = 2.8
    MAX_V_ROT_Z_RAD_S = 10.5

    def __init__(self, uuid, node):
        super().__init__(uuid, node)

        self.velocity = RoboMasterControl()
        self.velocity_subscription = self.node.create_subscription(
            RoboMasterControl, f"/{self.uuid}/cmd_vel", self.velocity_callback, 1
        )

    def velocity_callback(self, vel):
        self.reset_watchdog()
        self.velocity = vel

    def stop(self):
        self.velocity = RoboMasterControl()

    def step(self, dt):
        self.position += self.orientation.apply(
            np.array(
                [
                    np.clip(
                        self.velocity.vx,
                        -self.MAX_V_LINEAR_X_M_S,
                        self.MAX_V_LINEAR_X_M_S,
                    ),
                    -np.clip(
                        self.velocity.vy,
                        -self.MAX_V_LINEAR_Y_M_S,
                        self.MAX_V_LINEAR_Y_M_S,
                    ),
                    0,
                ]
            )
            * dt
        )
        self.orientation *= R.from_euler(
            "xyz",
            np.array(
                [
                    0,
                    0,
                    np.clip(
                        -self.velocity.omega,
                        -self.MAX_V_ROT_Z_RAD_S,
                        self.MAX_V_ROT_Z_RAD_S,
                    ),
                ]
            )
            * dt,
        )

def main(args=None):
    rclpy.init(args=args)
    publisher = SimpleSimulator("simple_crazyflie", r"/crazyflie_\d+/", CrazyFlie)
    rclpy.spin(publisher)
    publisher.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
