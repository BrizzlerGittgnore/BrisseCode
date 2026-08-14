"""
Auto-Rig Metahuman - Advanced Skeleton add-on.

Non-invasive: does NOT modify AdvancedSkeleton.mel. Instead it watches for
the AdvancedSkeleton window and injects an "Auto-Rig Metahuman" button into
its native "Tools" panel. That button calls AS's own stock procs in
sequence, same as clicking:
NameMatcher (set to MetaHuman) -> Create + Place FitSkeleton
-> Build AdvancedSkeleton -> Constraint to Joints.

Requires Advanced Skeleton to already be installed (an unmodified/vanilla
copy is fine - nothing here depends on any local edits to AS).

HOW TO USE
----------
One-time per Maya session:
    Drag this file from Windows Explorer onto a Maya shelf, then click the
    resulting button once. This arms the add-on for the rest of the
    session - the "Auto-Rig Metahuman" button then appears inside AS's own
    Tools panel every time the AdvancedSkeleton window is (re)opened.

To have it arm automatically every time Maya starts (no manual click):
    1. Put this file in a folder on Maya's script path
       (e.g. Documents/maya/scripts).
    2. Add this line to userSetup.py in that same folder
       (create the file if it doesn't exist):
           import AS_meta
"""

import maya.cmds as cmds
import maya.mel as mel

_TOOLS_LAYOUT = "asToolsFrameLayout"
_BUTTON = "asAutoRigMetahumanButton"
_ARMED_OPTVAR = "AS_meta_watcherJobNum"


def autoRigMetahuman(*_):
    if not mel.eval('exists "asNameMatcherUI"'):
        cmds.warning('Advanced Skeleton is not loaded in this session. '
                      'Open the AdvancedSkeleton window once, then try again.')
        return

    mel.eval('asNameMatcherUI')

    if mel.eval('optionMenu -q -ex asMappingUIFiles'):
        mel.eval('optionMenu -e -v "MetaHuman" asMappingUIFiles')
    mel.eval('asMappingUIFileOptionMenuChanged nameMatcher')

    if not mel.eval('asNameMatcherCheckAndAutoRigFit'):
        return

    mel.eval('asReBuildAdvancedSkeleton')

    mel.eval('asMappingUIFunction AutoRigConstraint')

    if mel.eval('window -q -ex asMappingUI'):
        mel.eval('deleteUI asMappingUI')

    print('// Auto-Rig Metahuman completed.')


def _injectButton():
    if not cmds.frameLayout(_TOOLS_LAYOUT, exists=True):
        return
    if cmds.control(_BUTTON, exists=True):
        return

    cmds.setParent(_TOOLS_LAYOUT)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(60, 168))
    cmds.separator(style="none")
    cmds.button(_BUTTON, width=140, label="Auto-Rig Metahuman", command=autoRigMetahuman)
    cmds.setParent("..")


def install():
    """Arm the watcher that re-injects the button every time AS's Tools panel is (re)built."""
    existingJob = cmds.optionVar(query=_ARMED_OPTVAR) if cmds.optionVar(exists=_ARMED_OPTVAR) else 0
    if existingJob and cmds.scriptJob(exists=existingJob):
        _injectButton()
        return

    _injectButton()
    jobNum = cmds.scriptJob(event=["idle", _injectButton])
    cmds.optionVar(intValue=(_ARMED_OPTVAR, jobNum))
    print('// Auto-Rig Metahuman add-on armed for this session.')


install()
