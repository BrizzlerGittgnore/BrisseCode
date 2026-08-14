#include "MasterSequenceUtility.h"
#include "ShotCreationUtility.h"
#include "LevelSequence.h"
#include "MovieScene.h"
#include "AssetToolsModule.h"
#include "IAssetTools.h"
#include "EditorAssetLibrary.h"
#include "EditorLevelUtils.h"
#include "LevelEditorSubsystem.h"
#include "FileHelpers.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Engine/LevelStreamingAlwaysLoaded.h"
#include "Tracks/MovieSceneSubTrack.h"
#include "Sections/MovieSceneSubSection.h"
#include "Tracks/MovieSceneLevelVisibilityTrack.h"
#include "Sections/MovieSceneLevelVisibilitySection.h"
#include "Misc/ConfigCacheIni.h"

PRAGMA_DISABLE_DEPRECATION_WARNINGS

// ============================================================
// Paths
// ============================================================

FString FMasterSequenceUtility::GetMasterLevelPath(const FString& BasePath)
{
	return BasePath / TEXT("L_Master");
}

FString FMasterSequenceUtility::GetMasterSequencePath(const FString& BasePath)
{
	return BasePath / TEXT("MSQ_Master");
}

bool FMasterSequenceUtility::MasterExists(const FString& BasePath)
{
	return UEditorAssetLibrary::DoesAssetExist(GetMasterSequencePath(BasePath));
}

// ============================================================
// Config helpers
// ============================================================

FString FMasterSequenceUtility::GetSequenceEnvironment(int32 SeqNum)
{
	FString Val;
	GConfig->GetString(TEXT("ShotCreationTool.SequenceEnv"), *FString::Printf(TEXT("sq%02d"), SeqNum), Val, GEditorPerProjectIni);
	return Val;
}

