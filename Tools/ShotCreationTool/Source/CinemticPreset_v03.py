import unreal

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------
shot_name = "sh0010"
Seq_name = "sq01"
base_path = f"/Game/01_BabyBird/Shots/{Seq_name}/{shot_name}"

level_names = ["GEO", "LGHT", "FX", "CHR", "CAM"]

frame_start = 1001
frame_duration = 150
frame_end = frame_start + frame_duration + 1

# --------------------------------------------------
# FOLDERS
# --------------------------------------------------
unreal.EditorAssetLibrary.make_directory(f"{base_path}/Levels")
unreal.EditorAssetLibrary.make_directory(f"{base_path}/Sequences")
unreal.EditorAssetLibrary.make_directory(f"{base_path}/Anims")

# --------------------------------------------------
# MAIN LEVEL
# --------------------------------------------------
level_tools = unreal.LevelEditorSubsystem()
main_level_path = f"{base_path}/L_{Seq_name}_{shot_name}"

level_tools.new_level_from_template(
    main_level_path,
    "/Game/Cinematics/L_Main"
)

# --------------------------------------------------
# SUB LEVELS
# --------------------------------------------------
sub_levels = []
for name in level_names:
    path = f"{base_path}/Levels/{shot_name}_{name}"
    level_tools.new_level_from_template(
        path,
        "/Game/Cinematics/L_Sublvl"
    )
    sub_levels.append(path)

# --------------------------------------------------
# LOAD LEVEL + ADD SUBLEVELS
# --------------------------------------------------
world = unreal.EditorLoadingAndSavingUtils.load_map(main_level_path)

for lvl in sub_levels:
    unreal.EditorLevelUtils.add_level_to_world(
        world,
        lvl,
        unreal.LevelStreamingAlwaysLoaded
    )
unreal.EditorLoadingAndSavingUtils.save_map(world, main_level_path  )
# --------------------------------------------------
# SEQUENCES
# --------------------------------------------------
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
seq_factory = unreal.LevelSequenceFactoryNew()

# Main sequence
main_seq = asset_tools.create_asset(
    f"{Seq_name}_{shot_name}",
    base_path,
    None,
    seq_factory
)

# Sub sequences
sub_seqs = {}
for name in level_names:
    sub_seq = asset_tools.create_asset(
        f"{shot_name}_{name}",
        f"{base_path}/Sequences",
        None,
        seq_factory
    )
    sub_seqs[name] = sub_seq

# --------------------------------------------------
# SUB PLAYBACK RANGE
# --------------------------------------------------
for sub_seq in sub_seqs.values():
    asset = unreal.load_asset(sub_seq.get_path_name())
    asset.set_playback_start(frame_start)
    asset.set_playback_end(frame_end)
    unreal.EditorAssetLibrary.save_asset(asset.get_path_name())

# --------------------------------------------------
# CAMERA IN CAM SUB-SEQUENCE
# --------------------------------------------------
cam_seq_asset = unreal.load_asset(sub_seqs["CAM"].get_path_name())

camera_binding = cam_seq_asset.add_spawnable_from_class(
    unreal.CineCameraActor
)
camera_binding.set_name(f"CAM_{shot_name}")

unreal.EditorAssetLibrary.save_asset(cam_seq_asset.get_path_name())

# --------------------------------------------------
# MAIN SEQUENCE SETUP
# --------------------------------------------------
main_seq_asset = unreal.load_asset(main_seq.get_path_name())
main_seq_asset.set_playback_start(frame_start)
main_seq_asset.set_playback_end(frame_end)

# --------------------------------------------------
# ADD SUB-SEQUENCES TO MAIN
# --------------------------------------------------
for sub_seq in sub_seqs.values():
    sub_asset = unreal.load_asset(sub_seq.get_path_name())
    track = main_seq_asset.add_track(unreal.MovieSceneSubTrack)
    section = track.add_section()
    section.set_range(frame_start, frame_end)
    section.set_sequence(sub_asset)

# --------------------------------------------------
# SAVE + RELOAD TO BUILD HIERARCHY
# --------------------------------------------------
unreal.EditorAssetLibrary.save_asset(main_seq_asset.get_path_name())
main_seq_asset = unreal.load_asset(main_seq_asset.get_path_name())

# --------------------------------------------------
# CAMERA CUT TRACK
# --------------------------------------------------
camera_cut_track = main_seq_asset.add_track(
    unreal.MovieSceneCameraCutTrack
)
camera_cut_section = camera_cut_track.add_section()
camera_cut_section.set_range(frame_start, frame_end)

# --------------------------------------------------
# PORTABLE BINDING (CORRECT)
# --------------------------------------------------
portable_binding_id = main_seq_asset.get_portable_binding_id(
    main_seq_asset,   # destination sequence
    camera_binding   # binding from CAM sub-sequence
)

camera_cut_section.set_camera_binding_id(portable_binding_id)

# --------------------------------------------------
# SAVE
# --------------------------------------------------
unreal.EditorAssetLibrary.save_asset(main_seq_asset.get_path_name())
unreal.LevelEditorSubsystem.save_all_dirty_levels()
print(
    f"Shot {shot_name} created\n"
    f"Frames: {frame_start}-{frame_end}\n"
    f"Camera binding: PORTABLE ({portable_binding_id})"
)
