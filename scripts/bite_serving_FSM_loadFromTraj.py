#!/usr/bin/env python
import json
import numpy
import openravepy
import adapy
import prpy
import numpy as np


import tf
import rospkg

import os
import time

import rospy

from std_msgs.msg import String

from tasklogger import TaskLogger

slowVelocityLimits = np.asarray([ 0.3,0.3,0.3,0.3,0.3,0.3,0.78,0.78])


defaultEndEffectorPose = np.asarray([[ 0.04367424,  0.02037604, -0.99883801,  0.65296864],
        [-0.99854746,  0.03246594, -0.04299924, -0.00927059],
        [ 0.03155207,  0.99926512,  0.02176437,  1.03388379],
        [ 0.        ,  0.        ,  0.        ,  1.        ]])

class AdaBiteServing(object):
  
  #Finite State Machine
  ROBOT_STATE = "INITIAL"
  plateDetectedTimes = 1
  RESOLUTION = 0.02
  NUMTRAJ = 9

  def addWaterServingTask(self):
    self.waterServing_task = self.tasklist.add_task('WaterServing')
    self.findGlass_subtask = self.waterServing_task.add_task('Find Glass')
    self.graspGlass_subtask = self.waterServing_task.add_task('Grasp Glass')
    self.liftGlass_subtask = self.waterServing_task.add_task('Lift Glass')
    self.drinkGlass_subtask = self.waterServing_task.add_task('Drink Glass')
    self.returnGlass_subtask = self.waterServing_task.add_task('Return Glass')
    self.placeGlass_subtask = self.waterServing_task.add_task('Place Glass')



  def initSimple(self):

    self.NUM_UPDATE_CALLS = 30
    self.Initialized = False

    rospy.init_node('bite_serving_scenario', anonymous = True)
    env_path = '/environments/table.env.xml'

    openravepy.RaveInitialize(True, level=openravepy.DebugLevel.Debug)
    openravepy.misc.InitOpenRAVELogging();
    self.env, self.robot = adapy.initialize(attach_viewer='qtcoin', sim=False, env_path = env_path)
    self.robot.SetActiveManipulator('Mico')
    self.manip = self.robot.GetActiveManipulator()


    # find the ordata
    rospack = rospkg.RosPack()
    file_root = rospack.get_path('pr_ordata')

    self.table = self.env.GetKinBody('table')

    robot_pose = numpy.array([[1, 0, 0, 0.409],[0, 1, 0, 0.338],[0, 0, 1, 0.795],[0, 0, 0, 1]])
    self.robot.SetTransform(robot_pose)

    ViewSide1Obj = self.env.GetKinBody('ViewSide1')
    ViewSide1Trans = ViewSide1Obj.GetTransform()

    ViewSide2Obj = self.env.GetKinBody('ViewSide2')
    ViewSide2Trans = ViewSide2Obj.GetTransform()

    ViewTopObj = self.env.GetKinBody('ViewTop')
    ViewTopTrans = ViewTopObj.GetTransform()

    self.numOfGrasps = 0
    self.numOfUpdateCalls = 100


    viewer = self.env.GetViewer()

    self.trajectoryPlanned = True


    # tf listener for querying transforms
    self.tfListener = tf.TransformListener()

    self.manip = self.robot.arm
    #self.robot.SetActiveManipulator(manip)
    activedofs = [i for i in range(6)]
    self.robot.SetActiveDOFs(activedofs)
    #self.robot.planner = prpy.planning.Sequence(self.robot.cbirrt_planner)      


    self.Initialized = True

    self.pub = rospy.Publisher('ada_tasks',String, queue_size=10)
    self.sub = rospy.Subscriber("/perception/morsel_detection", String, self._MorselDetectionCallback, queue_size=1)

    self.tasklist = TaskLogger()  
    self.addWaterServingTask()

    self.ball=self.env.ReadKinBodyURI('objects/smallsphere.kinbody.xml')
    self.ball.SetName('smallsphere')
    self.env.Add(self.ball)

    self.manip = self.robot.arm
    #self.manip.SetIKSolver(iksolver)

    self.statePub = rospy.Publisher('ROBOT_STATE', String, queue_size=10)
    #rospy.init_node('Robot State')
    self.rospyRate = rospy.Rate(33.33) # 10hz

    self.ROBOT_STATE = "EXECUTING_TRAJECTORY"
    self.statePub.publish(adaBiteServing.ROBOT_STATE)

    self.manip = self.robot.arm

    #load trajectories
    folderPath = os.path.dirname(os.path.abspath(os.path.join(__file__, os.pardir)))
    self.traj_lookingAtFace = prpy.rave.load_trajectory(self.env,folderPath + "/data/trajectories/traj_lookingAtFace.xml")   
    self.traj_lookingAtPlate = prpy.rave.load_trajectory(self.env,folderPath + "/data/trajectories/traj_lookingAtPlate.xml")   
    self.traj_serving = prpy.rave.load_trajectory(self.env,folderPath + "/data/trajectories/traj_serving.xml")   

    self.traj1_list = []
    self.traj2_list = []
    for ii in range(0,self.NUMTRAJ):
      for jj in range(0,self.NUMTRAJ):
          traj_name1 =folderPath + '/data/trajectories/traj1_x%d_y%d.xml' % (ii, jj)
          traj_name2 =folderPath + '/data/trajectories/traj2_x%d_y%d.xml' % (ii, jj)
          traj1 = prpy.rave.load_trajectory(self.env,traj_name1)   
          traj2 = prpy.rave.load_trajectory(self.env,traj_name2)   
          self.traj1_list.append(traj1)
          self.traj2_list.append(traj2)
    #from IPython import embed
    #embed()

    self.robot.ExecuteTrajectory(self.traj_lookingAtFace)
    time.sleep(4)

  
    #iksolver = openravepy.RaveCreateIkSolver(self.env,"NloptIK")
    #self.manip.SetIKSolver(iksolver)
    #self.bite_detected = False

    self.ROBOT_STATE = "LOOKING_AT_FACE"
    self.statePub.publish(adaBiteServing.ROBOT_STATE)

  def lookingAtPlate(self):
    if(self.bite_detected == True):
      print "registering ball pose"
      self.ball.SetTransform(self.bite_world_pose)
      self.ROBOT_STATE = "EXECUTING_TRAJECTORY"

  def lookingAtFace(self):
    #get face recognition
    self.bite_detected = False
    self.ROBOT_STATE = "EXECUTING_TRAJECTORY"
    self.statePub.publish(adaBiteServing.ROBOT_STATE)
    self.robot.ExecuteTrajectory(self.traj_lookingAtPlate)
    time.sleep(3)
    self.ROBOT_STATE = "LOOKING_AT_PLATE"
    self.statePub.publish(adaBiteServing.ROBOT_STATE)

  def _MorselDetectionCallback(self, msg):
    obj =  json.loads(msg.data)
    arr = obj['pts3d']
    pos = np.asarray(arr)
    if(pos is None) or(len(pos)==0) or (self.ROBOT_STATE!="LOOKING_AT_PLATE"):
      return
    else:
      relative_pos = pos[0]
      relative_pose = np.eye(4)
      relative_pose[0,3] = relative_pos[0] 
      relative_pose[1,3] = relative_pos[1]
      relative_pose[2,3] = relative_pos[2]
      world_camera = self.robot.GetLinks()[7].GetTransform()
      self.bite_world_pose = np.dot(world_camera,relative_pose)
      self.bite_detected = True


        

  def executeTrajectory(self):    
    defaultVelocityLimits = self.robot.GetDOFVelocityLimits()
    

    #endEffectorPose = defaultEndEffectorPose.copy()
    #endEffectorPose[0,3] = self.bite_world_pose[0,3]-0.11
    #endEffectorPose[1,3] = self.bite_world_pose[1,3]+0.035
    #endEffectorPose[2,3] = 0.98
    platecenter = numpy.array([0.729, -0.052,0.7612])
    startPose = numpy.zeros(2)
    startPose[0] = platecenter[0] - self.NUMTRAJ*self.RESOLUTION/2
    startPose[1] = platecenter[1] - self.NUMTRAJ*self.RESOLUTION/2

    diff = numpy.zeros(2)
    diff[0] = self.bite_world_pose[0,3] + 0.01 -   startPose[0] 
    diff[1] = self.bite_world_pose[1,3] -   startPose[1]

    numii = int(diff[0]/self.RESOLUTION) + 1
    numjj = int(diff[1]/self.RESOLUTION) - 1
    numii = max([numii,0])
    numjj = max([numjj,0])
    numii = min([numii,self.NUMTRAJ-1])
    numjj = min([numjj,self.NUMTRAJ-1])
    traj1 = self.traj1_list[numii*self.NUMTRAJ + numjj]
    traj2 = self.traj2_list[numii*self.NUMTRAJ + numjj]
   
    # path = self.robot.PlanToEndEffectorPose(endEffectorPose, execute = False)
    #from IPython import embed
    #embed()
    self.robot.ExecuteTrajectory(traj1)
    time.sleep(3.5)
    self.robot.ExecuteTrajectory(traj2)
    time.sleep(1.5)
    # #@self.robot.planner = prpy.planning.Sequence(self.robot.greedyik_planner, self.robot.cbirrt_planner) 
    # #from IPython import embed
    # #embed()
    # #from IPython import embed
    # #embed()
    # path = self.robot.PlanToEndEffectorOffset(numpy.asarray([0, 0, -1]),0.11, execute = False)
    # self.robot.ExecutePath(path)

    #time.sleep(2)

    self.robot.ExecuteTrajectory(self.traj_serving)


    time.sleep(5)
    #print str(self.tasklist)
    if(self.waterServing_task.is_complete()):
      self.addWaterServingTask()
      self.pub.publish(str(self.tasklist))
    #self.robot.planner = prpy.planning.Sequence(self.robot.cbirrt_planner) 
    self.ROBOT_STATE = "LOOKING_AT_FACE"

  
if __name__ == "__main__":
  adaBiteServing = AdaBiteServing()
  while not rospy.is_shutdown():
    if(adaBiteServing.ROBOT_STATE == "INITIAL"):
      adaBiteServing.initSimple()
    elif(adaBiteServing.ROBOT_STATE == "LOOKING_AT_FACE"):
      adaBiteServing.lookingAtFace()
    elif(adaBiteServing.ROBOT_STATE == "LOOKING_AT_PLATE"):
      adaBiteServing.lookingAtPlate()
    elif(adaBiteServing.ROBOT_STATE == "EXECUTING_TRAJECTORY"):
      adaBiteServing.executeTrajectory()
    else:
      print "Error: Unknown ROBOT_STATE"
  adaBiteServing.statePub.publish(adaBiteServing.ROBOT_STATE)
  adaBiteServing.rospyRate.sleep()