#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "ShotCreationUtility.h"
#include "MasterSequenceUtility.h"

class SEditableTextBox;
template<typename NumericType> class SSpinBox;
class SButton;
class STextBlock;
class SWidgetSwitcher;

/** Tree node: sequence header, real shot, ghost shot, or ghost sequence */
struct FShotTreeItem
{
	bool bIsSequenceHeader = false;
	bool bExistsOnDisk = false;
	bool bIsPendingCreation = false;
	bool bIsGhost = false;
	int32 SequenceNumber = 1;
	int32 ShotNumber = 0;
	int32 FrameDuration = 150;

	TArray<TSharedPtr<FShotTreeItem>> Children;

	FString GetDisplayName() const
	{
		if (bIsSequenceHeader)
			return FString::Printf(TEXT("sq%02d"), SequenceNumber);
		return FString::Printf(TEXT("sh%04d"), ShotNumber);
	}
};

/** Environment entry for the overview list */
struct FEnvListEntry
{
	FString Name;
	FString LevelPath;
};

class SShotCreationWidget : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SShotCreationWidget) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

private:
	// ==================== TAB BUILDING ====================
	TSharedRef<SWidget> BuildShotCreationTab();
	TSharedRef<SWidget> BuildMasterSetupTab();
	TSharedRef<SWidget> BuildSequenceOverviewTab();

	// ==================== SHOT CREATION TAB ====================
	TSharedRef<SWidget> BuildPathSection();
	TSharedRef<SWidget> BuildSettingsSection();
	TSharedRef<SWidget> BuildAddShotSection();
	TSharedRef<SWidget> BuildShotTreeSection();
	TSharedRef<SWidget> BuildOutputSection();

	TSharedRef<ITableRow> OnGenerateTreeRow(TSharedPtr<FShotTreeItem> Item, const TSharedRef<STableViewBase>& OwnerTable);
	void OnGetTreeChildren(TSharedPtr<FShotTreeItem> Item, TArray<TSharedPtr<FShotTreeItem>>& OutChildren);

	FReply OnAddShotClicked();
	FReply OnBatchAddClicked();
	FReply OnRemoveSelectedClicked();
	FReply OnClearPendingClicked();
	FReply OnCreateShotsClicked();
	FReply OnRefreshClicked();
	FReply OnAddGhostShot(int32 SeqNum, int32 ShotNum);
	FReply OnAddGhostSequence(int32 SeqNum);

	TSharedPtr<SWidget> OnContextMenuOpening();
	void InsertShotBefore(TSharedPtr<FShotTreeItem> Item);
	void InsertShotAfter(TSharedPtr<FShotTreeItem> Item);
	int32 CalculateMidpoint(int32 A, int32 B) const;

	// ==================== MASTER SETUP TAB ====================
	FReply OnCreateMasterClicked();
	FReply OnSyncMasterClicked();

	// ==================== SEQUENCE OVERVIEW TAB ====================
	TSharedRef<SWidget> BuildOverviewSequenceList();
	FReply OnSwapEnvironment(int32 SeqNum);
	FReply OnAddEnvironmentClicked();
	FReply OnRemoveEnvironment(const FString& Name);
	void RefreshOverview();

	// ==================== HELPERS ====================
	void AppendLog(const FString& Text);
	bool ShotExistsInTree(int32 SeqNum, int32 ShotNum) const;
	void RebuildTree();
	void AddPendingShot(int32 SeqNum, int32 ShotNum, int32 Duration);
	void SaveSettings();
	void LoadSettings();
	int32 GetNextShotNumber(int32 SeqNum) const;
	int32 GetNextSequenceNumber() const;
	FLinearColor GetSubSequenceColor(int32 Index) const;

	TSharedPtr<FShotTreeItem> FindOrCreateSequenceNode(int32 SeqNum);
	TSharedPtr<FShotTreeItem> FindShotInSequence(TSharedPtr<FShotTreeItem> SeqNode, int32 ShotNum) const;

	// ==================== DATA ====================
	TArray<TSharedPtr<FShotTreeItem>> TreeRoots;
	TSharedPtr<FShotTreeItem> GhostSequenceNode;
	TSharedPtr<STreeView<TSharedPtr<FShotTreeItem>>> ShotTreeView;
	TSharedPtr<SWidgetSwitcher> TabSwitcher;

	// Sequence overview
	TSharedPtr<SVerticalBox> OverviewListBox;
	TSharedPtr<SVerticalBox> EnvLibraryBox;
	TSharedPtr<SEditableTextBox> NewEnvPathTextBox;

	// Input widgets
	TSharedPtr<SEditableTextBox> BasePathTextBox;

	TSharedPtr<SSpinBox<int32>> AddSeqSpinBox;
	TSharedPtr<SSpinBox<int32>> AddShotSpinBox;
	TSharedPtr<SSpinBox<int32>> AddDurationSpinBox;

	TSharedPtr<SSpinBox<int32>> BatchSeqSpinBox;
	TSharedPtr<SSpinBox<int32>> BatchCountSpinBox;
	TSharedPtr<SSpinBox<int32>> BatchStartSpinBox;
	TSharedPtr<SSpinBox<int32>> BatchEndSpinBox;
	TSharedPtr<SSpinBox<int32>> BatchDurationSpinBox;

	TSharedPtr<SSpinBox<int32>> FrameStartSpinBox;
	TSharedPtr<SSpinBox<int32>> FPSSpinBox;

	// Output
	TSharedPtr<STextBlock> OutputTextBlock;
	FString OutputLog;

	// State
	int32 AddSeqNum = 1;
	int32 AddShotNum = 10;
	int32 AddFrameDuration = 150;
	int32 BatchSeqNum = 1;
	int32 BatchCount = 5;
	int32 BatchStart = 10;
	int32 BatchFrameDuration = 150;
	int32 FrameStart = 1001;
	int32 FPS = 24;

	FString BasePath = TEXT("/Game/Cinematics/Shots");

	bool bIsCreating = false;
	bool bOverwriteExisting = false;
};
