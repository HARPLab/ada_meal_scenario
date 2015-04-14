import numpy, prpy.viz
from bypassable_action import ActionException, BypassableAction
from prpy.planning.base import PlanningError
import time

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
        if True: #fork is None:
            desired_ee_pose = numpy.array([[0.04367424,  0.02037604, -0.99883801,  0.],
                                           [-0.99854746,  0.03246594, -0.04299924, 0.],
                                           [ 0.03155207,  0.99926512,  0.02176437, 0.],
                                           [ 0.        ,  0.        ,  0.        ,  1.        ]])
        else:
            
            desired_fork_tip_in_world = numpy.array([[ 0.,  0., 1., 0.],
                                                     [-1.,  0., 0., 0.],
                                                     [ 0., -1., 0., 0.],
                                                     [ 0.,  0., 0., 1.]])
            ee_in_world = manip.GetEndEffectorTransform()
            fork_tip_in_world = fork.GetLink('tinetip').GetTransform()
            ee_in_fork_tip = numpy.dot(numpy.linalg.inv(fork_tip_in_world),
                                       ee_in_world)
            desired_ee_pose = numpy.dot(desired_fork_tip_in_world, ee_in_fork_tip)

        morsal_pose = morsal.GetTransform()
        #xoffset = -0.11
        xoffset = -0.11
        #yoffset = 0.035
        yoffset = -0.02

        desired_ee_pose[0,3] = morsal_pose[0,3] + xoffset
        desired_ee_pose[1,3] = morsal_pose[1,3] + yoffset
        desired_ee_pose[2,3] = 1.03

        # Plan near morsal
        try:
            with prpy.viz.RenderPoses([desired_ee_pose], env):
                path = robot.PlanToEndEffectorPose(desired_ee_pose, execute=False)
                robot.ExecuteTrajectory(path)
        except PlanningError, e:
            raise ActionException(self, 'Failed to plan to pose near morsal: %s' % str(e))
        time.sleep(4)
        # Now stab the morsal
        try:
            direction = numpy.array([0., 0., -1.])
            distance = 0.085
            with prpy.viz.RenderVector(manip.GetEndEffectorTransform()[:3,3],
                                       direction=direction, length=distance, env=env):
                path = robot.PlanToEndEffectorOffset(direction=direction,
                                                 distance=distance,
                                                 execute=False)  #TODO: add some tolerance
                robot.ExecuteTrajectory(path)
                import time
                time.sleep(2)
        except PlanningError, e:
            raise ActionException(self, 'Failed to plan straight line path to grab morsal: %s' % str(e))

        # Grab the kinbody
        #robot.Grab(morsal)
