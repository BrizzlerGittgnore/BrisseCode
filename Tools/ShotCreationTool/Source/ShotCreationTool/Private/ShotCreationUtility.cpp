#include "ShotCreationUtility.h"
#include "ShotCreationUtility.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "AssetToolsModule.h"
#include "IAssetTools.h"
#include "EditorAssetLibrary.h"
#include "EditorLevelUtils.h"
#include "LevelEditorSubsystem.h"
#include "FileHelpers.h"
#include "CineCameraActor.h"
#include "Engine/LevelStreamingAlwaysLoaded.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Tracks/MovieSceneSubTrack.h"
#include "Sections/MovieSceneSubSection.h"
#include "Tracks/MovieSceneCameraCutTrack.h"
#include "Sections/MovieSceneCameraCutSection.h"
#include "Tracks/MovieSceneLevelVisibilityTrack.h"
#include "Sections/MovieSceneLevelVisibilitySection.h"
#include "MasterSequenceUtility.h"
#include "MovieScenePossessable.h"
#include "MovieSceneBindingProxy.h"
#include "LevelSequenceEditorSubsystem.h"
#include "ExtensionLibraries/MovieSceneSequenceExtensions.h"

PRAGMA_DISABLE_DEPRECATION_WARNINGS

FString FShotCreationUtility::FormatSeqName(int32 SeqNum)
{
	return FString::Printf(TEXT("sq%02d"), SeqNum);
}

FString FShotCreationUtility::FormatShotName(int32 SeqNum, int32 ShotNum)
{
	return FString::Printf(TEXT("sq%02d_sh%04d"), SeqNum, ShotNum);
}

bool FShotCreationUtility::ShotExistsOnDisk(const FString& BasePath, int32 SeqNum, int32 ShotNum)
{
	const FString SeqName = FormatSeqName(SeqNum);
	const FString ShotName = FString::Printf(TEXT("sh%04d"), ShotNum);
	const FString FullSeqPath = BasePath / SeqName / ShotName / FString::Printf(TEXT("%s_%s"), *SeqName, *ShotName);
	return UEditorAssetLibrary::DoesAssetExist(FullSeqPath);
}

TArray<FShotCreationResult> FShotCreationUtility::CreateShots(const FShotCreationParams& Params, FOnShotCreationLog LogCallback)
{
	TArray<FShotCreationResult> Results;

	for (const FShotDefinition& Shot : Params.Shots)
	{
		FShotCreationResult Result;
		Result.ShotName = FormatShotName(Shot.SequenceNumber, Shot.ShotNumber);

		if (ShotExistsOnDisk(Params.BasePath, Shot.SequenceNumber, Shot.ShotNumber))
		{
			if (!Params.bOverwriteExisting)
			{
				Result.bSkipped = true;
				Result.bSuccess = true;
				Result.Message = TEXT("Already exists - skipped");
				if (LogCallback.IsBound()) LogCallback.Execute(FString::Printf(TEXT("[%s] Already exists, skipping."), *Result.ShotName));
				Results.Add(Result);
				continue;
			}
			const FString SeqName = FormatSeqName(Shot.SequenceNumber);
			const FString ShotName = FString::Printf(TEXT("sh%04d"), Shot.ShotNumber);
			const FString ShotBasePath = Params.BasePath / SeqName / ShotName;
			if (LogCallback.IsBound()) LogCallback.Execute(FString::Printf(TEXT("[%s] Overwriting..."), *Result.ShotName));
			UEditorAssetLibrary::DeleteDirectory(ShotBasePath);
		}

		FString Error;
		if (CreateSingleShot(Params, Shot, LogCallback, Error))
		{
			Result.bSuccess = true;
			Result.Message = TEXT("Created successfully");
		}
		else
		{
			Result.bSuccess = false;
			Result.Message = Error;
		}
		Results.Add(Result);
	}

	return Results;
}

