using UnrealBuildTool;

public class ShotCreationTool : ModuleRules
{
    public ShotCreationTool(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(
            new string[]
            {
                "Core",
                "CoreUObject",
                "Engine",
                "InputCore",
                "Slate",
                "SlateCore",
                "LevelSequence",
                "LevelSequenceEditor",
                "MovieScene",
                "MovieSceneTracks",
                "AssetTools",
                "AssetRegistry",
                "UnrealEd",
                "ToolMenus",
                "EditorScriptingUtilities",
                "LevelEditor",
                "CinematicCamera",
                "EditorSubsystem",
                "SequencerScripting"
            }
        );
    }
}
