'''
HOANG TRONG PHI
@HuaangFei
17/10/2024
'''
import maya.cmds as cmds



def curveNameButtonPush(self, *args, **kwargs):
    '''pops the selection into the text field'''
    sel = cmds.ls(sl=True)
    if not sel:
        raise RuntimeError("select a curve")
    cmds.textFieldButtonGrp(self.widgets['curveNameGrp'], e=True, text=sel[0])


def geoNameButtonPush(self,*args,**kwargs):
    '''pops the selection into the text field'''
    sel = cmds.ls(sl=True)
    if not sel:
        raise RuntimeError("select the cable geo")
    cmds.textFieldButtonGrp(self.widgets['geoNameGrp'],e=True,text=sel[0])

    def rigFromCurve(self, crv, numSpans=8, numJoints=10, numCtrls=5, stripWidth=1.0, ctrlWidth=2.0, geo=None, uMin=0.0,
                     uMax=1.0):
        '''make a cable rig from the given curve
            numSpans = number of spans in Nurbs strip
            numJoints = number of joints riding on nurbs strip
            numCtrls = number of controls to make
            stripWidth = width of nurbs strip (can make it easier to paint weights if wider)
            ctrlWidth = size of ctrls
        '''

        shapes = cmds.listRelatives(crv, s=1)
        crvShape = shapes[0]
        # Make rig top nulls to parent stuff under
        topNull = cmds.createNode('transform', n=crv + "_Rig")
        hiddenStuff = cmds.createNode('transform', n=crv + "_NOTOUCH", p=topNull)
        cmds.setAttr(hiddenStuff + ".inheritsTransform", 0)
        cmds.setAttr(hiddenStuff + ".visibility", 0)
        cmds.addAttr(topNull, ln="stretchAmount", dv=1.0, min=0, max=1)
        cmds.addAttr(topNull, ln='slideAmount', dv=0.0)

        # make nurbs strip using extrude
        crossCurve = cmds.curve(d=1, p=[(0, 0, -0.5 * stripWidth), (0, 0, 0.5 * stripWidth)], k=(0, 1))
        cmds.select([crossCurve, crv], r=1)
        surf = cmds.extrude(ch=False, po=0, et=2, ucp=1, fpt=1, upn=1, rotation=0, scale=1, rsp=1)[0]
        cmds.delete(crossCurve)
        surf = cmds.rename(surf, crv + "_driverSurf")
        cmds.parent(surf, hiddenStuff)

        # Rebuild strip to proper number of spans
        cmds.rebuildSurface(surf, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kc=1, sv=numSpans, su=0, du=1, tol=0.01, fr=0,
                            dir=2)

        # make live curve on surface down the middle
        # this is used later for noStretch
        curvMaker = cmds.createNode('curveFromSurfaceIso', n=surf + "CurveIso")
        cmds.setAttr(curvMaker + ".isoparmValue", 0.5)
        cmds.setAttr(curvMaker + ".isoparmDirection", 1)
        cmds.connectAttr(surf + ".worldSpace[0]", curvMaker + ".inputSurface")

        offsetCrvShp = cmds.createNode("nurbsCurve", n=crv + "_driverSurfCrvShape")
        offsetCrv = cmds.listRelatives(p=1)[0]
        offsetCrv = cmds.rename(offsetCrv, crv + "_driverSurfCrv")
        cmds.connectAttr(curvMaker + ".outputCurve", offsetCrvShp + ".create")
        cmds.parent(offsetCrv, hiddenStuff)

        # Measure curve length and divide by start length.
        # This turns curve length into a normalized value that is
        # useful for multiplying by UV values later to control stretch
        crvInfo = cmds.createNode('curveInfo', n=offsetCrv + "Info")
        cmds.connectAttr(offsetCrv + ".worldSpace[0]", crvInfo + ".ic")
        arcLength = cmds.getAttr(crvInfo + ".al")
        stretchAmountNode = cmds.createNode('multiplyDivide', n=offsetCrv + "Stretch")
        cmds.setAttr(stretchAmountNode + ".op", 2)  # divide
        cmds.setAttr(stretchAmountNode + ".input1X", arcLength)
        cmds.connectAttr(crvInfo + ".al", stretchAmountNode + ".input2X")

        # Stretch Blender blends start length with current length
        # and pipes it back into stretchAmoundNode's startLength, to "trick" it into
        # thinking there is no stretch..
        # That way, when user turns on this "noStretch" attr, the startLength will
        # be made to equal current length, and stretchAmountNode will always be 1.
        # so the chain will not stretch.
        stretchBlender = cmds.createNode('blendColors', n=offsetCrv + "StretchBlender")
        cmds.setAttr(stretchBlender + ".c1r", arcLength)
        cmds.connectAttr(crvInfo + ".al", stretchBlender + ".c2r")
        cmds.connectAttr(stretchBlender + ".opr", stretchAmountNode + ".input1X")
        cmds.connectAttr(topNull + ".stretchAmount", stretchBlender + ".blender")

        # make skin joints and attach to surface
        skinJoints = []
        skinJointParent = cmds.createNode('transform', n=crv + "_skinJoints", p=topNull)
        for i in range(numJoints):
            cmds.select(clear=True)
            jnt = cmds.joint(p=(0, 0, 0), n=crv + "_driverJoint%02d" % i)
            locator = cmds.spaceLocator(n=crv + "driverLoc%02d" % i)[0]
            cmds.setAttr(locator + ".localScale", stripWidth, stripWidth, stripWidth)
            cmds.parent(locator, hiddenStuff)
            percentage = float(i) / (numJoints - 1.0)
            print("percentage:", percentage)
            print(i)
            if i > 1 and i < numJoints - 2:
                percentage = uMin + (percentage * (uMax - uMin))
                print("\tinterp percent", percentage)
            posNode, aimCnss, moPath, slider = self.attachObjToSurf(locator, surf, offsetCrv, stretchAmountNode,
                                                                    percentage)
            cmds.connectAttr(topNull + ".slideAmount", slider + ".i2")
            cmds.parentConstraint(locator, jnt, mo=False)
            if len(skinJoints):
                cmds.parent(jnt, skinJoints[-1])
            else:
                cmds.parent(jnt, skinJointParent)
            skinJoints.append(jnt)
            cmds.setAttr(jnt + ".radius", stripWidth)  # just cosmetic

        # add controls
        ctrls = []
        stripJoints = []
        stripJointParent = cmds.createNode('transform', n=crv + "_stripJoints", p=hiddenStuff)
        ctrlParent = cmds.createNode('transform', n=crv + "_Ctrls", p=topNull)

        for i in range(numCtrls):
            # The first control is larger, and has the stretch attr
            if i == 0:
                zero, ctrl = self.makeCubeCtrl(crv + "_Ctrl%02d" % i, size=ctrlWidth * 1.8)
                cmds.addAttr(ctrl, ln="noStretch", dv=0.0, min=0, max=1, k=1, s=1)
                cmds.addAttr(ctrl, ln='slideAmount', dv=0.0, min=-1.0, max=1.0, k=1, s=1)
                cmds.connectAttr(ctrl + ".noStretch", topNull + ".stretchAmount")
                cmds.connectAttr(ctrl + ".slideAmount", topNull + ".slideAmount")
            else:
                zero, ctrl = self.makeCubeCtrl(crv + "_Ctrl%02d" % i, size=ctrlWidth)

            # Make the joint the control. These drive the nurbs strip.
            cmds.select(clear=True)
            jnt = cmds.joint(p=(0, 0, 0), n=ctrl + "StripJnt")
            cmds.parentConstraint(ctrl, jnt, mo=False)
            cmds.setAttr(jnt + ".radius", stripWidth * 1.3)  # just cosmetic

            # briefly attach ctrls to strip to align them
            percentage = float(i) / (numCtrls - 1.0)
            print("ctrl percentage:", percentage)
            if i > 0 and i < numCtrls - 1:
                percentage = uMin + (percentage * (uMax - uMin))
                print('\tinterp percentage:', percentage)
            cmds.delete(self.attachObjToSurf(zero, surf, offsetCrv, stretchAmountNode, percentage))
            ctrls.append(ctrl)
            cmds.parent(jnt, stripJointParent)
            stripJoints.append(jnt)
            cmds.parent(zero, ctrlParent)

        # skin strip to controls
        # Can get some different behavior by chaning the strip's weights
        # or perhaps using dual quat. mode on the skinCluster
        skinObjs = stripJoints + [surf]
        cmds.skinCluster(skinObjs,
                         bindMethod=0,  # closest Point
                         sm=0,  # standard bind method
                         ih=True,  # ignore hierarchy
                         )

        # rebuild curve and skin to joints
        newCurve = cmds.duplicate(crv)[0]
        newCurve = cmds.rename(newCurve, crv + "_skinned")
        cmds.parent(newCurve, topNull)
        cmds.rebuildCurve(newCurve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0, s=numJoints - 2, d=3, tol=0.01)
        skinObjs = skinJoints + [newCurve]
        cmds.skinCluster(skinObjs,
                         bindMethod=0,
                         sm=0,
                         ih=True,
                         mi=1
                         )
        if geo:
            wireDef, wireCrv = cmds.wire(geo, w=newCurve, n=crv + "_wire", dds=(0, 10), en=1.0, ce=0, li=0)
            print(wireDef)
            cmds.parent(wireCrv, hiddenStuff)
            if cmds.objExists(wireCrv + "BaseWire"):
                cmds.parent(wireCrv + "BaseWire", hiddenStuff)