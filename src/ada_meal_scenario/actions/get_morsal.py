import numpy, prpy.viz
from bypassable_action import ActionException, BypassableAction
from prpy.planning.base import PlanningError
import time
import openravepy
import numpy as np


class SkewerMorsal(BypassableAction):
    def __init__(self, bypass=False):
        BypassableAction.__init__(self, 'EXECUTING_TRAJECTORY', bypass=bypass)
        
    def _run(self, manip):
        robot = manip.GetRobot()
        env = robot.GetEnv()
        morsal = env.GetKinBody('morsal')
        if morsal is None:
            raise ActionException(self, 'Failed to find morsal in environment.')
            
        fork = env.GetKinBody('fork')
        if fork is None:
            raise ActionException(self, 'Failed to find fork in environment.')
        
        morsal_pose = morsal.GetTransform()   

        # fork pointed downward
        desired_fork_tip_in_world = numpy.array([[-1.,  0., 0., 0.],
                                                 [ 0.,  1., 0., 0.],
                                                 [ 0.,  0.,-1., 0.],
                                                 [ 0.,  0., 0., 1.]])
        # calculate desired fork position to be above the morsal
        z_above_morsal = 0.05
        y_fork_offset = -0.02
        desired_fork_tip_in_world[0,3] = morsal_pose[0,3]
        desired_fork_tip_in_world[1,3] = morsal_pose[1,3] + y_fork_offset
        desired_fork_tip_in_world[2,3] = morsal_pose[2,3] + z_above_morsal

        fork_tip_in_world = fork.GetLink('tinetip').GetTransform()
        ee_in_world = manip.GetEndEffectorTransform()
        ee_in_fork_tip = numpy.dot(numpy.linalg.inv(fork_tip_in_world), ee_in_world)
        desired_ee_pose = numpy.dot(desired_fork_tip_in_world, ee_in_fork_tip)     
        
        import openravepy
        h3 = openravepy.misc.DrawAxes(env, desired_ee_pose)

        # plan to above the morsal
        try:
            with prpy.viz.RenderPoses([desired_ee_pose, desired_fork_tip_in_world], env):
                path = robot.PlanToEndEffectorPose(desired_ee_pose, execute=True)
        except PlanningError, e:
            raise ActionException(self, 'Failed to plan to pose above morsal: %s' % str(e))

        # move downward into the morsal
        z_into_morsal = 0.05
        try:
            direction = numpy.array([0., 0., -1.])
            distance = z_above_morsal + z_into_morsal
            with prpy.viz.RenderVector(manip.GetEndEffectorTransform()[:3,3], direction=direction, length=distance, env=env):
                with prpy.rave.Disabled(fork):
                    T = robot.arm.GetEndEffectorTransform()
                    path = robot.arm.PlanToEndEffectorOffset(direction=direction, distance=distance, execute=True)
        except PlanningError, e:
            raise ActionException(self, 'Failed to plan straight line path to grab morsal: %s' % str(e))
        
        '''
        #calculate the desired rotated fork position
        fork_tip_in_world = fork.GetLink('tinetip').GetTransform()
        
        import math
        theta = -80.0/180.0*math.pi
        yoffset = 0.03
        zoffset = 0.10
        
        r_x = np.array([[1., 0., 0., 0.],
                        [0., math.cos(theta), -math.sin(theta), 0.],
                        [0., math.sin(theta), math.cos(theta), 0.],
                        [0., 0., 0., 1.]])
        #r_y = np.array([[math.cos(theta), 0., math.sin(theta), 0.],
        #                [0., 1., 0., 0.],
        #                [-math.sin(theta), 0., math.cos(theta), 0.],
        #                [0., 0., 0., 1.]])
        offset_fork_in_world = fork_tip_in_world
        offset_fork_in_world[1][3] += yoffset
        offset_fork_in_world[2][3] += zoffset
        desired_fork_tip_in_world = np.dot(offset_fork_in_world, r_x)
        ee_in_world = manip.GetEndEffectorTransform()
        ee_in_fork_tip = numpy.dot(numpy.linalg.inv(fork_tip_in_world), ee_in_world)
        desired_ee_pose = numpy.dot(desired_fork_tip_in_world, ee_in_fork_tip)
        
        # plan to rotated position by the morsal
        try:
            with prpy.viz.RenderPoses([desired_ee_pose, desired_fork_tip_in_world], env):
                path = robot.PlanToEndEffectorPose(desired_ee_pose, execute=True)
        except PlanningError, e:
            raise ActionException(self, 'Failed to plan to rotated pose by the morsal: %s' % str(e))
        '''