void FMasterSequenceUtility::SetSequenceEnvironment(int32 SeqNum, const FString& EnvName)
{
	GConfig->SetString(TEXT("ShotCreationTool.SequenceEnv"), *FString::Printf(TEXT("sq%02d"), SeqNum), *EnvName, GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

TArray<FEnvironmentInfo> FMasterSequenceUtility::GetEnvironmentLibrary()
{
	TArray<FEnvironmentInfo> Result;
	FString LibStr;
	GConfig->GetString(TEXT("ShotCreationTool.Environments"), TEXT("Library"), LibStr, GEditorPerProjectIni);
	if (LibStr.IsEmpty()) return Result;

	TArray<FString> Entries;
	LibStr.ParseIntoArray(Entries, TEXT("|"));
	for (const FString& Entry : Entries)
	{
		FString Name, Path;
		if (Entry.Split(TEXT("="), &Name, &Path))
		{
			Result.Add({ Name, Path });
		}
	}
	return Result;
}

void FMasterSequenceUtility::AddEnvironmentToLibrary(const FString& Name, const FString& LevelPath)
{
	TArray<FEnvironmentInfo> Lib = GetEnvironmentLibrary();
	for (const auto& E : Lib)
	{
		if (E.Name == Name) return; // already exists
	}
	Lib.Add({ Name, LevelPath });

	FString LibStr;
	for (const auto& E : Lib)
	{
		if (!LibStr.IsEmpty()) LibStr += TEXT("|");
		LibStr += E.Name + TEXT("=") + E.LevelPath;
	}
	GConfig->SetString(TEXT("ShotCreationTool.Environments"), TEXT("Library"), *LibStr, GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

void FMasterSequenceUtility::RemoveEnvironmentFromLibrary(const FString& Name)
{
	TArray<FEnvironmentInfo> Lib = GetEnvironmentLibrary();
	Lib.RemoveAll([&](const FEnvironmentInfo& E) { return E.Name == Name; });

	FString LibStr;
	for (const auto& E : Lib)
	{
		if (!LibStr.IsEmpty()) LibStr += TEXT("|");
		LibStr += E.Name + TEXT("=") + E.LevelPath;
	}
	GConfig->SetString(TEXT("ShotCreationTool.Environments"), TEXT("Library"), *LibStr, GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

bool FMasterSequenceUtility::WasShotSyncedToMaster(int32 SeqNum, int32 ShotNum)
{
	bool Val = false;
	FString Key = FString::Printf(TEXT("sq%02d_sh%04d"), SeqNum, ShotNum);
	GConfig->GetBool(TEXT("ShotCreationTool.SyncedToMaster"), *Key, Val, GEditorPerProjectIni);
	return Val;
}

void FMasterSequenceUtility::MarkShotSyncedToMaster(int32 SeqNum, int32 ShotNum)
{
	FString Key = FString::Printf(TEXT("sq%02d_sh%04d"), SeqNum, ShotNum);
	GConfig->SetBool(TEXT("ShotCreationTool.SyncedToMaster"), *Key, true, GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

// ============================================================
// Create Master
// ============================================================

bool FMasterSequenceUtility::CreateMaster(
	const FString& BasePath,
	const FString& MasterLevelTemplate,
	float FrameRate,
	FOnMasterLog LogCallback,
	FString& OutError)
{
	auto Log = [&](const FString& Msg)
	{
		UE_LOG(LogTemp, Warning, TEXT("MasterSeq: %s"), *Msg);
		if (LogCallback.IsBound()) LogCallback.Execute(Msg);
	};

	// Create Master Level
	const FString MasterLevelPath = GetMasterLevelPath(BasePath);
	Log(FString::Printf(TEXT("Creating Master Level: %s"), *MasterLevelPath));

	ULevelEditorSubsystem* LevelTools = GEditor->GetEditorSubsystem<ULevelEditorSubsystem>();
	if (!LevelTools)
	{
		OutError = TEXT("Failed to get LevelEditorSubsystem");
		return false;
	}

	if (!UEditorAssetLibrary::DoesAssetExist(MasterLevelPath))
	{
		LevelTools->NewLevelFromTemplate(MasterLevelPath, MasterLevelTemplate);
		// NewLevelFromTemplate opens the level but doesn't always save it to disk
		// We need to explicitly save the current world as the master level
		UWorld* NewWorld = GEditor->GetEditorWorldContext().World();
		if (NewWorld)
		{
			UEditorLoadingAndSavingUtils::SaveMap(NewWorld, MasterLevelPath);
		}
		Log(TEXT("Master Level created and saved."));
	}
	else
	{
		Log(TEXT("Master Level already exists, skipping."));
	}

	// Create Master Sequence
	const FString MasterSeqPath = GetMasterSequencePath(BasePath);
	Log(FString::Printf(TEXT("Creating Master Sequence: %s"), *MasterSeqPath));

	if (!UEditorAssetLibrary::DoesAssetExist(MasterSeqPath))
	{
		IAssetTools& AssetTools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools").Get();
		FString SeqDir = FPaths::GetPath(MasterSeqPath);
		FString SeqName = FPaths::GetBaseFilename(MasterSeqPath);
		UObject* NewAsset = AssetTools.CreateAsset(SeqName, SeqDir, ULevelSequence::StaticClass(), nullptr);
		ULevelSequence* MasterSeq = Cast<ULevelSequence>(NewAsset);
		if (MasterSeq)
		{
			if (!MasterSeq->GetMovieScene()) MasterSeq->Initialize();
			UMovieScene* MS = MasterSeq->GetMovieScene();
			if (MS)
			{
				const FFrameRate DisplayRate(static_cast<int32>(FrameRate), 1);
				MS->SetDisplayRate(DisplayRate);
			}
			UEditorAssetLibrary::SaveAsset(MasterSeq->GetPathName(), false);
			Log(TEXT("Master Sequence created."));
		}
		else
		{
			OutError = TEXT("Failed to create Master Sequence asset");
			return false;
		}
	}
	else
	{
		Log(TEXT("Master Sequence already exists, skipping."));
	}

	return true;
}

// ============================================================
// Sync Master
// ============================================================

bool FMasterSequenceUtility::SyncMaster(
	const FString& BasePath,
	float FrameRate,
	int32 FrameStart,
	FOnMasterLog LogCallback,
	FString& OutError)
{
	auto Log = [&](const FString& Msg)
	{
		UE_LOG(LogTemp, Warning, TEXT("MasterSync: %s"), *Msg);
		if (LogCallback.IsBound()) LogCallback.Execute(Msg);
	};

	if (!MasterExists(BasePath))
	{
		OutError = TEXT("Master does not exist. Create it first.");
		return false;
	}

	// Load Master Sequence
	const FString MasterSeqPath = GetMasterSequencePath(BasePath);
	ULevelSequence* MasterSeq = LoadObject<ULevelSequence>(nullptr, *MasterSeqPath);
	if (!MasterSeq)
	{
		OutError = FString::Printf(TEXT("Failed to load Master Sequence: %s"), *MasterSeqPath);
		return false;
	}

	// Load Master Level
	const FString MasterLevelPath = GetMasterLevelPath(BasePath);
	UWorld* MasterWorld = UEditorLoadingAndSavingUtils::LoadMap(MasterLevelPath);
	if (!MasterWorld)
	{
		OutError = FString::Printf(TEXT("Failed to load Master Level: %s"), *MasterLevelPath);
		return false;
	}

	// Scan existing shots
	TArray<FShotDefinition> ExistingShots = FShotCreationUtility::ScanExistingShots(BasePath);
	Log(FString::Printf(TEXT("Found %d shots on disk."), ExistingShots.Num()));

	int32 ShotsAdded = 0;
	int32 ShotsSkipped = 0;

	for (const FShotDefinition& Shot : ExistingShots)
	{
		const FString SeqName = FShotCreationUtility::FormatSeqName(Shot.SequenceNumber);
		const FString ShotName = FString::Printf(TEXT("sh%04d"), Shot.ShotNumber);
		const FString FullName = FShotCreationUtility::FormatShotName(Shot.SequenceNumber, Shot.ShotNumber);

		// Skip if already synced (even if user deleted the track)
		if (WasShotSyncedToMaster(Shot.SequenceNumber, Shot.ShotNumber))
		{
			ShotsSkipped++;
			continue;
		}

		// Append sub-levels to Master Level (Blueprint streaming)
		const FString ShotBasePath = BasePath / SeqName / ShotName;
		TArray<FString> SubLevelNames = { TEXT("GEO"), TEXT("LGHT"), TEXT("FX"), TEXT("CHR"), TEXT("CAM") };
		TArray<FString> SubLevelPaths;
		for (const FString& Sub : SubLevelNames)
		{
			SubLevelPaths.Add(ShotBasePath / TEXT("Levels") / FString::Printf(TEXT("%s_%s_%s"), *SeqName, *ShotName, *Sub));
		}

		// Also add environment level if assigned
		FString EnvName = GetSequenceEnvironment(Shot.SequenceNumber);
		if (!EnvName.IsEmpty())
		{
			TArray<FEnvironmentInfo> Lib = GetEnvironmentLibrary();
			for (const auto& E : Lib)
			{
				if (E.Name == EnvName)
				{
					SubLevelPaths.AddUnique(E.LevelPath);
					break;
				}
			}
		}

		AppendSubLevelsToMasterLevel(MasterWorld, SubLevelPaths, LogCallback);

		// Append shot sequence to Master Sequence
		const FString ShotSeqAssetPath = ShotBasePath / FString::Printf(TEXT("%s_%s"), *SeqName, *ShotName);
		ULevelSequence* ShotSeq = LoadObject<ULevelSequence>(nullptr, *ShotSeqAssetPath);
		if (ShotSeq)
		{
			int32 Duration = Shot.FrameDuration > 0 ? Shot.FrameDuration : 150;
			int32 FrameEnd = FrameStart + Duration + 1;
			AppendShotToMasterSequence(MasterSeq, ShotSeq, FullName, FrameStart, FrameEnd, FrameRate, LogCallback);
		}

		MarkShotSyncedToMaster(Shot.SequenceNumber, Shot.ShotNumber);
		ShotsAdded++;
		Log(FString::Printf(TEXT("Synced: %s"), *FullName));
	}

	// Save
	UEditorLoadingAndSavingUtils::SaveMap(MasterWorld, MasterLevelPath);
	MasterSeq->MarkPackageDirty();
	UEditorAssetLibrary::SaveAsset(MasterSeq->GetPathName(), false);

	Log(FString::Printf(TEXT("Sync complete: %d added, %d already synced."), ShotsAdded, ShotsSkipped));
	return true;
}

// ============================================================
// Environment Swap
// ============================================================

bool FMasterSequenceUtility::SwapEnvironment(
	const FString& BasePath,
	int32 SeqNum,
	const FString& OldEnvName,
	const FString& NewEnvLevelPath,
	float FrameRate,
	FOnMasterLog LogCallback,
	FString& OutError)
{
	auto Log = [&](const FString& Msg)
	{
		UE_LOG(LogTemp, Warning, TEXT("EnvSwap: %s"), *Msg);
		if (LogCallback.IsBound()) LogCallback.Execute(Msg);
	};

	// Derive new env name from path
	FString NewEnvName = FPaths::GetBaseFilename(NewEnvLevelPath);

	// Verify new env level exists
	if (!UEditorAssetLibrary::DoesAssetExist(NewEnvLevelPath))
	{
		OutError = FString::Printf(TEXT("Environment level does not exist: %s"), *NewEnvLevelPath);
		return false;
	}

	const FString SeqName = FShotCreationUtility::FormatSeqName(SeqNum);

	// Append new env to Master Level
	if (MasterExists(BasePath))
	{
		const FString MasterLevelPath = GetMasterLevelPath(BasePath);
		UWorld* MasterWorld = UEditorLoadingAndSavingUtils::LoadMap(MasterLevelPath);
		if (MasterWorld)
		{
			AppendSubLevelsToMasterLevel(MasterWorld, { NewEnvLevelPath }, LogCallback);
			UEditorLoadingAndSavingUtils::SaveMap(MasterWorld, MasterLevelPath);
		}
	}

	// Find all shots in this sequence
	TArray<FShotDefinition> AllShots = FShotCreationUtility::ScanExistingShots(BasePath);
	int32 Updated = 0;

	for (const FShotDefinition& Shot : AllShots)
	{
		if (Shot.SequenceNumber != SeqNum) continue;

		const FString ShotName = FString::Printf(TEXT("sh%04d"), Shot.ShotNumber);
		const FString ShotBasePath = BasePath / SeqName / ShotName;
		const FString LvlSeqPath = ShotBasePath / TEXT("Sequences") / FString::Printf(TEXT("%s_%s_LVL"), *SeqName, *ShotName);

		ULevelSequence* LvlSeq = LoadObject<ULevelSequence>(nullptr, *LvlSeqPath);
		if (!LvlSeq)
		{
			Log(FString::Printf(TEXT("WARNING: No _LVL sequence for %s, skipping"), *ShotName));
			continue;
		}

		UMovieScene* MS = LvlSeq->GetMovieScene();
		if (!MS) continue;

		// Remove old env visibility tracks (find by level name)
		if (!OldEnvName.IsEmpty())
		{
			TArray<UMovieSceneTrack*> TracksToRemove;
			for (UMovieSceneTrack* Track : MS->GetTracks())
			{
				UMovieSceneLevelVisibilityTrack* LVT = Cast<UMovieSceneLevelVisibilityTrack>(Track);
				if (!LVT) continue;
				for (UMovieSceneSection* Section : LVT->GetAllSections())
				{
					UMovieSceneLevelVisibilitySection* LVS = Cast<UMovieSceneLevelVisibilitySection>(Section);
					if (LVS && LVS->GetLevelNames().Contains(FName(*OldEnvName)))
					{
						TracksToRemove.Add(Track);
						break;
					}
				}
			}
			for (UMovieSceneTrack* T : TracksToRemove)
			{
				MS->RemoveTrack(*T);
			}
		}

		// Add new env visibility track
		if (!NewEnvName.IsEmpty())
		{
			UMovieSceneLevelVisibilityTrack* NewTrack = MS->AddTrack<UMovieSceneLevelVisibilityTrack>();
			if (NewTrack)
			{
				NewTrack->SetDisplayName(FText::FromString(NewEnvName));
				UMovieSceneSection* NewSection = NewTrack->CreateNewSection();
				UMovieSceneLevelVisibilitySection* LVS = Cast<UMovieSceneLevelVisibilitySection>(NewSection);
				if (LVS)
				{
					LVS->SetVisibility(ELevelVisibility::Visible);
					LVS->SetLevelNames({ FName(*NewEnvName) });

					const FFrameRate DisplayRate(static_cast<int32>(FrameRate), 1);
					const FFrameRate TickResolution = MS->GetTickResolution();
					TRange<FFrameNumber> PlayRange = MS->GetPlaybackRange();
					LVS->SetRange(PlayRange);

					NewTrack->AddSection(*LVS);
				}
			}
		}

		LvlSeq->MarkPackageDirty();
		UEditorAssetLibrary::SaveAsset(LvlSeq->GetPathName(), false);
		Updated++;
		Log(FString::Printf(TEXT("Updated _LVL for %s_%s"), *SeqName, *ShotName));
	}

	// Update config
	SetSequenceEnvironment(SeqNum, NewEnvName);
	AddEnvironmentToLibrary(NewEnvName, NewEnvLevelPath);

	Log(FString::Printf(TEXT("Environment swap complete: %d shots updated"), Updated));
	return true;
}

// ============================================================
// Internal: Append sub-levels to Master Level
// ============================================================

bool FMasterSequenceUtility::AppendSubLevelsToMasterLevel(
	UWorld* MasterWorld,
	const TArray<FString>& SubLevelPaths,
	FOnMasterLog LogCallback)
{
	if (!MasterWorld) return false;

	auto Log = [&](const FString& Msg)
	{
		if (LogCallback.IsBound()) LogCallback.Execute(Msg);
	};

	// Get existing streaming level package names
	TSet<FString> ExistingLevels;
	for (ULevelStreaming* Existing : MasterWorld->GetStreamingLevels())
	{
		if (Existing)
		{
			ExistingLevels.Add(Existing->GetWorldAssetPackageName());
		}
	}

	for (const FString& SubPath : SubLevelPaths)
	{
		// Convert asset path to package name for comparison
		FString PackageName = SubPath;
		if (ExistingLevels.Contains(PackageName))
		{
			Log(FString::Printf(TEXT("  Already in Master Level: %s"), *SubPath));
			continue;
		}

		// Check if the level package exists on disk (umap file)
		FString MapFilePath = FPackageName::LongPackageNameToFilename(SubPath, FPackageName::GetMapPackageExtension());
		if (!FPaths::FileExists(MapFilePath))
		{
			Log(FString::Printf(TEXT("  Level not found on disk, skipping: %s"), *SubPath));
			continue;
		}

		ULevelStreaming* Result = UEditorLevelUtils::AddLevelToWorld(
			MasterWorld, *SubPath,
			TSubclassOf<ULevelStreaming>(ULevelStreamingDynamic::StaticClass()));

		if (Result)
		{
			Result->SetShouldBeVisible(false);
			Log(FString::Printf(TEXT("  Added to Master Level (hidden): %s"), *SubPath));
		}
		else
		{
			Log(FString::Printf(TEXT("  FAILED to add to Master Level: %s"), *SubPath));
		}
	}

	return true;
}

// ============================================================
// Internal: Append shot track to Master Sequence
// ============================================================

bool FMasterSequenceUtility::AppendShotToMasterSequence(
	ULevelSequence* MasterSeq,
	ULevelSequence* ShotSeq,
	const FString& DisplayName,
	int32 FrameStart,
	int32 FrameEnd,
	float FrameRate,
	FOnMasterLog LogCallback)
{
	if (!MasterSeq || !ShotSeq) return false;

	auto Log = [&](const FString& Msg)
	{
		if (LogCallback.IsBound()) LogCallback.Execute(Msg);
	};

	UMovieScene* MS = MasterSeq->GetMovieScene();
	if (!MS) return false;

	const FFrameRate DisplayRate(static_cast<int32>(FrameRate), 1);
	const FFrameRate TickResolution = MS->GetTickResolution();

	const FFrameNumber StartTick = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(FrameStart)), DisplayRate, TickResolution).FloorToFrame();
	const FFrameNumber EndTick = FFrameRate::TransformTime(
		FFrameTime(FFrameNumber(FrameEnd)), DisplayRate, TickResolution).FloorToFrame();
	const int32 DurationTicks = (EndTick - StartTick).Value;

	UMovieSceneSubTrack* SubTrack = MS->AddTrack<UMovieSceneSubTrack>();
	if (SubTrack)
	{
		SubTrack->SetDisplayName(FText::FromString(DisplayName));
		SubTrack->AddSequence(ShotSeq, StartTick, DurationTicks);
		Log(FString::Printf(TEXT("  Added to Master Sequence: %s"), *DisplayName));

		// Expand master playback range to include this shot
		TRange<FFrameNumber> CurrentRange = MS->GetPlaybackRange();
		FFrameNumber NewLower = CurrentRange.HasLowerBound() ? FMath::Min(CurrentRange.GetLowerBoundValue(), StartTick) : StartTick;
		FFrameNumber NewUpper = CurrentRange.HasUpperBound() ? FMath::Max(CurrentRange.GetUpperBoundValue(), EndTick) : EndTick;
		MS->SetPlaybackRange(TRange<FFrameNumber>(NewLower, NewUpper));
	}

	return true;
}

PRAGMA_ENABLE_DEPRECATION_WARNINGS