bool FShotCreationUtility::CreateSingleShot(
	const FShotCreationParams& Params,
	const FShotDefinition& Shot,
	FOnShotCreationLog LogCallback,
	FString& OutError)
{
	const FString SeqName = FormatSeqName(Shot.SequenceNumber);
	const FString ShotName = FString::Printf(TEXT("sh%04d"), Shot.ShotNumber);
	const FString FullShotName = FormatShotName(Shot.SequenceNumber, Shot.ShotNumber);
	const FString ShotBasePath = Params.BasePath / SeqName / ShotName;
	const int32 FrameEnd = Params.FrameStart + Shot.FrameDuration + 1;

	auto Log = [&](const FString& Msg)
	{
		UE_LOG(LogTemp, Warning, TEXT("ShotCreation: %s"), *Msg);
		if (LogCallback.IsBound()) LogCallback.Execute(Msg);
	};

	// ==================== FOLDERS ====================
	Log(FString::Printf(TEXT("[%s] Creating directories..."), *FullShotName));
	UEditorAssetLibrary::MakeDirectory(ShotBasePath / TEXT("Levels"));
	UEditorAssetLibrary::MakeDirectory(ShotBasePath / TEXT("Sequences"));
	UEditorAssetLibrary::MakeDirectory(ShotBasePath / TEXT("Anims"));

	// ==================== MAIN LEVEL ====================
	Log(FString::Printf(TEXT("[%s] Creating main level..."), *FullShotName));
	const FString MainLevelPath = ShotBasePath / FString::Printf(TEXT("L_%s_%s"), *SeqName, *ShotName);

	ULevelEditorSubsystem* LevelTools = GEditor->GetEditorSubsystem<ULevelEditorSubsystem>();
	if (!LevelTools)
	{
		OutError = TEXT("Failed to get LevelEditorSubsystem");
		return false;
	}
	LevelTools->NewLevelFromTemplate(MainLevelPath, Params.MainLevelTemplate);

	// ==================== SUB LEVELS ====================
	Log(FString::Printf(TEXT("[%s] Creating %d sub-levels..."), *FullShotName, Params.SubLevelNames.Num()));
	TArray<FString> SubLevelPaths;
	for (const FString& SubName : Params.SubLevelNames)
	{
		const FString SubPath = ShotBasePath / TEXT("Levels") / FString::Printf(TEXT("%s_%s_%s"), *SeqName, *ShotName, *SubName);
		LevelTools->NewLevelFromTemplate(SubPath, Params.SubLevelTemplate);
		SubLevelPaths.Add(SubPath);
	}

	// ==================== LOAD LEVEL + ADD SUBLEVELS ====================
	Log(FString::Printf(TEXT("[%s] Loading level: %s"), *FullShotName, *MainLevelPath));
	UWorld* World = UEditorLoadingAndSavingUtils::LoadMap(MainLevelPath);
	Log(FString::Printf(TEXT("[%s] LoadMap returned: %s"), *FullShotName, World ? TEXT("valid world") : TEXT("NULL")));
	if (!World)
	{
		OutError = FString::Printf(TEXT("Failed to load main level: %s"), *MainLevelPath);
		return false;
	}
	for (const FString& SubPath : SubLevelPaths)
	{
		Log(FString::Printf(TEXT("[%s] Adding sub-level: %s"), *FullShotName, *SubPath));
		TSubclassOf<ULevelStreaming> StreamClass = Params.bUseBlueprintStreaming
			? TSubclassOf<ULevelStreaming>(ULevelStreamingDynamic::StaticClass())
			: TSubclassOf<ULevelStreaming>(ULevelStreamingAlwaysLoaded::StaticClass());
		ULevelStreaming* Result = UEditorLevelUtils::AddLevelToWorld(
			World, *SubPath, StreamClass);
		Log(FString::Printf(TEXT("[%s] AddLevelToWorld returned: %s"), *FullShotName, Result ? TEXT("OK") : TEXT("NULL")));
	}
	bool bSaveResult = UEditorLoadingAndSavingUtils::SaveMap(World, MainLevelPath);
	Log(FString::Printf(TEXT("[%s] SaveMap returned: %s"), *FullShotName, bSaveResult ? TEXT("true") : TEXT("false")));

	// ==================== SEQUENCES ====================
	Log(FString::Printf(TEXT("[%s] Creating sequences..."), *FullShotName));

	const FString MainSeqAssetName = FString::Printf(TEXT("%s_%s"), *SeqName, *ShotName);
	Log(FString::Printf(TEXT("[%s] Creating main sequence: %s in %s"), *FullShotName, *MainSeqAssetName, *ShotBasePath));
	ULevelSequence* MainSequence = CreateLevelSequence(ShotBasePath, MainSeqAssetName);
	Log(FString::Printf(TEXT("[%s] Main sequence: %s, MovieScene: %s"), *FullShotName,
		MainSequence ? TEXT("valid") : TEXT("NULL"),
		(MainSequence && MainSequence->GetMovieScene()) ? TEXT("valid") : TEXT("NULL")));
	if (!MainSequence)
	{
		OutError = FString::Printf(TEXT("Failed to create main sequence: %s"), *MainSeqAssetName);
		return false;
	}

	TMap<FString, ULevelSequence*> SubSequences;
	for (const FString& SubName : Params.SubLevelNames)
	{
		const FString SubSeqName = FString::Printf(TEXT("%s_%s_%s"), *SeqName, *ShotName, *SubName);
		Log(FString::Printf(TEXT("[%s] Creating sub-sequence: %s"), *FullShotName, *SubSeqName));
		ULevelSequence* SubSeq = CreateLevelSequence(ShotBasePath / TEXT("Sequences"), SubSeqName);
		Log(FString::Printf(TEXT("[%s] Sub-sequence %s: %s"), *FullShotName, *SubName,
			SubSeq ? TEXT("valid") : TEXT("NULL")));
		if (SubSeq)
		{
			SetSequencePlaybackRange(SubSeq, Params.FrameStart, FrameEnd, Params.FrameRate);
			UEditorAssetLibrary::SaveAsset(SubSeq->GetPathName(), false);
			SubSequences.Add(SubName, SubSeq);
		}
	}
	Log(FString::Printf(TEXT("[%s] SubSequences map has %d entries"), *FullShotName, SubSequences.Num()));

	// ==================== CAMERA IN CAM SUB-SEQUENCE ====================
	// Python: camera_binding = cam_seq_asset.add_spawnable_from_class(unreal.CineCameraActor)
	//         camera_binding.set_name(f"CAM_{shot_name}")
	ULevelSequence* CamSubSeq = SubSequences.FindRef(TEXT("CAM"));
	Log(FString::Printf(TEXT("[%s] CAM sub-sequence lookup: %s"), *FullShotName,
		CamSubSeq ? *CamSubSeq->GetPathName() : TEXT("NOT FOUND")));
	FMovieSceneBindingProxy CameraBinding;

	if (CamSubSeq)
	{
		Log(FString::Printf(TEXT("[%s] Adding camera to CAM sub-sequence..."), *FullShotName));
		Log(FString::Printf(TEXT("[%s] CamSubSeq->GetMovieScene(): %s"), *FullShotName,
			CamSubSeq->GetMovieScene() ? TEXT("valid") : TEXT("NULL")));
		Log(FString::Printf(TEXT("[%s] CamSubSeq->AllowsSpawnableObjects(): %s"), *FullShotName,
			CamSubSeq->AllowsSpawnableObjects() ? TEXT("YES") : TEXT("NO")));

		// Call CreateSpawnable through UMovieSceneSequence* where it is public.
		// ULevelSequence redeclares it as protected, but the base class version is public.
		// ULevelSequenceEditorSubsystem::AddSpawnableFromClass requires the sequence to be
		// open in the Sequencer UI, so it silently fails when called programmatically.
		UMovieSceneSequence* SeqBase = CamSubSeq;
		FGuid CamGuid = SeqBase->CreateSpawnable(ACineCameraActor::StaticClass());
		Log(FString::Printf(TEXT("[%s] CreateSpawnable returned GUID: %s"), *FullShotName, *CamGuid.ToString()));
		CameraBinding = FMovieSceneBindingProxy(CamGuid, CamSubSeq);

		if (CameraBinding.BindingID.IsValid())
		{
			const FString CameraLabel = FString::Printf(TEXT("CAM_%s"), *ShotName);
			UMovieScene* CamMS = CamSubSeq->GetMovieScene();
			if (CamMS)
			{
				// UE 5.7 CreateSpawnable uses custom bindings which create a Possessable, not a Spawnable
				if (FMovieScenePossessable* Poss = CamMS->FindPossessable(CameraBinding.BindingID))
				{
					Poss->SetName(CameraLabel);
					Log(FString::Printf(TEXT("[%s] Possessable renamed to: %s"), *FullShotName, *CameraLabel));
				}
				else if (FMovieSceneSpawnable* Sp = CamMS->FindSpawnable(CameraBinding.BindingID))
				{
					Sp->SetName(CameraLabel);
					Log(FString::Printf(TEXT("[%s] Spawnable renamed to: %s"), *FullShotName, *CameraLabel));
				}
				else
				{
					Log(FString::Printf(TEXT("[%s] WARNING: Could not find possessable or spawnable for rename"), *FullShotName));
				}
			}
			UEditorAssetLibrary::SaveAsset(CamSubSeq->GetPathName(), false);
			Log(FString::Printf(TEXT("[%s] Camera spawnable created"), *FullShotName));
		}
		else
		{
			Log(FString::Printf(TEXT("[%s] WARNING: Camera creation returned invalid binding"), *FullShotName));
		}
	}
	else
	{
		Log(FString::Printf(TEXT("[%s] WARNING: No CAM sub-sequence found"), *FullShotName));
	}

	// ==================== MAIN SEQUENCE SETUP ====================
	SetSequencePlaybackRange(MainSequence, Params.FrameStart, FrameEnd, Params.FrameRate);

	UMovieScene* MainMovieScene = MainSequence->GetMovieScene();
	if (!MainMovieScene)
	{
		OutError = TEXT("Main sequence has no MovieScene");
		return false;
	}

	// ==================== ADD SUB-SEQUENCES TO MAIN ====================
	// Python: track = main_seq_asset.add_track(unreal.MovieSceneSubTrack)
	//         section = track.add_section()
	//         section.set_range(frame_start, frame_end)
	//         section.set_sequence(sub_asset)
	Log(FString::Printf(TEXT("[%s] Adding sub-sequences to main sequence..."), *FullShotName));

	const FFrameRate DisplayRate(static_cast<int32>(Params.FrameRate), 1);
	const FFrameRate TickResolution = MainMovieScene->GetTickResolution();
	const FFrameNumber StartTick = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(Params.FrameStart)), DisplayRate, TickResolution).FloorToFrame();
	const FFrameNumber EndTick = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(FrameEnd)), DisplayRate, TickResolution).FloorToFrame();
	const int32 DurationTicks = (EndTick - StartTick).Value;

	// Preroll/postroll (50 frames) - used for both sub-sections and camera cut
	const int32 PrerollFrames = 50;
	const int32 PostrollFrames = 50;
	const FFrameNumber PrerollStart = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(Params.FrameStart - PrerollFrames)),
		DisplayRate, TickResolution).FloorToFrame();
	const FFrameNumber PostrollEnd = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(FrameEnd + PostrollFrames)),
		DisplayRate, TickResolution).FloorToFrame();
	const int32 ExtendedDurationTicks = (PostrollEnd - PrerollStart).Value;

	// Per sub-sequence colors: dark muted tones for white text contrast
	static const TMap<FString, FColor> SubTrackColors = {
		{TEXT("GEO"),  FColor(30, 70, 40)},
		{TEXT("LGHT"), FColor(70, 65, 20)},
		{TEXT("FX"),   FColor(60, 30, 65)},
		{TEXT("CHR"),  FColor(25, 50, 75)},
		{TEXT("CAM"),  FColor(75, 35, 30)},
		{TEXT("LVL"),  FColor(50, 50, 50)},
	};

	// ==================== CREATE _LVL SUBSEQUENCE ====================
	const FString LvlSeqName = FString::Printf(TEXT("%s_%s_LVL"), *SeqName, *ShotName);
	Log(FString::Printf(TEXT("[%s] Creating _LVL sub-sequence: %s"), *FullShotName, *LvlSeqName));
	ULevelSequence* LvlSubSeq = CreateLevelSequence(ShotBasePath / TEXT("Sequences"), LvlSeqName);
	if (LvlSubSeq)
	{
		SetSequencePlaybackRange(LvlSubSeq, Params.FrameStart, FrameEnd, Params.FrameRate);

		UMovieScene* LvlMS = LvlSubSeq->GetMovieScene();
		if (LvlMS)
		{
			const FFrameRate LvlDisplayRate(static_cast<int32>(Params.FrameRate), 1);
			const FFrameRate LvlTickRes = LvlMS->GetTickResolution();
			const FFrameNumber LvlStart = FFrameRate::TransformTime(
				FFrameTime(FFrameNumber(Params.FrameStart)), LvlDisplayRate, LvlTickRes).FloorToFrame();
			const FFrameNumber LvlEnd = FFrameRate::TransformTime(
				FFrameTime(FFrameNumber(FrameEnd)), LvlDisplayRate, LvlTickRes).FloorToFrame();
			const TRange<FFrameNumber> LvlRange(LvlStart, LvlEnd);

			// Add visibility track for each sub-level
			for (const FString& SubName : Params.SubLevelNames)
			{
				FString LevelName = FString::Printf(TEXT("%s_%s_%s"), *SeqName, *ShotName, *SubName);
				UMovieSceneLevelVisibilityTrack* VisTrack = LvlMS->AddTrack<UMovieSceneLevelVisibilityTrack>();
				if (VisTrack)
				{
					VisTrack->SetDisplayName(FText::FromString(LevelName));
					UMovieSceneSection* NewSec = VisTrack->CreateNewSection();
					UMovieSceneLevelVisibilitySection* VisSec = Cast<UMovieSceneLevelVisibilitySection>(NewSec);
					if (VisSec)
					{
						VisSec->SetVisibility(ELevelVisibility::Visible);
						VisSec->SetLevelNames({ FName(*LevelName) });
						VisSec->SetRange(LvlRange);
						VisTrack->AddSection(*VisSec);
					}
				}
			}

			// Add environment visibility track if assigned
			FString EnvName = FMasterSequenceUtility::GetSequenceEnvironment(Shot.SequenceNumber);
			if (!EnvName.IsEmpty())
			{
				UMovieSceneLevelVisibilityTrack* EnvTrack = LvlMS->AddTrack<UMovieSceneLevelVisibilityTrack>();
				if (EnvTrack)
				{
					EnvTrack->SetDisplayName(FText::FromString(EnvName));
					UMovieSceneSection* EnvSec = EnvTrack->CreateNewSection();
					UMovieSceneLevelVisibilitySection* EnvVisSec = Cast<UMovieSceneLevelVisibilitySection>(EnvSec);
					if (EnvVisSec)
					{
						EnvVisSec->SetVisibility(ELevelVisibility::Visible);
						EnvVisSec->SetLevelNames({ FName(*EnvName) });
						EnvVisSec->SetRange(LvlRange);
						EnvTrack->AddSection(*EnvVisSec);
					}
				}
				Log(FString::Printf(TEXT("[%s] Added env visibility track: %s"), *FullShotName, *EnvName));
			}
		}

		UEditorAssetLibrary::SaveAsset(LvlSubSeq->GetPathName(), false);
		SubSequences.Add(TEXT("LVL"), LvlSubSeq);
		Log(FString::Printf(TEXT("[%s] _LVL sub-sequence created with %d visibility tracks"), *FullShotName, Params.SubLevelNames.Num()));
	}

	Log(FString::Printf(TEXT("[%s] StartTick=%d EndTick=%d PrerollStart=%d PostrollEnd=%d"),
		*FullShotName, StartTick.Value, EndTick.Value, PrerollStart.Value, PostrollEnd.Value));
	for (auto& Pair : SubSequences)
	{
		Log(FString::Printf(TEXT("[%s] Adding sub-track: %s -> %s"), *FullShotName, *Pair.Key, *Pair.Value->GetPathName()));
		UMovieSceneSubTrack* SubTrack = MainMovieScene->AddTrack<UMovieSceneSubTrack>();
		Log(FString::Printf(TEXT("[%s] SubTrack: %s"), *FullShotName, SubTrack ? TEXT("valid") : TEXT("NULL")));
		if (SubTrack)
		{
			SubTrack->SetDisplayName(FText::FromString(Pair.Key));
			if (const FColor* TrackColor = SubTrackColors.Find(Pair.Key))
			{
				SubTrack->SetColorTint(*TrackColor);
			}
			UMovieSceneSubSection* SubSection = SubTrack->AddSequence(Pair.Value, PrerollStart, ExtendedDurationTicks);
			Log(FString::Printf(TEXT("[%s] SubSection: %s"), *FullShotName, SubSection ? TEXT("valid") : TEXT("NULL")));
			if (SubSection)
			{
				// Set StartFrameOffset to -50 display frames (in tick resolution)
				// This makes the sub-sequence start playing from 50 frames before its own playback start
				const FFrameNumber OffsetTicks = FFrameRate::TransformTime(
					FFrameTime(FFrameNumber(-PrerollFrames)),
					DisplayRate, TickResolution).FloorToFrame();
				SubSection->Parameters.StartFrameOffset = OffsetTicks;
			}
		}
	}

	// ==================== SAVE + RELOAD TO BUILD HIERARCHY ====================
	// Python: unreal.EditorAssetLibrary.save_asset(...)
	//         main_seq_asset = unreal.load_asset(...)
	const FString MainSeqPath = MainSequence->GetPathName();
	Log(FString::Printf(TEXT("[%s] Saving main sequence: %s"), *FullShotName, *MainSeqPath));
	MainSequence->MarkPackageDirty();
	bool bSaved = UEditorAssetLibrary::SaveAsset(MainSeqPath, false);
	Log(FString::Printf(TEXT("[%s] SaveAsset returned: %s"), *FullShotName, bSaved ? TEXT("true") : TEXT("false")));
	Log(FString::Printf(TEXT("[%s] Reloading main sequence..."), *FullShotName));
	MainSequence = LoadObject<ULevelSequence>(nullptr, *MainSeqPath);
	MainMovieScene = MainSequence ? MainSequence->GetMovieScene() : nullptr;
	Log(FString::Printf(TEXT("[%s] After reload: Sequence=%s MovieScene=%s"), *FullShotName,
		MainSequence ? TEXT("valid") : TEXT("NULL"),
		MainMovieScene ? TEXT("valid") : TEXT("NULL")));

	if (!MainSequence || !MainMovieScene)
	{
		OutError = TEXT("Failed to reload main sequence after adding sub-tracks");
		return false;
	}

	// ==================== CAMERA CUT TRACK ====================
	// Python: camera_cut_track = main_seq_asset.add_track(unreal.MovieSceneCameraCutTrack)
	//         camera_cut_section = camera_cut_track.add_section()
	//         camera_cut_section.set_range(frame_start, frame_end)
	//         portable_binding_id = main_seq_asset.get_portable_binding_id(main_seq_asset, camera_binding)
	//         camera_cut_section.set_camera_binding_id(portable_binding_id)
	Log(FString::Printf(TEXT("[%s] CameraBinding valid: %s (GUID: %s)"), *FullShotName,
		CameraBinding.BindingID.IsValid() ? TEXT("YES") : TEXT("NO"),
		*CameraBinding.BindingID.ToString()));
	if (CameraBinding.BindingID.IsValid())
	{
		Log(FString::Printf(TEXT("[%s] Creating camera cut track..."), *FullShotName));

		UMovieSceneCameraCutTrack* CutTrack = MainMovieScene->AddTrack<UMovieSceneCameraCutTrack>();
		if (CutTrack)
		{
			UMovieSceneCameraCutSection* CutSection =
				Cast<UMovieSceneCameraCutSection>(CutTrack->CreateNewSection());
			if (CutSection)
			{
				CutSection->SetRange(TRange<FFrameNumber>(PrerollStart, PostrollEnd));
				CutTrack->AddSection(*CutSection);

				FMovieSceneObjectBindingID PortableID =
					UMovieSceneSequenceExtensions::GetPortableBindingID(
						MainSequence,
						MainSequence,
						CameraBinding);
				CutSection->SetCameraBindingID(PortableID);

				Log(FString::Printf(TEXT("[%s] Camera cut track created (preroll %d, postroll %d)"),
					*FullShotName, PrerollFrames, PostrollFrames));
			}
		}
	}
	else
	{
		Log(FString::Printf(TEXT("[%s] Skipping camera cut (no valid camera binding)"), *FullShotName));
	}

	// ==================== FINAL SAVE ====================
	MainSequence->MarkPackageDirty();
	UEditorAssetLibrary::SaveAsset(MainSequence->GetPathName(), false);

	Log(FString::Printf(TEXT("[%s] Done! Frames: %d-%d"), *FullShotName, Params.FrameStart, FrameEnd));
	return true;
}

