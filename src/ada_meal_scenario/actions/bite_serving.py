from bypassable_action import BypassableAction, ActionException
from trajectory_actions import LookAtPlate, Serve
from detect_morsel import DetectMorsel
from get_morsel import GetMorsel
from direct_teleop_action import DirectTeleopAction
from std_msgs.msg import String

from ada_teleoperation.DataRecordingUtils import *

import logging
logger = logging.getLogger('ada_meal_scenario')


class BiteServing(BypassableAction):

    def __init__(self, bypass = False):
        BypassableAction.__init__(self, 'BiteServing', bypass=bypass)

    def execute(self, manip, env, method, ui_device, state_pub, detection_sim=False, record_trial=False, file_directory=None):
        
        if record_trial:
          if file_directory is None:
            file_directory = rospkg.RosPack().get_path('ada_meal_scenario') + '/trajectory_data'

          rosbag_topic_names = ['/ada_tasks', '/hydra_calib', '/ada/joy', '/perception/morsel_detection', '/joint_states']
          filename_trajdata, filename_bag = get_next_filename_pair(file_directory=file_directory)

          rosbag_process = start_rosbag(rosbag_topic_names, filename=filename_bag)
          state_pub.publish("recording data to " + str(filename_bag))
        else:
          filename_trajdata = None


        try: 
          # Move to look at plate
          action = LookAtPlate(bypass = self.bypass)
          state_pub.publish(action.name)
          action.execute(manip)

          # Detect morsel
          if self.bypass:
              detection_sim = True
          action = DetectMorsel(bypass = detection_sim)
          state_pub.publish(action.name)
          action.execute(manip.GetRobot())
                      
          # Move to get object
          action = GetMorsel(bypass = self.bypass)
          state_pub.publish(action.name)
          action.execute(manip, method, ui_device, state_pub, filename_trajdata=filename_trajdata)

          # Serve the morsel
          action = Serve(bypass = self.bypass)
          state_pub.publish(action.name)
          action.execute(manip)

          state_pub.publish("Finished bite serving")
          if record_trial:
            stop_rosbag(rosbag_process)

        except ActionException, e:
          state_pub.publish("Failed to run bite serving")
          if record_trial:
            stop_rosbag(rosbag_process)
          raise

