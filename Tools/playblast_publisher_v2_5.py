"""
Playblast Publisher + Animation Exporter for Maya 2022 (v2)
===========================================================
Creates a playblast (optionally published to a Kitsu board via Gazu) and can
also bake/export the shot's character & camera animation.

Output layout:

    <PROJECT_ROOT>/                       e.g. EWC_FOUNDING_PARTNERS_2026
        movies/<SQ>/<SH>/                 <- playblasts
            SQ03_SH070_1001_1028_v001.mp4
        04_shots/.../<SQ_SH>/             e.g. .../SQ03_SH070
            anim/                         <- baked animation export
                v001/  v002/  ...
                  SQ03_SH070_Token_1001_1028_v001.fbx

Naming follows the animation exporter convention:
    <SQ>_<SH>[_<rig>][_Face]_<start>_<end>_<version>.<ext>
Playblast and export versions are independent counters (vNNN), separate from
the scene file version.

NOTES
-----
- Maya 2022 runs Python 3.7. Gazu must be installed into Maya's interpreter:
      "<MAYA>/bin/mayapy" -m pip install gazu
- Do NOT hard-code or commit credentials. Enter them in the UI at runtime.
"""

import maya.cmds as cmds
import maya.mel as mel
import os
import re
import sys
import subprocess
import tempfile
import shutil
import glob
import zipfile
import tarfile
import urllib.request
import json
from urllib.parse import urlparse

try:
    import gazu
    GAZU_AVAILABLE = True
except ImportError:
    gazu = None
    GAZU_AVAILABLE = False

import base64

# Embedded shelf icon (32x32 PNG, fox logo, transparent background).
_ICON_B64 = """\
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAABCGlDQ1BJQ0MgUHJvZmlsZQAAeJxj
YGA8wQAELAYMDLl5JUVB7k4KEZFRCuwPGBiBEAwSk4sLGHADoKpv1yBqL+viUYcLcKakFicD6Q9A
rFIEtBxopAiQLZIOYWuA2EkQtg2IXV5SUAJkB4DYRSFBzkB2CpCtkY7ETkJiJxcUgdT3ANk2uTml
yQh3M/Ck5oUGA2kOIJZhKGYIYnBncAL5H6IkfxEDg8VXBgbmCQixpJkMDNtbGRgkbiHEVBYwMPC3
MDBsO48QQ4RJQWJRIliIBYiZ0tIYGD4tZ2DgjWRgEL7AwMAVDQsIHG5TALvNnSEfCNMZchhSgSKe
DHkMyQx6QJYRgwGDIYMZAKbWPz9HbOBQAAAI7klEQVR42p2Xe4xV1RXGf2ufc98DwgwzKC8RUECc
VIUZnjKKWsQHQmCMqa2NVbGKpKaIIhSuY0qrFoMaG2MDSZsoWFCqLT5rtQOKwkQUkJcKA+X9hnnc
ufees/fqHzODgAM+dnLuyc29Z3/fWutb314HTl0CgOcxZ+L4W39dOmDbPQMucptrVjl1qjYM9buW
Da06p7pl9So3aUBfN6n04m1V48dWmkjkVIw2vogCf7j11pKDO7b+ueHwkQmlJcK+A8eJlQ5j9pKl
qIIxhrMtdQ4ReGziBLIbllNSXMTGg5ZUUfE/ivtfcu+MBQsOtIAqwInd0hUVnoDu3Lzx4Xj9oQmV
l0jwy/KYThhWzObl/6XmjWUYY3DWnhHcWYsYw6o3l7Hpw2omDu3MneURnXixCWJ1h8bv+rTmYQFN
V1R4rc98K5y6hvqUH8EmknnJ5Kz0LoSyngUsfmouYS6LiAHVNkJXRIQwn+OVJ5+irGeMXoWGhpyV
RCoQL2Jt5nh96vTHTiJQ3VwHMRZRb+3BJlbtbiQbWm64tAP7Nq7lg5cXIkYIgjzWWqwNWy5LPp9H
jOGDRS+xb9M6rr+0kFzg+GRPI2sPNiGIJ0bsWQicrAUl6fvsygT8p7aODknL1QOKWPL0s+Qy9USi
MTzPw/P8lssjGouRzzTy6rxnuaq0HR0Syvu1x9jdEJDwBVAcTk4OFsBvq5aC4FCiPhzNO97ddozL
L+jAmu17+cv0mZReMRwXBIjxTgjPRCKsX7GC6PG9XDaoiPe2HaUur8R8g6o7Y7T+WRWtEDNCfR4+
P3CU/r1SrF22mI2vLwS0WQrS0j4CGI/SPu1Zt/8YjYES8QWnincWjLMSkNYPVYwaRvb0uKlvIYog
KHrS/xSDAY7nsqzZ75pJqbR22w8j0Lq1AkGodGsX4bJzUySMYNUip3pJaxOiQOekz5Xnd2TNvkZ2
1WfxjYeYH0hAEKwq6pSfFKe4qDCGqiNwrfpojfrbjpZTJSrKsC4FbDliWH8oS+hABFwbWKattFtV
Ej4M79aefkUxQudwzpwAOfkup9mpQbAqhM7SryjJyG7tSPkG64Rvdqg4MwHrHAW+cFW3jpyX8MmH
LSmXs9fy2/4u5ENLSdKnokd7khElxHJ6G7ZBQIlFPJI+5FyIiPBjl4iQt0rSg4Tvo/Z7lECNCC0+
0KzrH0+gmQSoGhTBnojmLCXwfT/UIM+JJuebo0u1VUhtl8MhqOppvwqoQ4M8nu+FZ85ANU5VTdTp
4GjnHphYgdETOVOMCPGIEPcc2kZWHELMs8QigmdAWzXjQkw8aSIl3WgXT16pqlGqq90pBBZXVnpV
4Kb/9OqbY2Fm0LVTH7ORITcb21SPGA8jkMk7nv84y/JaJeZ5OOdQ53DO4ZyS8JQPa+GFlQENOfAR
MD4u00B08Dgz+qEqqw1HB0y/ZuSYKnCLKyu9VgKy4eIlqqre7i83zxwwZBj9h5YTK78Fr7gnGmQR
T2gKla8Phuytc4iE+PEEyY4dSRYWEoknUIE9dZavDgXkQkWMwQVNSOeeRAbfQv8hg6XfkDLdX7v9
UVWNbFiyRAHx0hUVftXfdtjYxo23Z/fvu++2382wnbp28bxoO1wsQX7dv8FPkopCeY8opZ0NDkOq
uDN+QQGRWAo/GidbX0/vYp9hPT06JKVZD9ksqbFTSfUuQzSQjp1K3KdvvdXli5Urt876YuPn6YoK
36+qrraqGpnUr8/M/mUDte/wK8TV14MR2pWNo+nzN9GvanCxAs6JO6xzeNE4XsTH2RCnBhPxkGiU
SDZDPB5BVXG5Bry+g2lfdhPkGnGq9B0xQi4aeLl+8dmamaq6UERCA+issdfdFvf0wnFTpjhnbYth
KZ4I7a+7H+fFACV04BxEEykQg2BarFCIJJOoQqgOBzg/Rrvr7sUY70RnOBuacVPud0nDhbPG3XAb
oAZAm2yvqAj5TM6aRAznHCKCzTWSumAQ0aET0cZ6jPHwjI8XT6AnjWWqSiSWbBYsPjTWERsygVTv
cly2ETEGnMPE4uSa8jbmCbYp0wvApNOYvqNHP9EUTb7/3OR7ouveeSfwi4qwocWIoEETHUfdgSvu
juYymHgcLxJtGQRMs9MgeNEoXjyBCxqxxd3pMOpXkMsgIrjQ4hUWs/7dd4LnJt8XParyVr504BNp
MKItZrVbNfmnwQOXBIcPXH/7Hx4Py8eP98PDhzAimIIOHPv479S/NJuCHr2JxxPYIIsTEG2eDUw0
Rj6ToX7nNtr/bA7nDLsF13gEVcEr7ETNa0vDv854xI927PTmXavXjL9EJK8gRkDT6bTpKpKZt+rT
8clzu74y/6Fp/keLFoV+p044NbjMcVKDbsbvfwVic9j2JZg+w0ldPYXkNVOQPiPQghKMy+P1H0mq
7EY0c7QZvKiIlS8vCudPm+anup//+rwW8HQ6beRkS02n0wYQ8SP8ZmjZ/Ht6nKvvPv9MoEFGg707
1B0+oNktNdq04lUNvlyrumu7Hq75RA/XfKy6a7uGX67XphVLNbulRt2RAxru3a6ab9T3nn8mf/f5
nfX+sktfEN9vfQGSM8yAKmkwkXicWWNGLbire4kum/fHQHMNGu7fqW7fTrVbN6vuqdW3n/y93tm7
q97Vq6u+/cRjqntr1X69We2+nRru26mab9Q35j0e3N2js84afe0CE422aC5tvs9xbsSP8EDF4Ko7
uhbrq3NmB5qvc+Gu7Zpbv1rtnq364m8n68+7dNJfnFekLz5wr9rdWzW3rkbDXdtVc3Vu6Zyq4I5u
nXTykMtnq6pUVuL9kKNVKsHDeDx4zciZd/co0ZdmTLVaf9jpnlrV/TtUazdp3ZqVWrfmI9XaTar7
/6e6t1a14ZBbOGOam9S9WB8cNWLmSWeOnHl4OQOJCvCqxYSPjh0zdcdnNXOHjblR+5eXodkm8SI+
vtccVGhDbGCReEI31azmw3/90/UsL59e9drbc9Pq/EdVrUjbI9V3paSZBISPjLl28qEtG+Y2ZbJR
Ec8o9oQZiUjzO6NTl0gm8snuPaY8vfyT+RXq/GoIzwbwfzhvgFuN7Z8GAAAAAElFTkSuQmCC"""


def _decode_icon():
    return base64.b64decode("".join(_ICON_B64.split()))