class GetMorsal(BypassableAction):

    def __init__(self, bypass=False):
        
        BypassableAction.__init__(self, 'EXECUTING_TRAJECTORY', bypass=bypass)
        
        
    def _run(self, manip):
        """
        Execute a sequence of plans that pick up the morsal
        @param manip The manipulator
        """
        global time
        robot = manip.GetRobot()
        env = robot.GetEnv()
        morsal = env.GetKinBody('morsal')
        if morsal is None:
            raise ActionException(self, 'Failed to find morsal in environment.')
  

        fork = env.GetKinBody('fork')
        #if True: #fork is None:
        if fork is None:
            desired_ee_pose = numpy.array([[-0.06875708,  0.25515971, -0.96445113,  0.51087426],
                                           [ 0.2036257 ,  0.9499768 ,  0.23681355,  0.03655854],
                                           [ 0.97663147, -0.18010443, -0.11727471,  0.92 ],
                                           [ 0.        ,  0.        ,  0.        ,  1.        ]])
        else:
            #TODO instead of fixing the pose, switch to TSR to sample orientations that face downward

            #fork top facing left
#            desired_fork_tip_in_world = numpy.array([[0.,  1., 0., 0.],
#                                                     [ 1.,  0., 0., 0.],
#                                                     [ 0.,  0.,-1., 0.],
#                                                     [ 0.,  0., 0., 1.]])

             #fork top facing towards user
            desired_fork_tip_in_world = numpy.array([[-1.,  0., 0., 0.],
                                                     [ 0.,  1., 0., 0.],
                                                     [ 0.,  0.,-1., 0.],
                                                     [ 0.,  0., 0., 1.]])

            morsal_pose = morsal.GetTransform()

            #old values
            #xoffset = -0.185
            #yoffset = 0.06
            
            xoffset = 0.01
            yoffset = -0.01#-0.005
            zoffset = 0.06

            desired_fork_tip_in_world[0,3] = morsal_pose[0,3] + xoffset
            desired_fork_tip_in_world[1,3] = morsal_pose[1,3] + yoffset
            desired_fork_tip_in_world[2,3] = morsal_pose[2,3] + zoffset

            fork_tip_in_world = fork.GetLink('tinetip').GetTransform()
            ee_in_world = manip.GetEndEffectorTransform()
            ee_in_fork_tip = numpy.dot(numpy.linalg.inv(fork_tip_in_world),
                                       ee_in_world)
            desired_ee_pose = numpy.dot(desired_fork_tip_in_world, ee_in_fork_tip)

        import openravepy
        h3 = openravepy.misc.DrawAxes(env, desired_ee_pose)

#        #save old limits
#        old_acceleration_limits = robot.GetDOFAccelerationLimits()
#        old_velocity_limits = robot.GetDOFVelocityLimits()
#
#        #slow down robot
#        robot.SetDOFVelocityLimits(0.5*robot.GetDOFVelocityLimits())
#        robot.SetDOFAccelerationLimits(0.8*robot.GetDOFAccelerationLimits())

        # Plan near morsal
        try:
            with prpy.viz.RenderPoses([desired_ee_pose, desired_fork_tip_in_world], env):
                


                path = robot.PlanToEndEffectorPose(desired_ee_pose, execute=True)
                
                #path = robot.PlanToEndEffectorPose(desired_ee_pose, execute=False)
                #res = openravepy.planningutils.SmoothTrajectory(path,1, 1, 'HauserParabolicSmoother', '')
                #robot.ExecuteTrajectory(path)

        except PlanningError, e:
            raise ActionException(self, 'Failed to plan to pose near morsal: %s' % str(e))
        #time.sleep(4)
        # Now stab the morsal
        
        #restore velocity limits
#        robot.SetDOFVelocityLimits(old_velocity_limits)
#        robot.SetDOFAccelerationLimits(old_acceleration_limits)

        try:
            direction = numpy.array([0., 0., -1.])
            distance = 0.05
            with prpy.viz.RenderVector(manip.GetEndEffectorTransform()[:3,3],
                                       direction=direction, length=distance, env=env):
                with prpy.rave.Disabled(fork):
                    T = robot.arm.GetEndEffectorTransform()
                    path = robot.arm.PlanToEndEffectorOffset(direction=direction,
                                                 distance=distance,
                                                 execute=True)  #TODO: add some tolerance


               
                    #from IPython import embed
                    #embed()
                    
        except PlanningError, e:
            raise ActionException(self, 'Failed to plan straight line path to grab morsal: %s' % str(e))

        # Grab the kinbody
        #robot.Grab(morsal)
