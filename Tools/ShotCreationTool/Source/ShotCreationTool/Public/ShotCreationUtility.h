#pragma once

#include "CoreMinimal.h"

class ULevelSequence;
class UWorld;

struct FShotDefinition
{
	int32 SequenceNumber = 1;
	int32 ShotNumber = 10;
	int32 FrameDuration = 150;
};

struct FShotCreationParams
{
	FString BasePath = TEXT("/Game/Cinematics/Shots");
	FString MainLevelTemplate = TEXT("/ShotCreationTool/L_Main");
	FString SubLevelTemplate = TEXT("/ShotCreationTool/L_Sublvl");
	int32 FrameStart = 1001;
	float FrameRate = 24.0f;
	bool bOverwriteExisting = false;
	bool bUseBlueprintStreaming = true;
	TArray<FString> SubLevelNames;
	TArray<FShotDefinition> Shots;

	/** Environment level name (e.g. "ENV_Forest") per sequence, looked up from config. */
	TMap<int32, FString> SequenceEnvironments;

	FShotCreationParams()
	{
		SubLevelNames = { TEXT("GEO"), TEXT("LGHT"), TEXT("FX"), TEXT("CHR"), TEXT("CAM") };
	}
};

struct FShotCreationResult
{
	FString ShotName;
	bool bSuccess = false;
	bool bSkipped = false;
	FString Message;
};

DECLARE_DELEGATE_OneParam(FOnShotCreationLog, const FString&);

class FShotCreationUtility
{
public:
	static TArray<FShotCreationResult> CreateShots(const FShotCreationParams& Params, FOnShotCreationLog LogCallback);
	static FString FormatShotName(int32 SeqNum, int32 ShotNum);
	static FString FormatSeqName(int32 SeqNum);
	static bool ShotExistsOnDisk(const FString& BasePath, int32 SeqNum, int32 ShotNum);

	/** Scan BasePath for existing sequence/shot folders. Returns array of {SeqNum, ShotNum, 0} for found shots. */
	static TArray<FShotDefinition> ScanExistingShots(const FString& BasePath);

private:
	static bool CreateSingleShot(const FShotCreationParams& Params, const FShotDefinition& Shot, FOnShotCreationLog LogCallback, FString& OutError);
	static ULevelSequence* CreateLevelSequence(const FString& Path, const FString& Name);
	static void SetSequencePlaybackRange(ULevelSequence* Sequence, int32 FrameStart, int32 FrameEnd, float FrameRate);
};
