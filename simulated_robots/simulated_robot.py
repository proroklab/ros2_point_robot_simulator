import numpy as np

from geometry_msgs.msg import PoseStamped, TransformStamped
from scipy.spatial.transform import Rotation as R
from tf2_ros.transform_broadcaster import TransformBroadcaster


class SimulatedRobotBase:
    WATCHDOG_FREQUENCY_HZ = 5

    def __init__(self, uuid, node):
        super().__init__()

        self.orientation = R.from_euler("xyz", [0, 0, 0])
        self.position = np.zeros(3)  # x/y/z

        self.node = node
        self.uuid = uuid
        self.orientation_offset = R.from_euler("z", 0)

        self.pose_publisher = self.node.create_publisher(
            PoseStamped, f"/motion_capture_server/rigid_bodies/{self.uuid}/pose", 1
        )
        self.tf_publisher = TransformBroadcaster(node=self.node)

        self.watchdog = None

    def reset_watchdog(self):
        # Reset the watchdog. The watchdog only starts running after it was reset once.
        if self.watchdog is None:
            self.watchdog = self.node.create_timer(
                1 / self.WATCHDOG_FREQUENCY_HZ, self.stop
            )
        self.watchdog.reset()

    def step(self, dt):
        # dt: time step
        raise NotImplementedError()

    def stop(self):
        # Called by watchdog if wasn't reset in time
        raise NotImplementedError()

    def publish_pose(self):
        msg = PoseStamped()

        msg.pose.position.x = self.position[0]
        msg.pose.position.y = self.position[1]
        msg.pose.position.z = self.position[2]

        # This offset is inversing the mocap_offset in tb_control action_server
        orientation = (self.orientation * self.orientation_offset).as_quat()
        msg.pose.orientation.x = orientation[0]
        msg.pose.orientation.y = orientation[1]
        msg.pose.orientation.z = orientation[2]
        msg.pose.orientation.w = orientation[3]

        msg.header.frame_id = "mocap"
        msg.header.stamp = self.node.get_clock().now().to_msg()

        self.pose_publisher.publish(msg)

    def publish_tf(self):
        """Broadcast the goal as a tf for visualization"""
        tf = TransformStamped()
        tf.header.frame_id = "mocap"
        tf.header.stamp = self.node.get_clock().now().to_msg()
        tf.child_frame_id = f"{self.uuid}"

        tf.transform.translation.x = float(self.position[0])
        tf.transform.translation.y = float(self.position[1])
        tf.transform.translation.z = float(self.position[2])
        # This offset is inversing the mocap_offset in tb_control action_server
        orientation = (self.orientation * self.orientation_offset).as_quat()

        tf.transform.rotation.x = orientation[0]
        tf.transform.rotation.y = orientation[1]
        tf.transform.rotation.z = orientation[2]
        tf.transform.rotation.w = orientation[3]

        self.tf_publisher.sendTransform(tf)
