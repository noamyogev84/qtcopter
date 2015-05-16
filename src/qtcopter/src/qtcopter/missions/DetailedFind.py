from . import MissionState
from .balldrop.coords import cam_pixel_to_xy
import rospy
import cv2
import tf


class DetailedFind(MissionState):
    def __init__(self, debug_pub, find_object_center_func):
        MissionState.__init__(self,
                              debug_pub,
                              input_keys=['roi'],
                              outcomes=['succeeded',
                                        'aborted',
                                        'failed'])
        self._find_object_center = find_object_center_func
        self._pub = tf.TransformBroadcaster()

    def publish_offset(self, center, estimated_size):
        # Get size of target in millimeters
        real_size = rospy.get_param('target/size')

        image_width = rospy.get_param('camera/image_width')
        image_height = rospy.get_param('camera/image_height')

        # Get offset in pixels
        offset = (center[0]-image_width/2.0, center[1]-image_height/2.0)

        # Get distance in millimetres
        # TODO: f from camera calibration
        f = 28
        distance = f*real_size/estimated_size
        offset[0] = f*offset[0]/distance
        offset[1] = f*offset[1]/distance

        # Send a default angle
        angle = tf.transformations.quaternion_from_euler(0, 0, 0)

        if rospy.get_param('camera/pointing_downwards'):
            # Camera points to the ground
            # -> distance to object is z coordinate
            x, y = offset
            z = distance
        else:
            # Camera is facing forward
            # -> distance to object is y coordinate
            x, z = offset
            y = distance

        self._pub.sendTransform((x, y, z),
                                angle,
                                rospy.Time.now(),
                                'camera',
                                'target')

    def on_execute(self, userdata, image, height):
        '''
        Finds the target object and publishes the transformation to it.

        If the target is lost, return 'failed'.
        If the optimal position is reached, return 'succeeded'.
        '''
        # Cut out ROI
        min, max = userdata.roi
        rospy.loginfo('Searching for target in ROI '
                      '({0:d}, {1:d}), ({2:d}, {3:d}).'.format(min[0],
                                                               min[1],
                                                               max[0],
                                                               max[1]))
        cropped_image = image[min[1]:max[1], min[0]:max[0]]

        # Find center of target
        center, size = self._find_object_center(cropped_image)
        if center is not None:
            # Add offset to uncropped image
            center = (int(center[0] + min[0]), int(center[1] + min[1]))

        def draw_center_location():
            rospy.logdebug('Publishing center location of target.')
            cv2.rectangle(image, userdata.roi[0], userdata.roi[1], (255, 0, 0))
            if center is not None:
                cv2.circle(image, center, int(height*10),
                           (0, 255, 0), -1)
            return image
        self.debug_publish(draw_center_location)

        if center is None:
            rospy.loginfo('Lost target, try finding it again.')
            return 'failed'

        rospy.logdebug('Publishing offset to target.')
        self.publish_offset(center, size)
        # TODO: when mission finished:
        #  return 'succeeded'
        return None