class PlayblastPublishUI(object):

    def __init__(self):
        self.window_name = "PlayblastPublishUI"
        self.kitsu_connected = False
        self.kitsu_user = None
        self.kitsu_projects = []
        self._last_detected_scene = None
        self._pw_is_qt = False
        self._pw_widget = None
        self.kitsu_pass_field = None

        # Resolved scene state (filled in by refresh_info)
        self.scene_name = None
        self.shot_name = None          # shot token, e.g. SQ03_SH070
        self.scene_version = None
        self.shot_root = None
        self.project_root = None
        self.movies_dir = None         # <project_root>/movies/<SQ>/<SH>
        self.render_root = None        # mirrors movies_dir (Open button target)
        self.next_version = None       # current playblast version (project-based)
        self._playblast_version_override = None  # set when user edits the field
        # Manual overrides for the (now editable) Scene Information fields.
        # None means "use the auto-detected value".
        self._ov_scene_name = None
        self._ov_shot_name = None
        self._ov_scene_version = None
        self._ov_shot_root = None
        self._ov_movies_dir = None
        self._ov_start = None
        self._ov_end = None
        self.project_name = None
        self.start_frame = None
        self.end_frame = None

        # Animation export state
        self.export_base = None        # <shot_root>/anim
        self.export_dir = None
        self.export_version = None
        self.custom_export_dir = None  # set when the user picks a location manually
        self.export_character_data = []
        self.export_body_checks = {}
        self.export_face_checks = {}

        # Landscape / blockout export state
        self.landscape_objects = []     # full DAG paths the user added
        self.landscape_dir = None       # user-specified output folder

    # ================================================================== UI
    def create_ui(self):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        self.window = cmds.window(self.window_name,
                                  title="Playblast Publisher",
                                  width=560, height=560,
                                  menuBar=True)
        cmds.menu(label="Tools", parent=self.window)
        cmds.menuItem(label="Install to Shelf",
                      command=lambda *a: install_to_shelf())
        cmds.menuItem(label="Forget Saved Kitsu Login",
                      command=self.forget_creds)

        root = cmds.scrollLayout(horizontalScrollBarThickness=0,
                                 verticalScrollBarThickness=16)
        main = cmds.columnLayout(adjustableColumn=True, rowSpacing=4,
                                 columnAttach=("both", 5), parent=root)

        # ---- Kitsu connection ----------------------------------------
        cmds.frameLayout(label="Kitsu Connection", collapsable=True,
                         collapse=False, marginHeight=5, parent=main)
        kcol = cmds.columnLayout(adjustableColumn=True)
        cached = self._load_creds()
        self.kitsu_url_field = cmds.textFieldGrp(
            label="Kitsu URL:", parent=kcol, text=cached.get("url", ""),
            annotation="Your Kitsu server URL. You can paste the API URL "
                       "(https://your-kitsu/api) or just the address bar from "
                       "your browser - it will be reduced to the /api root.")
        self.kitsu_login_field = cmds.textFieldGrp(
            label="Login (email):", parent=kcol, text=cached.get("login", ""))
        self._build_password_field(kcol)
        self.remember_check = cmds.checkBox(
            label="Remember login on this machine",
            value=bool(cached.get("remember", True)), parent=kcol,
            annotation="Caches URL, login and (obfuscated) password locally so "
                       "you don't re-enter them. Uncheck to stop saving.")
        self.kitsu_connect_btn = cmds.button(
            label="Connect", command=self.connect_kitsu, parent=kcol)
        self.kitsu_status_text = cmds.text(
            label="Status: not connected", align="left", parent=kcol)
        self._kcol = kcol
        self.install_btn = None
        self.gazu_status_text = None
        if GAZU_AVAILABLE:
            self.gazu_status_text = cmds.text(
                label="gazu installed", align="left", parent=kcol)
        else:
            self.install_btn = cmds.button(
                label="Install gazu", command=self.install_gazu, parent=kcol)
        cmds.setParent(main)

        # Prefill the cached password (masked) so a click on Connect is enough.
        cached_pw = self._deobfuscate(cached.get("pw", ""))
        if cached_pw:
            self._set_password(cached_pw)

        # ---- Scene information ---------------------------------------
        cmds.frameLayout(label="Scene Information", collapsable=True,
                         collapse=False, marginHeight=5, parent=main)
        scol = cmds.columnLayout(adjustableColumn=True)
        self.scene_name_field = cmds.textFieldGrp(
            label="Scene Name:", editable=True, parent=scol,
            changeCommand=self.on_scene_name_edited)
        self.shot_name_field = cmds.textFieldGrp(
            label="Shot Name:", editable=True, parent=scol,
            changeCommand=self.on_shot_name_edited,
            annotation="e.g. SQ03_SH070. Drives the movies folder, file naming "
                       "and the Kitsu shot. Clear to revert to auto-detect.")
        self.scene_version_field = cmds.textFieldGrp(
            label="Scene Version:", editable=True, parent=scol,
            changeCommand=self.on_scene_version_edited,
            annotation="Project version (e.g. v022). Sets the default playblast "
                       "version. Clear to revert to auto-detect.")
        self.shot_root_field = cmds.textFieldGrp(
            label="Shot Root:", editable=True, parent=scol,
            changeCommand=self.on_shot_root_edited,
            annotation="The shot folder. Animation exports go to <Shot Root>/anim. "
                       "Clear to revert to auto-detect.")
        self.frange_field = cmds.textFieldGrp(
            label="Frame Range:", editable=True, parent=scol,
            changeCommand=self.on_range_edited,
            annotation="Playblast/export range, e.g. '1001 - 1096'. Clear to use "
                       "the timeline range.")
        self.render_root_field = cmds.textFieldButtonGrp(
            label="Playblast Folder:", editable=True, parent=scol,
            buttonLabel="Open", buttonCommand=self.open_render_folder,
            changeCommand=self.on_movies_dir_edited,
            annotation="movies/<SQ>/<SH> under the project root. Editable; clear "
                       "to revert to auto-detect. 'Open' reveals it.")
        self.next_version_field = cmds.textFieldButtonGrp(
            label="Playblast Version:", editable=True, parent=scol,
            buttonLabel="Reset to project", buttonCommand=self.reset_playblast_version,
            changeCommand=self.on_playblast_version_edited,
            annotation="Defaults to the scene/project version (e.g. v022 from "
                       "SQ03_SH070_v022). Edit freely; 'Reset to project' restores "
                       "the project version.")
        self.kitsu_project_menu = cmds.optionMenu(
            label="Kitsu Board:", parent=scol,
            annotation="Target Kitsu board for publishing. Auto-selected from "
                       "the scene when you open one; change it to override.")
        cmds.menuItem(parent=self.kitsu_project_menu, label="<connect to load>")
        cmds.setParent(main)

        # ---- Playblast settings (streamlined) ------------------------
        cmds.frameLayout(label="Playblast Settings", collapsable=True,
                         collapse=False, marginHeight=5, parent=main)
        pcol = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label="Output: 1920 x 1080, mp4 (H.264 via FFmpeg)",
                  align="left", parent=pcol)
        self.publish_check = cmds.checkBox(
            label="Publish to Kitsu after render", value=True, parent=pcol)
        self.publish_column_menu = cmds.optionMenuGrp(
            label="Publish to column:", parent=pcol,
            annotation="Which Kitsu task type the playblast preview is "
                       "attached to.")
        for column in ("Styleframe", "Animatic", "Layout", "Mocap", "Animation"):
            cmds.menuItem(label=column)
        # Default the column to Animation
        cmds.optionMenuGrp(self.publish_column_menu, edit=True, value="Animation")
        self.comment_field = cmds.textFieldGrp(
            label="Comment:", parent=pcol,
            annotation="Optional comment posted with the Kitsu publish. "
                       "Leave blank to use 'Playblast vNNN'.")
        cmds.setParent(main)

        # ---- Export Animations (collapsed options until enabled) -----
        cmds.frameLayout(label="Export Animations", collapsable=True,
                         collapse=False, marginHeight=5, parent=main)
        excol = cmds.columnLayout(adjustableColumn=True)
        self.export_enable_check = cmds.checkBox(
            label="Enable animation export", value=False, parent=excol,
            changeCommand=self._toggle_export_options)

        # Everything below is hidden until the toggle is on.
        self.export_options_col = cmds.columnLayout(
            adjustableColumn=True, parent=excol, manage=False)

        self.export_format_radio = cmds.radioButtonGrp(
            label="Format:", labelArray2=["FBX", "Alembic"],
            numberOfRadioButtons=2, select=1, parent=self.export_options_col,
            changeCommand=lambda *a: self.refresh_export_info(),
            annotation="FBX exports the baked skeleton; Alembic bakes the "
                       "deforming meshes as a geometry cache.")
        self.export_path_field = cmds.textFieldButtonGrp(
            label="Export Folder:", editable=True, parent=self.export_options_col,
            buttonLabel="Browse...", buttonCommand=self.browse_export_location,
            changeCommand=self.on_export_path_edited,
            annotation="Default is <shot>/anim/vNNN. Browse or type to override; "
                       "Reset returns to the default.")
        rrow = cmds.rowLayout(numberOfColumns=2, parent=self.export_options_col)
        cmds.button(label="Reset to Default Location",
                    command=self.reset_export_location, parent=rrow)
        cmds.button(label="Open Folder", command=self.open_export_folder, parent=rrow)
        cmds.setParent(self.export_options_col)
        self.export_next_version_field = cmds.textFieldGrp(
            label="Next Export Version:", editable=False, parent=self.export_options_col)
        self.export_frange_field = cmds.textFieldGrp(
            label="Frame Range:", editable=False, parent=self.export_options_col)

        cmds.text(label="Characters to export:", align="left",
                  parent=self.export_options_col)
        self.export_characters_column = cmds.columnLayout(
            adjustableColumn=True, parent=self.export_options_col)
        cmds.setParent(self.export_options_col)
        self.export_camera_text = cmds.text(
            label="ShotCam: Not Found", align="left", parent=self.export_options_col)
        cmds.button(label="Export Animations", command=self.export_animations,
                    parent=self.export_options_col)
        cmds.setParent(main)

        # ---- Export Landscape (blockout meshes; collapsed until enabled) --
        cmds.frameLayout(label="Export Landscape", collapsable=True,
                         collapse=True, marginHeight=5, parent=main)
        lcol = cmds.columnLayout(adjustableColumn=True)
        self.landscape_enable_check = cmds.checkBox(
            label="Enable landscape export", value=False, parent=lcol,
            changeCommand=self._toggle_landscape_options)
        cmds.setParent(main)

        self.landscape_options_col = cmds.columnLayout(
            adjustableColumn=True, rowSpacing=3, manage=False, parent=main)
        self.landscape_format_radio = cmds.radioButtonGrp(
            label="Format:", labelArray2=["FBX", "Alembic"],
            numberOfRadioButtons=2, select=1, parent=self.landscape_options_col)
        self.landscape_path_field = cmds.textFieldButtonGrp(
            label="Export Folder:", editable=True, parent=self.landscape_options_col,
            buttonLabel="Browse...", buttonCommand=self.browse_landscape_location,
            changeCommand=self.on_landscape_path_edited,
            annotation="Required. Pick the folder these meshes are exported to.")
        lrow = cmds.rowLayout(numberOfColumns=1, parent=self.landscape_options_col)
        cmds.button(label="Open Folder", command=self.open_landscape_folder, parent=lrow)
        cmds.setParent(self.landscape_options_col)
        self.landscape_name_field = cmds.textFieldGrp(
            label="Base Name:", text="Blockout", parent=self.landscape_options_col,
            annotation="Used for the combined file, and as a prefix otherwise.")
        self.landscape_combine_check = cmds.checkBox(
            label="Combine selection into one file", value=True,
            parent=self.landscape_options_col)

        cmds.text(label="Objects to export (add from your outliner selection):",
                  align="left", parent=self.landscape_options_col)
        self.landscape_list = cmds.textScrollList(
            allowMultiSelection=True, numberOfRows=6, height=110,
            parent=self.landscape_options_col)
        orow = cmds.rowLayout(numberOfColumns=3, columnWidth3=(180, 180, 180),
                              parent=self.landscape_options_col)
        cmds.button(label="Add Selected", command=self.add_landscape_objects, parent=orow)
        cmds.button(label="Remove Highlighted", command=self.remove_landscape_objects, parent=orow)
        cmds.button(label="Clear", command=self.clear_landscape_objects, parent=orow)
        cmds.setParent(self.landscape_options_col)
        cmds.button(label="Export Landscape", command=self.export_landscape,
                    parent=self.landscape_options_col)
        cmds.setParent(main)

        # ---- Buttons -------------------------------------------------
        brow = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2,
                              columnWidth2=(180, 360), parent=main)
        cmds.button(label="Refresh Info", command=self.refresh_info, parent=brow)
        cmds.button(label="Render Playblast", command=self.render_playblast, parent=brow)
        cmds.setParent(main)

        cmds.showWindow(self.window)
        self.refresh_info()

        # If a login is cached, connect automatically so no typing is needed.
        if GAZU_AVAILABLE and self._get_password() and \
                cmds.textFieldGrp(self.kitsu_login_field, q=True, text=True).strip():
            try:
                self.connect_kitsu()
            except Exception:
                pass

    # ============================================================ helpers
    def _default_resolution(self):
        try:
            w = int(cmds.getAttr("defaultResolution.width"))
            h = int(cmds.getAttr("defaultResolution.height"))
            if w > 0 and h > 0:
                return w, h
        except Exception:
            pass
        return 1920, 1080

    @staticmethod
    def _normalize(text):
        """Lowercase + strip everything but alphanumerics, for folder matching."""
        return re.sub(r"[^a-z0-9]", "", text.lower())

    # ===================================================== scene resolution
    def get_scene_info(self):
        """Parse scene path -> (scene_name, shot_token, scene_version, scene_path).

        shot_token preserves case and uses an underscore, e.g. 'SQ03_SH070'.
        """
        scene_path = cmds.file(q=True, sn=True)
        if not scene_path:
            return None, None, None, None

        scene_name = os.path.basename(scene_path)
        scene_no_ext = os.path.splitext(scene_name)[0]

        shot_match = re.search(r"(SQ\d+)[_]?(SH\d+)", scene_no_ext, re.IGNORECASE)
        shot_token = "{}_{}".format(shot_match.group(1), shot_match.group(2)) \
            if shot_match else "Unknown"

        version_match = re.search(r"(v\d+)", scene_no_ext, re.IGNORECASE)
        scene_version = version_match.group(1) if version_match else "v001"

        return scene_name, shot_token, scene_version, scene_path

    @staticmethod
    def get_frame_range():
        """Timeline (playback) range as integers (start, end)."""
        start = int(round(cmds.playbackOptions(q=True, min=True)))
        end = int(round(cmds.playbackOptions(q=True, max=True)))
        return start, end

    def _split_shot_token(self, token=None):
        """Return (sequence, shot) from a shot token, e.g. ('SQ03', 'SH070')."""
        token = token if token is not None else (self.shot_name or "")
        m = re.search(r"(SQ\d+)[_]?(SH\d+)", token, re.IGNORECASE)
        if not m:
            return None, None
        return m.group(1), m.group(2)

    def find_project_root(self, scene_path):
        """Walk up to the folder above the shots folder (e.g. '04_shots').

        Example: .../EWC_FOUNDING_PARTNERS_2026/04_shots/main/SQ03_SH070/01_Maya
        -> returns .../EWC_FOUNDING_PARTNERS_2026 . The 'movies' folder lives here.
        """
        if not scene_path:
            return None
        d = os.path.dirname(scene_path)
        last = None
        while d and d != last:
            if re.fullmatch(r"\d*[_-]?shots", os.path.basename(d), re.IGNORECASE):
                return os.path.dirname(d)
            last = d
            d = os.path.dirname(d)
        return None

    def find_shot_root(self, scene_path, shot_name):
        """Walk up from the scene file to the folder named after the shot."""
        if shot_name in (None, "Unknown"):
            return None
        target = self._normalize(shot_name)
        d = os.path.dirname(scene_path)
        last = None
        while d and d != last:
            if self._normalize(os.path.basename(d)) == target:
                return d
            last = d
            d = os.path.dirname(d)
        return None

    def get_next_version(self, base_dir):
        """Scan base_dir for vNNN sub-folders and return the next one as 'vNNN'."""
        existing = []
        if os.path.isdir(base_dir):
            for name in os.listdir(base_dir):
                m = re.fullmatch(r"v(\d+)", name, re.IGNORECASE)
                if m and os.path.isdir(os.path.join(base_dir, name)):
                    existing.append(int(m.group(1)))
        nxt = (max(existing) + 1) if existing else 1
        return "v{:03d}".format(nxt)

    def get_next_file_version(self, folder):
        """Next vNNN based on existing files named '..._vNNN.<ext>' in folder."""
        nums = []
        if os.path.isdir(folder):
            for name in os.listdir(folder):
                m = re.search(r"_v(\d+)\.", name, re.IGNORECASE)
                if m:
                    nums.append(int(m.group(1)))
        nxt = (max(nums) + 1) if nums else 1
        return "v{:03d}".format(nxt)

    # ===================================================== UI population
    def refresh_info(self, *args):
        scene_name, shot_token, scene_version, scene_path = self.get_scene_info()

        if not scene_name:
            for f in (self.scene_name_field, self.shot_name_field,
                      self.scene_version_field, self.shot_root_field,
                      self.frange_field):
                cmds.textFieldGrp(f, edit=True, text="<scene not saved>")
            cmds.textFieldButtonGrp(self.next_version_field, edit=True,
                                    text="<scene not saved>")
            cmds.textFieldButtonGrp(self.render_root_field, edit=True,
                                    text="<scene not saved>")
            return

        shot_root = self._ov_shot_root or self.find_shot_root(scene_path, shot_token)
        project_root = self.find_project_root(scene_path) or \
            (os.path.dirname(shot_root) if shot_root else os.path.dirname(scene_path))

        # Apply manual overrides (None => use auto-detected value).
        scene_name = self._ov_scene_name or scene_name
        shot_token = self._ov_shot_name or shot_token
        scene_version = self._ov_scene_version or scene_version

        # Playblast destination: <project_root>/movies/<SQ>/<SH>
        seq, shot = self._split_shot_token(shot_token)
        if project_root and seq and shot:
            detected_movies = os.path.join(project_root, "movies", seq, shot)
        else:
            detected_movies = ""
        movies_dir = self._ov_movies_dir or detected_movies

        # Default playblast version = the project/scene version (e.g. v022).
        # A manual edit (override) is kept until the user resets it.
        default_version = scene_version or "v001"
        playblast_version = self._playblast_version_override or default_version

        det_start, det_end = self.get_frame_range()
        start = self._ov_start if self._ov_start is not None else det_start
        end = self._ov_end if self._ov_end is not None else det_end

        # Export base: <shot_folder>/anim  (animation-exporter convention)
        export_base = os.path.join(shot_root, "anim") if shot_root else ""

        # The "Maya project" is the shot-root folder (e.g. SQ03_SH070).
        project_name = os.path.basename(shot_root) if shot_root else shot_token

        self.scene_name = scene_name
        self.shot_name = shot_token
        self.scene_version = scene_version
        self.shot_root = shot_root
        self.project_root = project_root
        self.movies_dir = movies_dir
        self.next_version = playblast_version
        self.project_name = project_name
        self.start_frame = start
        self.end_frame = end
        self.export_base = export_base
        self.render_root = movies_dir  # so the Open button targets the movies folder

        cmds.textFieldGrp(self.scene_name_field, edit=True, text=scene_name)
        cmds.textFieldGrp(self.shot_name_field, edit=True, text=shot_token)
        cmds.textFieldGrp(self.scene_version_field, edit=True, text=scene_version)
        cmds.textFieldGrp(self.shot_root_field, edit=True,
                          text=shot_root or "<shot folder not found>")
        cmds.textFieldGrp(self.frange_field, edit=True,
                          text="{} - {}".format(start, end))
        cmds.textFieldButtonGrp(self.render_root_field, edit=True,
                                text=movies_dir or "<could not resolve movies path>")
        cmds.textFieldButtonGrp(self.next_version_field, edit=True, text=playblast_version)
        self._update_kitsu_project_field()

        if cmds.checkBox(self.export_enable_check, q=True, value=True):
            self.refresh_export_info()

    @staticmethod
    def _normalize_version(text):
        """Coerce user input to vNNN (>=3 digits). Returns None if no digits."""
        if not text:
            return None
        m = re.search(r"(\d+)", text)
        if not m:
            return None
        return "v{:03d}".format(int(m.group(1)))

    def on_playblast_version_edited(self, *args):
        """Capture a manual edit of the playblast version as an override."""
        txt = cmds.textFieldButtonGrp(self.next_version_field, q=True, text=True)
        norm = self._normalize_version(txt)
        default = self.scene_version or "v001"
        if norm and norm != default:
            self._playblast_version_override = norm
            self.next_version = norm
            # Reflect the normalized form back into the field.
            if norm != txt:
                cmds.textFieldButtonGrp(self.next_version_field, edit=True, text=norm)
        else:
            # Empty or back to the project version -> drop the override.
            self._playblast_version_override = None
            self.next_version = default
            cmds.textFieldButtonGrp(self.next_version_field, edit=True, text=default)

    def reset_playblast_version(self, *args):
        """Reset the playblast version back to the project/scene version."""
        self._playblast_version_override = None
        default = self.scene_version or "v001"
        self.next_version = default
        cmds.textFieldButtonGrp(self.next_version_field, edit=True, text=default)

    # --------------------------------------------- editable field handlers
    def on_scene_name_edited(self, *args):
        txt = cmds.textFieldGrp(self.scene_name_field, q=True, text=True).strip()
        self._ov_scene_name = txt or None

    def on_shot_name_edited(self, *args):
        txt = cmds.textFieldGrp(self.shot_name_field, q=True, text=True).strip()
        self._ov_shot_name = txt or None
        self.refresh_info()

    def on_scene_version_edited(self, *args):
        txt = cmds.textFieldGrp(self.scene_version_field, q=True, text=True).strip()
        self._ov_scene_version = (self._normalize_version(txt) if txt else None)
        self.refresh_info()

    def on_shot_root_edited(self, *args):
        txt = cmds.textFieldGrp(self.shot_root_field, q=True, text=True).strip()
        self._ov_shot_root = txt.replace("\\", "/") if txt else None
        self.refresh_info()

    def on_range_edited(self, *args):
        txt = cmds.textFieldGrp(self.frange_field, q=True, text=True).strip()
        m = re.search(r"(-?\d+)\s*\D+\s*(-?\d+)", txt)
        if m:
            self._ov_start, self._ov_end = int(m.group(1)), int(m.group(2))
        else:
            self._ov_start = self._ov_end = None
        self.refresh_info()

    def on_movies_dir_edited(self, *args):
        txt = cmds.textFieldButtonGrp(self.render_root_field, q=True, text=True).strip()
        self._ov_movies_dir = txt.replace("\\", "/") if txt else None
        self.refresh_info()

    @staticmethod
    def _open_in_explorer(path):
        path = os.path.normpath(path)
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def open_render_folder(self, *args):
        """Reveal the movies/SQ/SH folder (or its parent if not created yet)."""
        target = None
        if self.movies_dir and os.path.isdir(self.movies_dir):
            target = self.movies_dir
        elif self.project_root and os.path.isdir(os.path.join(self.project_root, "movies")):
            target = os.path.join(self.project_root, "movies")
        elif self.shot_root and os.path.isdir(self.shot_root):
            target = self.shot_root
        if not target:
            cmds.warning("Playblast folder doesn't exist yet - render once, or "
                         "save the scene inside the shot folder structure.")
            return
        try:
            self._open_in_explorer(target)
        except Exception as e:
            cmds.warning("Could not open folder: {}".format(e))

    def open_export_folder(self, *args):
        """Reveal the anim Export folder (or the shot root if not created yet)."""
        target = None
        if self.export_base and os.path.isdir(self.export_base):
            target = self.export_base
        elif self.shot_root and os.path.isdir(self.shot_root):
            target = self.shot_root
        if not target:
            cmds.warning("Export folder doesn't exist yet - export once, or "
                         "save the scene inside the 01_Maya folder structure.")
            return
        try:
            self._open_in_explorer(target)
        except Exception as e:
            cmds.warning("Could not open folder: {}".format(e))

    # ===================================================== gazu install
    @staticmethod
    def _gazu_importable():
        try:
            import gazu  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def _maya_python_exe():
        """Locate Maya's standalone interpreter (mayapy) for pip installs."""
        maya_loc = os.environ.get("MAYA_LOCATION")
        candidates = []
        if maya_loc:
            candidates.append(os.path.join(maya_loc, "bin", "mayapy"))
        # Fallback: alongside the current executable
        candidates.append(os.path.join(os.path.dirname(sys.executable), "mayapy"))
        for cand in candidates:
            for path in (cand, cand + ".exe"):
                if os.path.exists(path):
                    return path
        return None

    def _mark_gazu_installed(self, label="gazu installed"):
        """Remove the install button and show a small 'gazu installed' text."""
        try:
            if self.install_btn and cmds.button(self.install_btn, exists=True):
                cmds.deleteUI(self.install_btn)
        except Exception:
            pass
        self.install_btn = None
        try:
            if self.gazu_status_text and cmds.text(self.gazu_status_text, exists=True):
                cmds.text(self.gazu_status_text, edit=True, label=label)
            else:
                self.gazu_status_text = cmds.text(label=label, align="left",
                                                  parent=self._kcol)
        except Exception:
            pass

    def install_gazu(self, *args):
        """Install gazu into Maya's interpreter. No-op once it is available."""
        global gazu, GAZU_AVAILABLE

        # Already there? Just swap to the text label and stop.
        if GAZU_AVAILABLE or self._gazu_importable():
            GAZU_AVAILABLE = True
            self._mark_gazu_installed()
            return

        py = self._maya_python_exe()
        if not py:
            cmds.confirmDialog(title="Install gazu", message=(
                "Could not locate Maya's Python (mayapy).\n"
                "Install manually with:\n"
                "  \"<MAYA>/bin/mayapy\" -m pip install --user gazu"))
            return

        cmds.button(self.install_btn, edit=True, enable=False, label="Installing...")
        cmds.refresh()

        def run_pip(extra):
            return subprocess.run(
                [py, "-m", "pip"] + extra,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                universal_newlines=True)

        try:
            result = run_pip(["install", "--user", "gazu"])
            # If pip itself is missing, bootstrap it and retry once.
            if result.returncode != 0 and "No module named pip" in (result.stdout or ""):
                subprocess.run([py, "-m", "ensurepip"],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True)
                result = run_pip(["install", "--user", "gazu"])
        except Exception as e:
            cmds.button(self.install_btn, edit=True, enable=True, label="Install gazu")
            cmds.confirmDialog(title="Install gazu",
                               message="Install failed:\n{}".format(e))
            return

        if result.returncode != 0:
            cmds.button(self.install_btn, edit=True, enable=True, label="Install gazu")
            tail = (result.stdout or "")[-1500:]
            cmds.confirmDialog(title="Install gazu",
                               message="pip failed:\n\n{}".format(tail))
            return

        # Installed on disk - make it importable in this session without a restart.
        try:
            import site
            import importlib
            for d in (site.getusersitepackages(),):
                if d and d not in sys.path:
                    sys.path.append(d)
            importlib.invalidate_caches()
            import gazu as _gazu
            gazu = _gazu
            GAZU_AVAILABLE = True
            self._mark_gazu_installed()
        except ImportError:
            self._mark_gazu_installed(label="gazu installed (restart Maya)")
            cmds.confirmDialog(title="Install gazu", message=(
                "gazu was installed but could not be imported into the running "
                "session. Restart Maya and it will be available."))

    # ===================================================== Kitsu connection
    @staticmethod
    def _normalize_kitsu_host(url):
        """
        Turn whatever the user pasted into a valid Gazu API host.

        Accepts the API URL, the bare host, or a Kitsu web URL (e.g. the
        .../productions/<id>/shots page) and reduces it to '<scheme>://<host>/api'.
        """
        url = (url or "").strip()
        if not url:
            return url
        if "://" not in url:
            url = "https://" + url
        p = urlparse(url)
        path = p.path or ""
        idx = path.rfind("/api")
        if idx != -1:
            # Already points at an /api root (possibly under a subpath) - keep it.
            return "{}://{}{}".format(p.scheme, p.netloc, path[:idx + 4])
        return "{}://{}/api".format(p.scheme, p.netloc)

    # ----------------------------------------------------- credential cache
    @staticmethod
    def _creds_cache_path():
        d = os.path.join(cmds.internalVar(userAppDir=True), "playblast_publisher")
        if not os.path.isdir(d):
            os.makedirs(d)
        return os.path.join(d, "kitsu_session.json")

    def _load_creds(self):
        try:
            with open(self._creds_cache_path(), "r") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _save_creds(self, data):
        try:
            with open(self._creds_cache_path(), "w") as f:
                json.dump(data, f)
        except Exception as e:
            cmds.warning("Could not save Kitsu login cache: {}".format(e))

    @staticmethod
    def _obfuscate(text):
        # Light obfuscation only (base64) - NOT real encryption. Keeps the
        # password from being read at a glance in the cache file.
        if not text:
            return ""
        return base64.b64encode(text.encode("utf-8")).decode("ascii")

    @staticmethod
    def _deobfuscate(text):
        if not text:
            return ""
        try:
            return base64.b64decode(text.encode("ascii")).decode("utf-8")
        except Exception:
            return ""

    def forget_creds(self, *args):
        """Delete the cached Kitsu login from disk and clear the fields."""
        try:
            path = self._creds_cache_path()
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            cmds.warning("Could not delete cache: {}".format(e))
        self._set_password("")
        cmds.confirmDialog(title="Kitsu", message="Saved Kitsu login cleared.")

    # ----------------------------------------------------- masked password
    def _build_password_field(self, parent):
        """Create a masked password field (Qt). Falls back to a cmds field."""
        self._pw_is_qt = False
        self._pw_widget = None
        self.kitsu_pass_field = None
        try:
            from maya import OpenMayaUI as omui
            from PySide2.QtWidgets import QLineEdit, QWidget
            try:
                from shiboken2 import wrapInstance
            except ImportError:
                from shiboken import wrapInstance

            prow = cmds.rowLayout(numberOfColumns=2, columnWidth2=(138, 360),
                                  columnAttach=[(1, "right", 4), (2, "left", 3)],
                                  parent=parent)
            cmds.text(label="Password:", parent=prow)
            host = cmds.columnLayout(adjustableColumn=True, parent=prow)
            cmds.setParent(parent)

            ptr = omui.MQtUtil.findControl(host)
            qhost = wrapInstance(int(ptr), QWidget) if ptr else None
            if qhost is None or qhost.layout() is None:
                raise RuntimeError("no Qt layout for host")
            field = QLineEdit()
            field.setEchoMode(QLineEdit.Password)
            field.setPlaceholderText("Kitsu password")
            qhost.layout().addWidget(field)
            self._pw_widget = field
            self._pw_is_qt = True
        except Exception:
            # Fallback: plain cmds field (text will be visible).
            self.kitsu_pass_field = cmds.textFieldGrp(
                label="Password:", parent=parent,
                annotation="Masked field unavailable; text is visible here.")

    def _get_password(self):
        if self._pw_is_qt and self._pw_widget is not None:
            return self._pw_widget.text()
        if self.kitsu_pass_field:
            return cmds.textFieldGrp(self.kitsu_pass_field, q=True, text=True)
        return ""

    def _set_password(self, text):
        if self._pw_is_qt and self._pw_widget is not None:
            self._pw_widget.setText(text or "")
        elif self.kitsu_pass_field:
            cmds.textFieldGrp(self.kitsu_pass_field, edit=True, text=text or "")

    def connect_kitsu(self, *args):
        if not GAZU_AVAILABLE:
            cmds.confirmDialog(title="Kitsu", message=(
                "The 'gazu' package is not installed in Maya's Python.\n\n"
                "Use the 'Install gazu' button, or install manually with:\n"
                "  \"<MAYA>/bin/mayapy\" -m pip install gazu"))
            return

        raw_url = cmds.textFieldGrp(self.kitsu_url_field, q=True, text=True)
        host = self._normalize_kitsu_host(raw_url)
        email = cmds.textFieldGrp(self.kitsu_login_field, q=True, text=True).strip()
        password = self._get_password()

        if not host or not email or not password:
            cmds.confirmDialog(title="Kitsu",
                               message="Please fill in URL, login and password.")
            return

        # Show the user the actual API URL being used.
        cmds.textFieldGrp(self.kitsu_url_field, edit=True, text=host)

        try:
            gazu.set_host(host)
            self.kitsu_user = gazu.log_in(email, password)
            self.kitsu_connected = True
            name = self.kitsu_user.get("user", {}).get("full_name", email) \
                if isinstance(self.kitsu_user, dict) else email
            cmds.text(self.kitsu_status_text, edit=True,
                      label="Status: connected as {}".format(name))
            # Cache the project list and fill the board dropdown.
            try:
                self.kitsu_projects = gazu.project.all_open_projects() or []
            except Exception:
                self.kitsu_projects = []
            names = sorted(p.get("name", "") for p in self.kitsu_projects)
            detected = self._resolve_kitsu_project()
            self._set_project_menu(names, detected.get("name") if detected else None)
            self._last_detected_scene = cmds.file(q=True, sn=True) or ""

            # Save (or clear) the cached login per the Remember checkbox.
            remember = cmds.checkBox(self.remember_check, q=True, value=True)
            if remember:
                self._save_creds({
                    "url": host, "login": email, "remember": True,
                    "pw": self._obfuscate(password),
                })
            else:
                self._save_creds({"url": host, "login": email, "remember": False, "pw": ""})
        except Exception as e:
            self.kitsu_connected = False
            cmds.text(self.kitsu_status_text, edit=True,
                      label="Status: connection failed")
            cmds.confirmDialog(title="Kitsu",
                               message="Login failed:\n{}\n\nAPI URL tried:\n{}".format(e, host))

    def _set_project_menu(self, names, select_name=None):
        """(Re)populate the board dropdown and optionally select an entry."""
        menu = self.kitsu_project_menu
        for item in (cmds.optionMenu(menu, q=True, itemListLong=True) or []):
            cmds.deleteUI(item)
        if not names:
            cmds.menuItem(parent=menu, label="<no projects>")
            return
        for n in names:
            cmds.menuItem(parent=menu, label=n)
        if select_name and select_name in names:
            cmds.optionMenu(menu, edit=True, value=select_name)

    def _selected_project(self):
        """Return the project dict currently chosen in the dropdown."""
        try:
            name = cmds.optionMenu(self.kitsu_project_menu, q=True, value=True)
        except Exception:
            return None
        for proj in (self.kitsu_projects or []):
            if proj.get("name") == name:
                return proj
        return None

    def _resolve_kitsu_project(self):
        """Match a folder in the scene path against the cached Kitsu projects."""
        scene_path = cmds.file(q=True, sn=True) or ""
        parts = [self._normalize(p) for p in re.split(r"[\\/]+", scene_path) if p]
        for proj in (self.kitsu_projects or []):
            if self._normalize(proj.get("name", "")) in parts:
                return proj
        return None

    def _update_kitsu_project_field(self):
        """
        Auto-select the detected board, but only when the scene actually
        changes - so a manual override is preserved across refreshes
        (including the refresh that runs at the start of a render).
        """
        if not self.kitsu_connected:
            return
        scene_path = cmds.file(q=True, sn=True) or ""
        if scene_path == self._last_detected_scene:
            return
        self._last_detected_scene = scene_path
        detected = self._resolve_kitsu_project()
        if detected and detected.get("name"):
            try:
                cmds.optionMenu(self.kitsu_project_menu, edit=True,
                                value=detected["name"])
            except Exception:
                pass

    # ===================================================== Playblast
    @staticmethod
    def _scene_fps():
        """Return the scene's frame rate as a float."""
        unit = cmds.currentUnit(q=True, time=True)
        named = {"game": 15.0, "film": 24.0, "pal": 25.0, "ntsc": 30.0,
                 "show": 48.0, "palf": 50.0, "ntscf": 60.0}
        if unit in named:
            return named[unit]
        m = re.match(r"([\d.]+)\s*fps", unit or "")
        return float(m.group(1)) if m else 24.0

    @staticmethod
    def _ffmpeg_store_dir():
        base = cmds.internalVar(userAppDir=True)
        return os.path.join(base, "playblast_publisher", "ffmpeg")

    def _default_ffmpeg_path(self):
        """The expected FFmpeg location:
        <maya app dir>/playblast_publisher/ffmpeg/
            ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe
        """
        return os.path.join(self._ffmpeg_store_dir(),
                            "ffmpeg-master-latest-win64-gpl", "bin", "ffmpeg.exe")

    def _find_downloaded_ffmpeg(self):
        d = self._ffmpeg_store_dir()
        if not os.path.isdir(d):
            return None
        exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
        for root, _dirs, files in os.walk(d):
            if exe in files:
                return os.path.join(root, exe)
        return None

    def _resolve_ffmpeg(self):
        """Locate ffmpeg: the fixed expected path first, then a nearby copy,
        then PATH."""
        fixed = self._default_ffmpeg_path()
        if os.path.isfile(fixed):
            return fixed
        return self._find_downloaded_ffmpeg() or shutil.which("ffmpeg")

    def _playblast_to_mp4(self, version_folder, base_name, common):
        """
        QuickTime-free path: playblast a local image sequence, then encode it
        to H.264 mp4 with FFmpeg and place the mp4 in version_folder.
        Returns the mp4 path, or None on failure.
        """
        ffmpeg = self._resolve_ffmpeg()
        if not ffmpeg:
            cmds.confirmDialog(title="Playblast", message=(
                "FFmpeg was not found. Place an FFmpeg build at:\n\n{}\n\n"
                "(or anywhere under that ffmpeg folder, or on your PATH)."
                .format(self._default_ffmpeg_path())))
            return None

        temp_dir = tempfile.mkdtemp(prefix="pbpub_")
        try:
            seq_base = os.path.join(temp_dir, base_name)
            seq_opts = dict(common)
            seq_opts.update(filename=seq_base, format="image",
                            compression="jpg", quality=95)
            cmds.playblast(**seq_opts)

            frames = sorted(glob.glob(os.path.join(temp_dir, base_name + ".*.jpg")))
            if not frames:
                cmds.warning("Playblast produced no frames - nothing to encode.")
                return None

            # Derive the numeric pattern from the first frame's padding.
            first = os.path.basename(frames[0])
            digits = first.split(".")[-2]
            pattern = os.path.join(temp_dir, "{}.%0{}d.jpg".format(base_name, len(digits)))
            start_num = int(digits)

            # Encode to LOCAL temp first. Writing the mp4 directly to a network
            # share fails when the muxer seeks back to write the moov atom, so
            # we finalize locally and copy the finished file to the share.
            local_mp4 = os.path.join(temp_dir, base_name + ".mp4")
            cmd = [
                ffmpeg, "-y",
                "-framerate", str(self._scene_fps()),
                "-start_number", str(start_num),
                "-i", pattern,
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-crf", "18",
                # libx264 + yuv420p requires even dimensions.
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                local_mp4,
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, universal_newlines=True)
            if result.returncode != 0:
                tail = (result.stdout or "")[-1500:]
                cmds.confirmDialog(title="FFmpeg", message="Encoding failed:\n\n{}".format(tail))
                return None

            out_mp4 = os.path.join(version_folder, base_name + ".mp4")
            ok, err = self._robust_copy(local_mp4, out_mp4)
            if not ok:
                cmds.confirmDialog(title="Playblast", message=(
                    "Encoded the mp4 locally but could not copy it to:\n{}\n\n{}"
                    .format(out_mp4, err)))
                return None
            return out_mp4
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _robust_copy(src, dst):
        """
        Copy src -> dst with fallbacks for flaky network shares.

        shutil.copy2 copies metadata (os.utime) which can raise
        '[Errno 9] Bad file descriptor' on SMB shares, so we avoid it and
        fall back to robocopy (built for resilient network copies on Windows).
        """
        last = None
        # 1) Data-only copy (no metadata) - fixes the copystat EBADF case.
        try:
            shutil.copyfile(src, dst)
            return True, None
        except Exception as e:
            last = e
        # 2) Windows robocopy. Source and destination file names match here.
        if os.name == "nt":
            src_dir, name = os.path.split(src)
            dst_dir, _ = os.path.split(dst)
            try:
                r = subprocess.run(
                    ["robocopy", src_dir, dst_dir, name,
                     "/R:3", "/W:2", "/IS", "/NJH", "/NJS", "/NP", "/NFL", "/NDL"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    universal_newlines=True)
                # robocopy uses exit codes 0-7 for success, 8+ for failure.
                if r.returncode < 8 and os.path.exists(dst):
                    return True, None
                last = RuntimeError("robocopy exit {}:\n{}".format(
                    r.returncode, (r.stdout or "")[-800:]))
            except Exception as e:
                last = e
        # 3) Manual chunked copy as a last resort.
        try:
            with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
                while True:
                    chunk = fsrc.read(1024 * 1024)
                    if not chunk:
                        break
                    fdst.write(chunk)
            return True, None
        except Exception as e:
            last = e
        return False, last

    # Display categories that make up rig "controls" / viewport overlays.
    # Geometry (polymeshes, nurbsSurfaces, subdivs) is deliberately left on.
    _CONTROL_DISPLAY_FLAGS = (
        "nurbsCurves", "locators", "handles", "ikHandles", "deformers",
        "dynamicConstraints", "pivots", "dimensions", "controlVertices",
        "hulls", "motionTrails",
    )

    def _visible_model_panels(self):
        """All visible model panels (so whichever one playblast uses is covered)."""
        panels = [p for p in (cmds.getPanel(visiblePanels=True) or [])
                  if cmds.getPanel(typeOf=p) == "modelPanel"]
        if panels:
            return panels
        focus = cmds.getPanel(withFocus=True)
        if focus and cmds.getPanel(typeOf=focus) == "modelPanel":
            return [focus]
        allm = cmds.getPanel(type="modelPanel") or []
        return allm[:1]

    def _hide_controls(self):
        """Turn off control/overlay display on the visible model panel(s).

        Returns (panels, saved) so the prior state can be restored afterwards.
        Returns (None, None) if there's no model panel to act on.
        """
        panels = self._visible_model_panels()
        if not panels:
            return None, None
        saved = {}
        for panel in panels:
            flags = {}
            for flag in self._CONTROL_DISPLAY_FLAGS:
                try:
                    flags[flag] = cmds.modelEditor(panel, q=True, **{flag: True})
                except Exception:
                    continue
            for flag in flags:
                try:
                    cmds.modelEditor(panel, e=True, **{flag: False})
                except Exception:
                    pass
            saved[panel] = flags
        return panels, saved

    def _restore_controls(self, panels, saved):
        """Restore the display flags captured by _hide_controls."""
        for panel in (panels or []):
            if cmds.getPanel(typeOf=panel) != "modelPanel":
                continue
            for flag, value in (saved.get(panel, {}) or {}).items():
                try:
                    cmds.modelEditor(panel, e=True, **{flag: value})
                except Exception:
                    pass

    # Camera gate overlays that draw the green resolution text etc.
    _CAMERA_GATE_ATTRS = (
        "displayResolution", "displayFilmGate", "displayGateMask",
        "displaySafeAction", "displaySafeTitle", "displayFieldChart",
    )

    @staticmethod
    def _panel_camera(panel):
        try:
            cam = cmds.modelEditor(panel, q=True, camera=True)
        except Exception:
            return None
        if not cam:
            return None
        if cmds.objectType(cam) == "camera":
            return cam
        shapes = cmds.listRelatives(cam, shapes=True, type="camera", fullPath=True) or []
        return shapes[0] if shapes else None

    def _hide_camera_gates(self):
        """Turn off resolution/film-gate overlays on the visible panels' cameras.

        Returns {camera_shape: {attr: prior_value}} for restoration.
        """
        saved = {}
        for panel in self._visible_model_panels():
            cam = self._panel_camera(panel)
            if not cam or cam in saved:
                continue
            attrs = {}
            for a in self._CAMERA_GATE_ATTRS:
                full = "{}.{}".format(cam, a)
                if not cmds.objExists(full):
                    continue
                try:
                    attrs[a] = cmds.getAttr(full)
                    cmds.setAttr(full, 0)
                except Exception:
                    pass
            saved[cam] = attrs
        return saved

    def _restore_camera_gates(self, saved):
        for cam, attrs in (saved or {}).items():
            for a, v in attrs.items():
                try:
                    cmds.setAttr("{}.{}".format(cam, a), v)
                except Exception:
                    pass

    def render_playblast(self, *args):
        self.refresh_info()

        if not self.movies_dir:
            cmds.confirmDialog(title="Playblast", message=(
                "Could not resolve the movies folder. Make sure the scene is "
                "saved inside the project's shots structure (e.g. "
                ".../<project>/04_shots/.../SQ03_SH070/...)."))
            return

        # movies/<SQ>/<SH> - files go straight in, versioned by file name.
        if not os.path.exists(self.movies_dir):
            os.makedirs(self.movies_dir)
            print("Created playblast folder: {}".format(self.movies_dir))

        # Version = the editable field (defaults to the project version, e.g.
        # v022 from SQ03_SH070_v022). Re-rendering the same version overwrites.
        field_txt = cmds.textFieldButtonGrp(self.next_version_field, q=True, text=True)
        version = self._normalize_version(field_txt) or self.scene_version or "v001"
        self.next_version = version

        # Animation-exporter naming: <shot>_<start>_<end>_<version>
        base_name = "{}_{}_{}_{}".format(
            self.shot_name, self.start_frame, self.end_frame, version)

        start, end = self._get_bake_range()

        # Resolution and scale are locked to 1920x1080 @ 100%.
        common = dict(
            forceOverwrite=True,
            clearCache=True,
            viewer=False,
            offScreen=True,
            showOrnaments=False,
            percent=100,
            widthHeight=(1920, 1080),
            startTime=start,
            endTime=end,
            framePadding=4,
        )

        # Always hide rig controls and the camera resolution/film-gate overlays
        # (the green "960x540" text) for the duration of the capture.
        panel, saved_flags = self._hide_controls()
        gates_saved = self._hide_camera_gates()

        try:
            produced = self._playblast_to_mp4(self.movies_dir, base_name, common)
            if not produced:
                return
        finally:
            if panel and saved_flags:
                self._restore_controls(panel, saved_flags)
            self._restore_camera_gates(gates_saved)

        print("Playblast written: {}".format(produced))

        if cmds.checkBox(self.publish_check, q=True, value=True):
            if self.kitsu_connected:
                self.publish_to_kitsu(produced)
            else:
                cmds.warning("Not connected to Kitsu - skipped publish.")

        cmds.confirmDialog(title="Playblast Complete", message=(
            "Playblast saved to:\n{}".format(self.movies_dir)))

    # ===================================================== Kitsu publish
    @staticmethod
    def _name_candidates(prefix, digits):
        """
        Build Kitsu name candidates for a SQ/SH number, tolerant of zero-padding
        differences between Maya and Kitsu.

        Padding is inconsistent across boards (e.g. Maya 'SQ01_sh0020' maps to
        'SQ01'/'SH020' on one board but 'SQ010'/'SH020' on another), so this
        covers: the exact digits, one fewer / one extra leading zero, the numeric
        value at common fixed widths, and one extra / one fewer trailing zero.
        Ordered most-likely first; the resolver takes the first that exists, so
        the exact form always wins when it is present.
        """
        prefix = prefix.upper()
        out = []

        def add(d):
            name = prefix + d
            if d and name not in out:
                out.append(name)

        add(digits)                                       # exact
        if digits.startswith("0") and len(digits) > 1:
            add(digits[1:])                               # one fewer leading zero
        add("0" + digits)                                 # one extra leading zero
        value = digits.lstrip("0") or "0"
        for width in (2, 3, 4):
            add(value.zfill(width))                       # common fixed widths
        add(digits + "0")                                 # one extra trailing zero
        if digits.endswith("0") and len(digits) > 1:
            add(digits[:-1])                              # one fewer trailing zero
        return out

    @staticmethod
    def _resolve_by_candidates(getter, parent, candidates):
        """Try getter(parent, name) for each candidate; return (entity, name)."""
        for name in candidates:
            entity = getter(parent, name)
            if entity:
                return entity, name
        return None, None

    def _resolve_kitsu_shot(self):
        """
        Resolve the Kitsu shot from the Maya project name.

        The Maya project (e.g. SQ01_sh0020) encodes the sequence and shot
        numbers. Both are matched against the selected board with zero-padding
        tolerance, since Maya and Kitsu pad them differently per board.
        """
        project = self._selected_project()
        if not project:
            raise RuntimeError(
                "No Kitsu board selected. Connect, then pick the target board "
                "from the 'Kitsu Board' dropdown.")
        project_name = project.get("name", "?")

        seq_match = re.search(r"SQ(\d+)", self.project_name or "", re.IGNORECASE)
        shot_match = re.search(r"SH(\d+)", self.project_name or "", re.IGNORECASE)
        if not seq_match or not shot_match:
            raise RuntimeError(
                "Could not parse a sequence (SQxx) and shot (SHxxxx) from the "
                "Maya project name '{}'.".format(self.project_name))

        seq_candidates = self._name_candidates("SQ", seq_match.group(1))
        shot_candidates = self._name_candidates("SH", shot_match.group(1))

        # Collect every sequence on the board that matches a candidate name.
        matched_sequences = []
        for sname in seq_candidates:
            seq = gazu.shot.get_sequence_by_name(project, sname)
            if seq:
                matched_sequences.append((sname, seq))
        if not matched_sequences:
            raise RuntimeError(
                "Sequence not found in board '{}'. Tried: {}.".format(
                    project_name, ", ".join(seq_candidates)))

        # Find the shot in any matched sequence; collect what exists for diagnostics.
        available = []
        for sname, seq in matched_sequences:
            shot, shot_name = self._resolve_by_candidates(
                gazu.shot.get_shot_by_name, seq, shot_candidates)
            if shot:
                print("[Kitsu] Matched {} / {} in board '{}'.".format(
                    sname, shot_name, project_name))
                return shot
            try:
                existing = [s.get("name", "?")
                            for s in (gazu.shot.all_shots_for_sequence(seq) or [])]
            except Exception:
                existing = []
            available.append("{} -> {}".format(sname, ", ".join(existing) or "(no shots)"))

        raise RuntimeError(
            "Shot not found on board '{}'. Tried shot names: {}.\nShots that "
            "exist in the matched sequence(s): {}.".format(
                project_name, ", ".join(shot_candidates), "; ".join(available)))

    def publish_to_kitsu(self, file_path):
        """Upload the playblast as a preview against the chosen task column."""
        column = cmds.optionMenuGrp(self.publish_column_menu, q=True, value=True)
        try:
            shot = self._resolve_kitsu_shot()

            task_type = gazu.task.get_task_type_by_name(column)
            if not task_type:
                cmds.warning("Kitsu: task type '{}' does not exist.".format(column))
                return

            task = self._get_shot_task(shot, task_type)
            if not task:
                cmds.warning("Kitsu: no '{}' task on shot '{}'.".format(column, shot["name"]))
                return

            # Reuse the task's current status so publishing does not change it.
            current_status = task.get("task_status_id")

            comment_text = cmds.textFieldGrp(self.comment_field, q=True, text=True).strip()
            if not comment_text:
                comment_text = "Playblast {}".format(self.next_version)

            comment, preview = gazu.task.publish_preview(
                task,
                current_status,
                comment=comment_text,
                preview_file_path=file_path,
            )
            gazu.task.set_main_preview(preview)
            board = (self._selected_project() or {}).get("name", "?")
            print("[Kitsu] Published {} preview to {} / {} / {}".format(
                self.next_version, board, shot["name"], column))
        except Exception as e:
            cmds.warning("Kitsu publish failed: {}".format(e))

    @staticmethod
    def _get_shot_task(shot, task_type):
        """Find the shot's task for a task type (version-tolerant)."""
        # Primary: the standard 'main' task for this entity + type.
        getter = getattr(gazu.task, "get_task_by_entity", None)
        if getter:
            task = getter(shot, task_type)
            if task:
                return task
        # Fallback: scan all tasks on the shot and match by task type id.
        for t in (gazu.task.all_tasks_for_shot(shot) or []):
            if t.get("task_type_id") == task_type["id"]:
                return t
        return None

    # ===================================================== Landscape export
    def _toggle_landscape_options(self, *args):
        enabled = cmds.checkBox(self.landscape_enable_check, q=True, value=True)
        cmds.columnLayout(self.landscape_options_col, edit=True, manage=enabled)
        if enabled and not cmds.textFieldGrp(self.landscape_name_field, q=True, text=True).strip():
            base = "{}_Blockout".format(self.shot_name) if self.shot_name else "Blockout"
            cmds.textFieldGrp(self.landscape_name_field, edit=True, text=base)

    def browse_landscape_location(self, *args):
        result = cmds.fileDialog2(fileMode=3, dialogStyle=2,
                                  caption="Select Landscape Export Folder",
                                  okCaption="Use Folder",
                                  startingDirectory=(self.landscape_dir or ""))
        if result:
            self.landscape_dir = result[0].replace("\\", "/")
            cmds.textFieldButtonGrp(self.landscape_path_field, edit=True, text=self.landscape_dir)

    def on_landscape_path_edited(self, *args):
        txt = cmds.textFieldButtonGrp(self.landscape_path_field, q=True, text=True).strip()
        self.landscape_dir = txt.replace("\\", "/") if txt else None

    def open_landscape_folder(self, *args):
        target = self.landscape_dir
        if not target or not os.path.isdir(target):
            cmds.warning("Pick an existing export folder first.")
            return
        try:
            self._open_in_explorer(target)
        except Exception as e:
            cmds.warning("Could not open folder: {}".format(e))

    def _refresh_landscape_list(self):
        cmds.textScrollList(self.landscape_list, edit=True, removeAll=True)
        for obj in self.landscape_objects:
            cmds.textScrollList(self.landscape_list, edit=True,
                                append=obj.split("|")[-1])

    def add_landscape_objects(self, *args):
        sel = cmds.ls(selection=True, long=True) or []
        if not sel:
            cmds.warning("Select the objects to export in the outliner first.")
            return
        added = 0
        for obj in sel:
            if obj not in self.landscape_objects:
                self.landscape_objects.append(obj)
                added += 1
        self._refresh_landscape_list()
        print("Added {} object(s) to the landscape export list.".format(added))

    def remove_landscape_objects(self, *args):
        highlighted = cmds.textScrollList(self.landscape_list, q=True, selectItem=True) or []
        if not highlighted:
            cmds.warning("Highlight items in the list to remove them.")
            return
        # Match by short name (what's shown in the list).
        keep = [o for o in self.landscape_objects if o.split("|")[-1] not in highlighted]
        self.landscape_objects = keep
        self._refresh_landscape_list()

    def clear_landscape_objects(self, *args):
        self.landscape_objects = []
        self._refresh_landscape_list()

    def get_landscape_format(self):
        idx = cmds.radioButtonGrp(self.landscape_format_radio, q=True, select=True)
        return {1: ("fbx", "fbx"), 2: ("abc", "abc")}.get(idx, ("fbx", "fbx"))

    def _export_alembic(self, roots, out_path, start, end):
        """Export the given root nodes as an Alembic (.abc) cache over a range."""
        if not roots:
            return False
        if not cmds.pluginInfo("AbcExport", q=True, loaded=True):
            cmds.loadPlugin("AbcExport")
        out = out_path.replace("\\", "/")
        root_flags = " ".join('-root {}'.format(r) for r in roots)
        job = ('-frameRange {} {} -uvWrite -writeVisibility -worldSpace '
               '-eulerFilter -stripNamespaces -dataFormat ogawa {} -file "{}"'
               ).format(int(start), int(end), root_flags, out)
        cmds.AbcExport(j=job)
        return True

    def _export_geo_selected(self, out_path, fmt_type):
        """Export the current selection as static geometry (no animation bake)."""
        out = out_path.replace("\\", "/")
        if fmt_type == "abc":
            roots = cmds.ls(selection=True, long=True) or []
            start = cmds.playbackOptions(q=True, min=True)
            end = cmds.playbackOptions(q=True, max=True)
            self._export_alembic(roots, out, start, end)
        else:  # fbx
            mel.eval("FBXResetExport;")
            mel.eval("FBXExportIncludeChildren -v true;")
            mel.eval("FBXExportInputConnections -v false;")
            mel.eval("FBXExportSkins -v false;")
            mel.eval("FBXExportShapes -v true;")
            mel.eval("FBXExportCameras -v false;")
            mel.eval("FBXExportLights -v false;")
            mel.eval("FBXExportEmbeddedTextures -v false;")
            mel.eval("FBXExportConstraints -v false;")
            mel.eval("FBXExportSmoothMesh -v true;")
            mel.eval("FBXExportInstances -v false;")
            mel.eval("FBXExportReferencedAssetsContent -v true;")
            mel.eval("FBXExportBakeComplexAnimation -v false;")
            mel.eval("FBXExportInAscii -v false;")
            mel.eval("FBXExportUpAxis y;")
            mel.eval('FBXExport -f "{}" -s;'.format(out))

    def export_landscape(self, *args):
        """Export the chosen blockout meshes to the user-specified folder."""
        if not cmds.checkBox(self.landscape_enable_check, q=True, value=True):
            cmds.warning("Enable landscape export first.")
            return

        folder = (cmds.textFieldButtonGrp(self.landscape_path_field, q=True, text=True) or "").strip()
        folder = folder.replace("\\", "/") if folder else (self.landscape_dir or "")
        if not folder:
            cmds.confirmDialog(title="Export Landscape",
                               message="Please specify an export folder (Browse...).")
            return
        self.landscape_dir = folder

        objs = [o for o in self.landscape_objects if cmds.objExists(o)]
        if not objs:
            cmds.confirmDialog(title="Export Landscape", message=(
                "No objects to export. Select meshes in the outliner and click "
                "'Add Selected'."))
            return

        if not os.path.isdir(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                cmds.confirmDialog(title="Export Landscape",
                                   message="Could not create folder:\n{}".format(e))
                return

        fmt_type, ext = self.get_landscape_format()
        base_name = (cmds.textFieldGrp(self.landscape_name_field, q=True, text=True) or "Blockout").strip()
        combine = cmds.checkBox(self.landscape_combine_check, q=True, value=True)
        version = self.get_next_file_version(folder)

        written = []
        prev = cmds.ls(selection=True, long=True) or []
        try:
            if combine:
                cmds.select(objs, r=True)
                out_path = os.path.join(folder, "{}_{}.{}".format(base_name, version, ext))
                self._export_geo_selected(out_path, fmt_type)
                written.append(out_path)
            else:
                for obj in objs:
                    short = obj.split("|")[-1].split(":")[-1]
                    cmds.select(obj, r=True)
                    out_path = os.path.join(folder, "{}_{}.{}".format(short, version, ext))
                    self._export_geo_selected(out_path, fmt_type)
                    written.append(out_path)
        except Exception as e:
            cmds.confirmDialog(title="Export Landscape", message="Export failed:\n{}".format(e))
            return
        finally:
            if prev:
                try:
                    cmds.select(prev, r=True)
                except Exception:
                    pass

        for w in written:
            print("Exported landscape: {}".format(w))
        cmds.confirmDialog(title="Export Landscape", message=(
            "Exported {} file(s) to:\n{}".format(len(written), folder)))

    # ===================================================== Animation export
    def _toggle_export_options(self, *args):
        enabled = cmds.checkBox(self.export_enable_check, q=True, value=True)
        cmds.columnLayout(self.export_options_col, edit=True, manage=enabled)
        if enabled:
            self.refresh_info()

    def get_export_format(self):
        """Returns the selected export format and its file extension."""
        if hasattr(self, "export_format_radio") and \
                cmds.radioButtonGrp(self.export_format_radio, exists=True):
            if cmds.radioButtonGrp(self.export_format_radio, q=True, select=True) == 2:
                return "abc", "abc"
        return "fbx", "fbx"

    def browse_export_location(self, *args):
        result = cmds.fileDialog2(fileMode=3, dialogStyle=2,
                                  caption="Select Export Folder", okCaption="Use Folder",
                                  startingDirectory=(self.export_dir or ""))
        if result:
            self.custom_export_dir = result[0].replace("\\", "/")
            self.export_dir = self.custom_export_dir
            cmds.textFieldButtonGrp(self.export_path_field, edit=True, text=self.export_dir)

    def on_export_path_edited(self, *args):
        txt = cmds.textFieldButtonGrp(self.export_path_field, q=True, text=True).strip()
        if txt:
            self.custom_export_dir = txt.replace("\\", "/")
            self.export_dir = self.custom_export_dir

    def reset_export_location(self, *args):
        self.custom_export_dir = None
        self.refresh_export_info()

    @staticmethod
    def _rig_name_from(ns, fname):
        """Best-effort asset/character name from the namespace, then filename."""
        for source in (ns or "", os.path.splitext(fname or "")[0]):
            m = re.match(r"(.+?)[_\-]?[Rr]ig(?:[_\-.]|\d|$)", source)
            if m and m.group(1):
                return m.group(1).strip("_-")
        # Fallback: namespace with any trailing _NN / digits removed.
        cleaned = re.sub(r"[_\-]?\d+$", "", ns or "")
        return cleaned or (ns or "Asset")

    def find_characters(self):
        """Find rig references and build export entries.

        Detection is namespace-based (so it works even when the reference file
        name doesn't contain '_rig_'). A reference counts as a rig if its file
        name or namespace mentions 'rig', or it has Advanced Skeleton groups.
        Assets/props are split into two kinds:
          - 'asset_joints': the namespace contains joints (e.g. a skinned prop
            like the hoverboard - the animation lives on the joint, not on the
            geometry group), so we export the baked joints.
          - 'asset_geo': no joints - the controls drive a geometry group, so we
            bake that group's transform.
        """
        characters = []
        refs = cmds.file(q=True, r=True) or []

        raw_entries = []
        for ref in refs:
            try:
                ns = cmds.file(ref, q=True, ns=True)
            except Exception:
                ns = None
            if not ns:
                continue
            fname = os.path.basename(ref)

            rig_grp = "{}:rig".format(ns)
            joints_grp = "{}:joints_grp".format(ns)
            deform_grp = "{}:DeformationSystem".format(ns)
            headrig_grp = "{}:headRig_grp".format(ns)
            has_as_new = cmds.objExists(rig_grp) and cmds.objExists(joints_grp)
            has_deform = cmds.objExists(deform_grp)

            looks_like_rig = ("rig" in fname.lower()) or ("rig" in ns.lower())
            if not (looks_like_rig or has_as_new or has_deform):
                continue  # skip env / wireframe / curve / camera references

            character_name = self._rig_name_from(ns, fname)
            has_headrig = cmds.objExists(headrig_grp)

            asset_root = None
            if has_as_new:
                method, rig_type = "New Method (rig + joints_grp)", "as_new"
            elif has_deform:
                method, rig_type = "Original Method (DeformationSystem)", "as_legacy"
            else:
                # No Advanced Skeleton groups -> asset / prop.
                if cmds.ls("{}:*".format(ns), type="joint"):
                    method, rig_type = "Asset / Prop (skinned - joint export)", "asset_joints"
                else:
                    asset_root = self._find_asset_root(ns)
                    if asset_root:
                        method, rig_type = "Asset / Prop (geometry export)", "asset_geo"
                    else:
                        method, rig_type = "No valid groups found", "unknown"

            raw_entries.append({"name": character_name, "namespace": ns,
                                "export_method": method, "has_headrig": has_headrig,
                                "rig_type": rig_type, "asset_root": asset_root})

        name_counts = {}
        for e in raw_entries:
            name_counts[e["name"]] = name_counts.get(e["name"], 0) + 1

        _, ext = self.get_export_format()
        name_index = {}
        for e in raw_entries:
            name = e["name"]
            if name_counts[name] > 1:
                name_index[name] = name_index.get(name, 0) + 1
                suffix = "_{:02d}".format(name_index[name])
            else:
                suffix = ""
            display_name = "{}{}".format(name, suffix)
            base = "{}_{}_{}_{}_{}".format(
                self.shot_name, display_name, self.start_frame, self.end_frame, self.export_version)
            face = "{}_{}_Face_{}_{}_{}".format(
                self.shot_name, display_name, self.start_frame, self.end_frame, self.export_version)
            characters.append({
                "name": name, "display_name": display_name, "namespace": e["namespace"],
                "export_method": e["export_method"], "has_headrig": e["has_headrig"],
                "rig_type": e["rig_type"], "asset_root": e["asset_root"],
                "file_name": "{}.{}".format(base, ext),
                "face_file_name": "{}.{}".format(face, ext),
            })
        return characters

        name_counts = {}
        for e in raw_entries:
            name_counts[e["name"]] = name_counts.get(e["name"], 0) + 1

        _, ext = self.get_export_format()
        name_index = {}
        for e in raw_entries:
            name = e["name"]
            if name_counts[name] > 1:
                name_index[name] = name_index.get(name, 0) + 1
                suffix = "_{:02d}".format(name_index[name])
            else:
                suffix = ""
            display_name = "{}{}".format(name, suffix)
            base = "{}_{}_{}_{}_{}".format(
                self.shot_name, display_name, self.start_frame, self.end_frame, self.export_version)
            face = "{}_{}_Face_{}_{}_{}".format(
                self.shot_name, display_name, self.start_frame, self.end_frame, self.export_version)
            characters.append({
                "name": name, "display_name": display_name, "namespace": e["namespace"],
                "export_method": e["export_method"], "has_headrig": e["has_headrig"],
                "rig_type": e["rig_type"], "asset_root": e["asset_root"],
                "file_name": "{}.{}".format(base, ext),
                "face_file_name": "{}.{}".format(face, ext),
            })
        return characters

    def _common_ancestor(self, nodes):
        if not nodes:
            return None
        split = [n.split("|") for n in nodes]
        common = []
        for tup in zip(*split):
            if all(x == tup[0] for x in tup):
                common.append(tup[0])
            else:
                break
        if not any(c for c in common):
            return None
        path = "|".join(common)
        return path if cmds.objExists(path) else None

    def _find_asset_root(self, ns):
        """Group that holds all (non-intermediate) geometry for an asset rig."""
        shapes = (cmds.ls("{}:*".format(ns), type="mesh", long=True) or [])
        shapes += (cmds.ls("{}:*".format(ns), type="nurbsSurface", long=True) or [])
        if not shapes:
            return None
        geo_transforms = set()
        for s in shapes:
            try:
                if cmds.getAttr(s + ".intermediateObject"):
                    continue
            except Exception:
                pass
            parents = cmds.listRelatives(s, parent=True, fullPath=True) or []
            if parents:
                geo_transforms.add(parents[0])
        if not geo_transforms:
            return None
        return self._common_ancestor(list(geo_transforms))

    def find_camera(self):
        """Find a ShotCam transform (case-insensitive, namespace-agnostic)."""
        for obj in cmds.ls(type="transform", long=True) or []:
            short = obj.split("|")[-1].split(":")[-1]
            if short.lower().startswith("shotcam"):
                if cmds.listRelatives(obj, shapes=True, type="camera"):
                    return obj
        for shape in cmds.ls(type="camera", long=True) or []:
            short = shape.split("|")[-1].split(":")[-1]
            if short.lower().startswith("shotcam"):
                parents = cmds.listRelatives(shape, parent=True, fullPath=True) or []
                if parents:
                    return parents[0]
        return None

    def refresh_export_info(self, *args):
        """Populate export folder/version/range, the character rows and camera."""
        if not hasattr(self, "export_characters_column"):
            return
        export_base = self.export_base or ""
        self.export_version = self.get_next_version(export_base) if export_base else "v001"
        if self.custom_export_dir:
            self.export_dir = self.custom_export_dir
        else:
            self.export_dir = os.path.join(export_base, self.export_version) if export_base else ""

        cmds.textFieldButtonGrp(self.export_path_field, edit=True, text=self.export_dir or "")
        cmds.textFieldGrp(self.export_next_version_field, edit=True, text=self.export_version)
        cmds.textFieldGrp(self.export_frange_field, edit=True,
                          text="{} - {}".format(self.start_frame, self.end_frame))

        for child in (cmds.layout(self.export_characters_column, q=True, childArray=True) or []):
            cmds.deleteUI(child)
        self.export_body_checks = {}
        self.export_face_checks = {}
        self.export_character_data = self.find_characters()

        if self.export_character_data:
            for char in self.export_character_data:
                is_asset = char.get("rig_type", "").startswith("asset")
                row = cmds.rowLayout(numberOfColumns=4, adjustableColumn=3,
                                     columnWidth4=(55, 55, 360, 220),
                                     parent=self.export_characters_column)
                self.export_body_checks[char["namespace"]] = cmds.checkBox(
                    label="Asset" if is_asset else "Body", value=True, parent=row)
                self.export_face_checks[char["namespace"]] = cmds.checkBox(
                    label="Face", value=False, enable=not is_asset, parent=row)
                cmds.text(label=char["file_name"], align="left", parent=row)
                if char["has_headrig"]:
                    cmds.text(label="+ " + char["face_file_name"], align="left", parent=row)
                cmds.setParent("..")
        else:
            cmds.text(label="No characters found with *_Rig references",
                      align="left", parent=self.export_characters_column)

        camera = self.find_camera()
        if camera:
            _, ext = self.get_export_format()
            cam_file = "{}_Cam_{}_{}_{}.{}".format(
                self.shot_name, self.start_frame, self.end_frame, self.export_version, ext)
            cmds.text(self.export_camera_text, edit=True,
                      label="ShotCam: Found  ->  " + cam_file)
        else:
            cmds.text(self.export_camera_text, edit=True, label="ShotCam: Not Found")

    def _apply_fbx_bake_range(self):
        start, end = self._get_bake_range()
        mel.eval("FBXExportBakeComplexStart -v {};".format(start))
        mel.eval("FBXExportBakeComplexEnd -v {};".format(end))
        mel.eval("FBXExportBakeComplexStep -v 1;")
        mel.eval("FBXExportBakeResampleAnimation -v true;")

    def _get_bake_range(self):
        """Export/playblast range, honoring a manual Frame Range override."""
        if self._ov_start is not None and self._ov_end is not None:
            return int(self._ov_start), int(self._ov_end)
        return (int(cmds.playbackOptions(q=True, min=True)),
                int(cmds.playbackOptions(q=True, max=True)))

    def _export_joints_fbx_clean(self, joints_to_export, out_path):
        """Export joints to FBX with namespaces stripped via a temp clean skeleton."""
        if not joints_to_export:
            return False
        sel_set = set(joints_to_export)
        roots = []
        for j in joints_to_export:
            parent = cmds.listRelatives(j, parent=True, fullPath=True) or []
            if not parent or parent[0] not in sel_set:
                roots.append(j)

        dup_roots = []
        try:
            dup_top = cmds.duplicate(roots, returnRootsOnly=True, renameChildren=False) or []
            for dr in dup_top:
                dr_full = cmds.ls(dr, long=True)[0]
                if cmds.listRelatives(dr_full, parent=True):
                    dr_full = cmds.ls(cmds.parent(dr_full, world=True)[0], long=True)[0]
                dup_roots.append(dr_full)

            keep_dups = []
            for orig_root, dup_root in zip(roots, dup_roots):
                orig_chain = [orig_root] + (cmds.listRelatives(orig_root, ad=True, fullPath=True) or [])
                dup_chain = [dup_root] + (cmds.listRelatives(dup_root, ad=True, fullPath=True) or [])
                if len(orig_chain) != len(dup_chain):
                    cmds.warning("Clean FBX export: hierarchy mismatch, aborting.")
                    return False
                for orig_node, dup_node in zip(orig_chain, dup_chain):
                    if not cmds.objExists(dup_node):
                        continue
                    if orig_node in sel_set:
                        try:
                            cmds.parentConstraint(orig_node, dup_node, maintainOffset=False)
                            cmds.scaleConstraint(orig_node, dup_node, maintainOffset=False)
                        except Exception:
                            pass
                        keep_dups.append(dup_node)
                    else:
                        try:
                            cmds.delete(dup_node)
                        except Exception:
                            pass

            keep_dups = [d for d in keep_dups if cmds.objExists(d)]
            if not keep_dups:
                cmds.warning("Clean FBX export: nothing left to export.")
                return False
            cmds.select(keep_dups, r=True)
            self._fbx_export_selected(out_path, include_children=False, skins=False, shapes=False)
            return True
        finally:
            for dr in dup_roots:
                if dr and cmds.objExists(dr):
                    try:
                        cmds.delete(dr)
                    except Exception:
                        pass

    def _fbx_export_selected(self, out_path, include_children, skins, shapes,
                             cameras=False, smooth=False):
        mel.eval("FBXResetExport;")
        mel.eval("FBXExportIncludeChildren -v {};".format("true" if include_children else "false"))
        mel.eval("FBXExportInputConnections -v false;")
        mel.eval("FBXExportSkins -v {};".format("true" if skins else "false"))
        mel.eval("FBXExportShapes -v {};".format("true" if shapes else "false"))
        mel.eval("FBXExportCameras -v {};".format("true" if cameras else "false"))
        mel.eval("FBXExportLights -v false;")
        mel.eval("FBXExportEmbeddedTextures -v false;")
        mel.eval("FBXExportConstraints -v false;")
        mel.eval("FBXExportSmoothMesh -v {};".format("true" if smooth else "false"))
        mel.eval("FBXExportInstances -v false;")
        mel.eval("FBXExportReferencedAssetsContent -v false;")
        mel.eval("FBXExportBakeComplexAnimation -v true;")
        self._apply_fbx_bake_range()
        mel.eval("FBXExportInAscii -v false;")
        mel.eval("FBXExportUpAxis y;")
        mel.eval('FBXExport -f "{}" -s;'.format(out_path.replace("\\", "/")))

    def export_animations(self, *args):
        """Export enabled characters + ShotCam into <shot>/anim/vNNN (or custom)."""
        scene_name, shot_token, _scene_version, scene_path = self.get_scene_info()
        if not scene_path:
            cmds.confirmDialog(title="Export", message="Scene is not saved.")
            return
        self.shot_name = shot_token
        self.start_frame, self.end_frame = self._get_bake_range()

        shot_root = self.find_shot_root(scene_path, shot_token)
        export_base = os.path.join(shot_root, "anim") if shot_root else \
            os.path.join(os.path.dirname(scene_path), "anim")
        self.export_base = export_base

        if self.custom_export_dir:
            self.export_dir = self.custom_export_dir
            self.export_version = self.export_version or self.get_next_version(export_base)
        else:
            self.export_version = self.get_next_version(export_base)
            self.export_dir = os.path.join(export_base, self.export_version)

        # Rebuild names with the current version (does not touch checkboxes).
        self.export_character_data = self.find_characters()

        if not self.export_character_data and not self.find_camera():
            cmds.confirmDialog(title="Export",
                               message="Nothing to export - no characters or camera found.")
            return

        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
            print("Created export directory: {}".format(self.export_dir))

        import time
        prev_eval_mode = cmds.evaluationManager(q=True, mode=True)[0]
        prev_autokey = cmds.autoKeyframe(q=True, state=True)
        prev_cycle_check = cmds.cycleCheck(q=True, e=True)
        main_pane = mel.eval('$tmp = $gMainPane')
        t_start = time.time()

        cmds.refresh(suspend=True)
        try:
            cmds.autoKeyframe(state=False)
            cmds.cycleCheck(e=False)
            try:
                cmds.evaluationManager(mode="parallel")
            except Exception:
                pass
            try:
                cmds.paneLayout(main_pane, edit=True, manage=False)
            except Exception:
                pass

            for char in self.export_character_data:
                body_cb = self.export_body_checks.get(char["namespace"])
                face_cb = self.export_face_checks.get(char["namespace"])
                export_body = cmds.checkBox(body_cb, q=True, value=True) if body_cb else True
                export_face = cmds.checkBox(face_cb, q=True, value=True) if face_cb else False
                if export_body or export_face:
                    self.export_character(char, export_body, export_face)
                else:
                    print("Skipping {} - Body and Face both off".format(char["display_name"]))

            camera = self.find_camera()
            if camera:
                self.export_camera(camera)
        finally:
            try:
                cmds.paneLayout(main_pane, edit=True, manage=True)
            except Exception:
                pass
            try:
                cmds.evaluationManager(mode=prev_eval_mode)
            except Exception:
                pass
            cmds.cycleCheck(e=prev_cycle_check)
            cmds.autoKeyframe(state=prev_autokey)
            cmds.refresh(suspend=False)
            cmds.refresh()

        elapsed = time.time() - t_start
        print("Export finished in {:.1f}s".format(elapsed))
        cmds.confirmDialog(title="Export Complete",
                           message="Export finished in {:.1f}s\nSaved to:\n{}".format(
                               elapsed, self.export_dir))
        self.refresh_export_info()

    def export_character(self, character_data, export_body=True, export_face=False):
        fmt_type, _ = self.get_export_format()
        if fmt_type == "abc":
            # Alembic = baked geometry cache of the deforming meshes.
            if export_body:
                self.export_character_alembic(character_data)
            return

        ns = character_data["namespace"]
        rig_grp = "{}:rig".format(ns)
        joints_grp = "{}:joints_grp".format(ns)
        deform_grp = "{}:DeformationSystem".format(ns)
        headrig_grp = "{}:headRig_grp".format(ns)

        if cmds.objExists(rig_grp) and cmds.objExists(joints_grp):
            if export_body:
                self.export_body_animation(character_data)
            if export_face and cmds.objExists(headrig_grp):
                self.export_face_animation(character_data)
        elif cmds.objExists(deform_grp):
            self.export_legacy_character(character_data, export_body, export_face)
        elif character_data.get("rig_type", "").startswith("asset"):
            if export_body:
                self.export_asset(character_data)

    def export_character_alembic(self, character_data):
        """Export a character/asset's deforming meshes as an Alembic cache."""
        ns = character_data["namespace"]
        root = self._find_asset_root(ns)
        if root:
            roots = [root]
        else:
            meshes = cmds.ls("{}:*".format(ns), type="mesh", long=True) or []
            roots = sorted({(cmds.listRelatives(m, parent=True, fullPath=True)
                             or [None])[0] for m in meshes} - {None})
        if not roots:
            cmds.warning("No geometry to cache for {}".format(character_data["name"]))
            return
        out_path = os.path.join(self.export_dir, character_data["file_name"])
        start, end = self._get_bake_range()
        self._export_alembic(roots, out_path, start, end)
        print("Exported alembic cache {}: {}".format(character_data["name"], out_path))

    def export_asset(self, character_data):
        """Export an asset / prop.

        Skinned props (rig_type 'asset_joints', e.g. the hoverboard) carry their
        animation on a joint that's driven by the control rig - so we export the
        baked joints, the same way a character body is exported. Rigid props
        ('asset_geo') have the controls drive a geometry group, so we bake that
        group's transform.
        """
        out_path = os.path.join(self.export_dir, character_data["file_name"])
        ns = character_data["namespace"]

        if character_data.get("rig_type") == "asset_joints":
            joints = cmds.ls("{}:*".format(ns), type="joint", long=True) or []
            if not joints:
                cmds.warning("No joints to export for asset {}".format(character_data["name"]))
                return
            self._export_joints_fbx_clean(joints, out_path)
            print("Exported asset (joints) {}: {}".format(character_data["name"], out_path))
            return

        asset_root = character_data.get("asset_root")
        if not asset_root or not cmds.objExists(asset_root):
            cmds.warning("No geometry to export for asset {}".format(character_data["name"]))
            return
        self._export_asset_fbx_clean(asset_root, out_path)
        print("Exported asset {}: {}".format(character_data["name"], out_path))

    def _export_asset_fbx_clean(self, asset_root, out_path):
        if not asset_root or not cmds.objExists(asset_root):
            return False
        dup_full = None
        try:
            dup = cmds.duplicate(asset_root, returnRootsOnly=True)[0]
            dup_full = cmds.ls(dup, long=True)[0]
            if cmds.listRelatives(dup_full, parent=True):
                dup_full = cmds.ls(cmds.parent(dup_full, world=True)[0], long=True)[0]
            for n in (cmds.listRelatives(dup_full, ad=True, fullPath=True) or []):
                if cmds.objExists(n) and "Constraint" in cmds.nodeType(n):
                    try:
                        cmds.delete(n)
                    except Exception:
                        pass
            try:
                cmds.parentConstraint(asset_root, dup_full, maintainOffset=False)
                cmds.scaleConstraint(asset_root, dup_full, maintainOffset=False)
            except Exception:
                pass
            cmds.select(dup_full, r=True)
            self._fbx_export_selected(out_path, include_children=True, skins=False, shapes=True)
            return True
        finally:
            if dup_full and cmds.objExists(dup_full):
                try:
                    cmds.delete(dup_full)
                except Exception:
                    pass

    def export_body_animation(self, character_data):
        ns = character_data["namespace"]
        all_joints = cmds.listRelatives("{}:joints_grp".format(ns), ad=True,
                                        fullPath=True, type="joint") or []
        joints = [j for j in all_joints if "FACIAL" not in j.upper()]
        if not joints:
            cmds.warning("No body joints for {}".format(character_data["name"]))
            return
        out_path = os.path.join(self.export_dir, character_data["file_name"])
        self._export_joints_fbx_clean(joints, out_path)
        print("Exported body: {}".format(out_path))

    def export_face_animation(self, character_data):
        ns = character_data["namespace"]
        cmds.select("{}:headRig_grp".format(ns), r=True)
        out_path = os.path.join(self.export_dir, character_data["face_file_name"])
        self._fbx_export_selected(out_path, include_children=True, skins=True,
                                  shapes=True, smooth=True)
        print("Exported face: {}".format(out_path))

    def export_legacy_character(self, character_data, export_body=True, export_face=False):
        ns = character_data["namespace"]
        all_joints = cmds.listRelatives("{}:DeformationSystem".format(ns), ad=True,
                                        fullPath=True, type="joint") or []
        if not all_joints:
            cmds.warning("No joints for {}".format(character_data["name"]))
            return

        if export_body and export_face:
            joints = all_joints
        elif export_body and not export_face:
            exclude = set()
            for fj in [j for j in all_joints if "FaceJoint_M" in j]:
                exclude.add(fj)
                exclude.update(cmds.listRelatives(fj, ad=True, fullPath=True, type="joint") or [])
            joints = [j for j in all_joints if j not in exclude]
        elif not export_body and export_face:
            joints = []
            for fj in [j for j in all_joints if "FaceJoint_M" in j]:
                joints.append(fj)
                joints.extend(cmds.listRelatives(fj, ad=True, fullPath=True, type="joint") or [])
            joints = list(set(joints))
        else:
            print("Skipping {} - Body and Face both off".format(character_data["name"]))
            return

        if not joints:
            cmds.warning("No joints to export for {}".format(character_data["name"]))
            return
        out_path = os.path.join(self.export_dir, character_data["file_name"])
        self._export_joints_fbx_clean(joints, out_path)
        print("Exported legacy character {}: {}".format(character_data["name"], out_path))

    def _bake_camera_duplicate(self, camera, start, end):
        """Return a world-space, fully baked duplicate of the camera.

        Duplicates the ShotCam, frees it to world, constrains it to the original
        so it follows the rig, then bakes the transform per frame and copies any
        animated camera-shape attributes (focal length, apertures, focus). The
        caller is responsible for deleting the returned node.
        """
        dup = cmds.duplicate(camera, returnRootsOnly=True, name="bakedShotCam")[0]
        dup = cmds.ls(dup, long=True)[0]
        if cmds.listRelatives(dup, parent=True):
            dup = cmds.ls(cmds.parent(dup, world=True)[0], long=True)[0]

        # Strip any duplicated constraint nodes that came along.
        for n in (cmds.listRelatives(dup, ad=True, fullPath=True) or []):
            if cmds.objExists(n) and "Constraint" in cmds.nodeType(n):
                try:
                    cmds.delete(n)
                except Exception:
                    pass

        pc = cmds.parentConstraint(camera, dup, maintainOffset=False)
        sc = cmds.scaleConstraint(camera, dup, maintainOffset=False)
        cmds.bakeResults(
            dup, simulation=True, t=(start, end), sampleBy=1,
            disableImplicitControl=True, preserveOutsideKeys=False,
            attribute=["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"])
        for c in (pc, sc):
            try:
                cmds.delete(c)
            except Exception:
                pass

        # Bake animated camera-shape attributes (e.g. focal length).
        orig_shape = (cmds.listRelatives(camera, shapes=True, type="camera",
                                         fullPath=True) or [None])[0]
        dup_shape = (cmds.listRelatives(dup, shapes=True, type="camera",
                                        fullPath=True) or [None])[0]
        if orig_shape and dup_shape:
            for attr in ("focalLength", "horizontalFilmAperture",
                         "verticalFilmAperture", "fStop", "focusDistance",
                         "nearClipPlane", "farClipPlane"):
                src = "{}.{}".format(orig_shape, attr)
                dst = "{}.{}".format(dup_shape, attr)
                if not (cmds.objExists(src) and cmds.objExists(dst)):
                    continue
                if cmds.listConnections(src, s=True, d=False):
                    for f in range(int(start), int(end) + 1):
                        try:
                            cmds.setKeyframe(dst, t=f, v=cmds.getAttr(src, time=f))
                        except Exception:
                            pass
                else:
                    try:
                        cmds.setAttr(dst, cmds.getAttr(src))
                    except Exception:
                        pass
        return dup

    def export_camera(self, camera):
        fmt_type, ext = self.get_export_format()
        cam_file = "{}_Cam_{}_{}_{}.{}".format(
            self.shot_name, self.start_frame, self.end_frame, self.export_version, ext)
        out_path = os.path.join(self.export_dir, cam_file)
        start, end = self._get_bake_range()

        dup = None
        try:
            dup = self._bake_camera_duplicate(camera, start, end)
            cmds.select(dup, r=True)
            if fmt_type == "abc":
                self._export_alembic([dup], out_path, start, end)
            else:
                self._fbx_export_selected(out_path, include_children=False, skins=False,
                                          shapes=False, cameras=True)
        finally:
            if dup and cmds.objExists(dup):
                try:
                    cmds.delete(dup)
                except Exception:
                    pass
        print("Exported camera (baked): {}".format(out_path))


def show_playblast_ui():
    ui = PlayblastPublishUI()
    ui.create_ui()
    return ui


# ===================================================== Shelf installation
def _icon_path():
    """Write the embedded fox icon to a persistent file and return its path."""
    d = os.path.join(cmds.internalVar(userAppDir=True), "playblast_publisher")
    if not os.path.isdir(d):
        os.makedirs(d)
    path = os.path.join(d, "playblast_fox.png")
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(_decode_icon())
    return path


_MODULE_NAME = "playblast_publisher_v2"


def _ensure_importable():
    """
    Make this tool importable (as the module named after this file) so the shelf
    button survives a Maya restart. Returns (ok, message).
    """
    try:
        __import__(_MODULE_NAME)
        return True, "module already importable"
    except Exception:
        pass
    src = globals().get("__file__")
    if src and os.path.isfile(src):
        dst = os.path.join(cmds.internalVar(userScriptDir=True), _MODULE_NAME + ".py")
        try:
            shutil.copyfile(src, dst)
            return True, "installed module to:\n{}".format(dst)
        except Exception as e:
            return False, "could not copy module: {}".format(e)
    return False, None


def install_to_shelf(*args):
    """Create a shelf button for this tool on the active shelf, with the icon."""
    icon = _icon_path()
    importable, msg = _ensure_importable()

    if importable:
        command = (
            "import {m}\n"
            "try:\n"
            "    import importlib\n"
            "    importlib.reload({m})\n"
            "except Exception:\n"
            "    pass\n"
            "{m}.show_playblast_ui()".format(m=_MODULE_NAME)
        )
    else:
        # Session-only fallback: works now, but not after restart.
        command = "show_playblast_ui()"

    shelf_top = mel.eval('$tmp = $gShelfTopLevel')
    current_shelf = cmds.tabLayout(shelf_top, q=True, selectTab=True)

    cmds.shelfButton(
        parent=current_shelf,
        image=icon,
        image1=icon,
        label="PBpub",
        annotation="Playblast Publisher",
        imageOverlayLabel="",
        command=command,
        sourceType="python",
    )

    note = "Added Playblast Publisher to the '{}' shelf.".format(current_shelf)
    if importable:
        note += "\n\n" + (msg or "")
    else:
        note += ("\n\nNote: the button works this session only. To make it "
                 "persist after restarting Maya, save this script as "
                 "'{}.py' in:\n{}\nthen run Install to Shelf "
                 "again.".format(_MODULE_NAME, cmds.internalVar(userScriptDir=True)))
    cmds.confirmDialog(title="Install to Shelf", message=note)


# Launch the UI when the script is run directly. Suppressed only when this file
# is imported as a module (e.g. by the shelf button, which calls show itself).
if __name__ != _MODULE_NAME:
    show_playblast_ui()
