#pragma once

#include "CoreMinimal.h"

class ULevelSequence;
class UWorld;

DECLARE_DELEGATE_OneParam(FOnMasterLog, const FString&);

struct FEnvironmentInfo
{
	FString Name;        // e.g. "ENV_Forest"
	FString LevelPath;   // e.g. "/Game/Environments/ENV_Forest"
};

/**
 * Manages Master Level, Master Sequence, environment assignments, and sync.
 * Non-destructive: only appends to Master, never removes or reorders.
 */
class FMasterSequenceUtility
{
public:
	// ==================== MASTER CREATION ====================

	/** Create empty Master Level and Master Sequence at BasePath. */
	static bool CreateMaster(
		const FString& BasePath,
		const FString& MasterLevelTemplate,
		float FrameRate,
		FOnMasterLog LogCallback,
		FString& OutError);

	// ==================== SYNC ====================

	/**
	 * Sync Master with all existing shots on disk.
	 * - Appends new sub-levels to Master Level (Blueprint streaming)
	 * - Appends new shot sub-tracks to Master Sequence (at end)
	 * - Never removes or reorders existing content
	 * - Skips shots already synced (tracked in config)
	 */
	static bool SyncMaster(
		const FString& BasePath,
		float FrameRate,
		int32 FrameStart,
		FOnMasterLog LogCallback,
		FString& OutError);

	// ==================== ENVIRONMENT ====================

	/** Swap environment for a sequence. Updates all _LVL subsequences in that seq. */
	static bool SwapEnvironment(
		const FString& BasePath,
		int32 SeqNum,
		const FString& OldEnvName,
		const FString& NewEnvLevelPath,
		float FrameRate,
		FOnMasterLog LogCallback,
		FString& OutError);

	// ==================== CONFIG ====================

	static FString GetMasterLevelPath(const FString& BasePath);
	static FString GetMasterSequencePath(const FString& BasePath);
	static bool MasterExists(const FString& BasePath);

	/** Get/Set environment assignment for a sequence. */
	static FString GetSequenceEnvironment(int32 SeqNum);
	static void SetSequenceEnvironment(int32 SeqNum, const FString& EnvName);

	/** Get/Set environment library (list of available env level paths). */
	static TArray<FEnvironmentInfo> GetEnvironmentLibrary();
	static void AddEnvironmentToLibrary(const FString& Name, const FString& LevelPath);
	static void RemoveEnvironmentFromLibrary(const FString& Name);

	/** Check if a shot was ever synced to master (won't re-add if deleted by user). */
	static bool WasShotSyncedToMaster(int32 SeqNum, int32 ShotNum);
	static void MarkShotSyncedToMaster(int32 SeqNum, int32 ShotNum);

private:
	static bool AppendSubLevelsToMasterLevel(
		UWorld* MasterWorld,
		const TArray<FString>& SubLevelPaths,
		FOnMasterLog LogCallback);

	static bool AppendShotToMasterSequence(
		ULevelSequence* MasterSeq,
		ULevelSequence* ShotSeq,
		const FString& DisplayName,
		int32 FrameStart,
		int32 FrameEnd,
		float FrameRate,
		FOnMasterLog LogCallback);

	static FString ConfigSection() { return TEXT("ShotCreationTool"); }
};