ULevelSequence* FShotCreationUtility::CreateLevelSequence(const FString& AssetPath, const FString& AssetName)
{
	const FString FullPath = AssetPath / AssetName;

	if (FPackageName::DoesPackageExist(FullPath))
	{
		return LoadObject<ULevelSequence>(nullptr, *FullPath);
	}

	IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
	UObject* NewAsset = AssetTools.CreateAsset(AssetName, AssetPath, ULevelSequence::StaticClass(), nullptr);

	ULevelSequence* NewSequence = Cast<ULevelSequence>(NewAsset);
	if (NewSequence && !NewSequence->GetMovieScene())
	{
		NewSequence->Initialize();
	}
	return NewSequence;
}

void FShotCreationUtility::SetSequencePlaybackRange(ULevelSequence* Sequence, int32 FrameStart, int32 FrameEnd, float FrameRate)
{
	if (!Sequence) return;
	UMovieScene* MovieScene = Sequence->GetMovieScene();
	if (!MovieScene) return;

	const FFrameRate DisplayRate(static_cast<int32>(FrameRate), 1);
	MovieScene->SetDisplayRate(DisplayRate);

	const FFrameRate TickResolution = MovieScene->GetTickResolution();
	const FFrameNumber Start = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(FrameStart)), DisplayRate, TickResolution).FloorToFrame();
	const FFrameNumber End = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(FrameEnd)), DisplayRate, TickResolution).FloorToFrame();

	MovieScene->SetPlaybackRange(TRange<FFrameNumber>(Start, End));
}

TArray<FShotDefinition> FShotCreationUtility::ScanExistingShots(const FString& BasePath)
{
	TArray<FShotDefinition> Found;

	// Scan for sq## folders
	TArray<FString> SeqFolders;
	IFileManager::Get().FindFiles(SeqFolders, *(FPackageName::LongPackageNameToFilename(BasePath) / TEXT("sq*")), false, true);

	for (const FString& SeqFolder : SeqFolders)
	{
		// Parse sequence number from "sq##"
		if (SeqFolder.Len() >= 4 && SeqFolder.StartsWith(TEXT("sq")))
		{
			int32 SeqNum = FCString::Atoi(*SeqFolder.Mid(2));
			if (SeqNum <= 0) continue;

			// Scan for sh#### folders inside this sequence
			const FString SeqPath = BasePath / SeqFolder;
			TArray<FString> ShotFolders;
			IFileManager::Get().FindFiles(ShotFolders, *(FPackageName::LongPackageNameToFilename(SeqPath) / TEXT("sh*")), false, true);

			for (const FString& ShotFolder : ShotFolders)
			{
				if (ShotFolder.Len() >= 6 && ShotFolder.StartsWith(TEXT("sh")))
				{
					int32 ShotNum = FCString::Atoi(*ShotFolder.Mid(2));
					if (ShotNum <= 0) continue;

					// Verify the main sequence asset exists
					const FString MainSeqAsset = SeqPath / ShotFolder / FString::Printf(TEXT("%s_%s"), *SeqFolder, *ShotFolder);
					if (UEditorAssetLibrary::DoesAssetExist(MainSeqAsset))
					{
						FShotDefinition Def;
						Def.SequenceNumber = SeqNum;
						Def.ShotNumber = ShotNum;
						Def.FrameDuration = 0; // Unknown for existing shots
						Found.Add(Def);
					}
				}
			}
		}
	}

	return Found;
}

PRAGMA_ENABLE_DEPRECATION_WARNINGS