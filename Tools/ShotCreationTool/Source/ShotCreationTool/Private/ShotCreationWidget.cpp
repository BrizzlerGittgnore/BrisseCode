#include "ShotCreationWidget.h"
#include "ShotCreationWidget.h"
#include "ShotCreationUtility.h"
#include "MasterSequenceUtility.h"
#include "Widgets/Input/SSpinBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/Views/STreeView.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Styling/AppStyle.h"
#include "Framework/MultiBox/MultiBoxBuilder.h"

#define LOCTEXT_NAMESPACE "SShotCreationWidget"

static const FString GConfigSection = TEXT("ShotCreationTool");

static const FLinearColor GSubSeqColors[] = {
	FLinearColor(0.3f, 0.7f, 0.4f),
	FLinearColor(0.9f, 0.8f, 0.2f),
	FLinearColor(0.7f, 0.3f, 0.7f),
	FLinearColor(0.3f, 0.6f, 0.9f),
	FLinearColor(0.9f, 0.4f, 0.3f),
	FLinearColor(0.5f, 0.8f, 0.8f),
	FLinearColor(0.8f, 0.5f, 0.3f),
};

// ============================================================
void SShotCreationWidget::Construct(const FArguments& InArgs)
{
	LoadSettings();

	ChildSlot
	[
		SNew(SVerticalBox)
		// Tab buttons
		+ SVerticalBox::Slot().AutoHeight().Padding(10, 10, 10, 0)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 4, 0)
			[ SNew(SButton).Text(LOCTEXT("Tab1", "Shot Creation")).OnClicked_Lambda([this]() { TabSwitcher->SetActiveWidgetIndex(0); return FReply::Handled(); }) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 4, 0)
			[ SNew(SButton).Text(LOCTEXT("Tab2", "Master Setup")).OnClicked_Lambda([this]() { TabSwitcher->SetActiveWidgetIndex(1); return FReply::Handled(); }) ]
			+ SHorizontalBox::Slot().AutoWidth()
			[ SNew(SButton).Text(LOCTEXT("Tab3", "Sequence Overview")).OnClicked_Lambda([this]() { RefreshOverview(); TabSwitcher->SetActiveWidgetIndex(2); return FReply::Handled(); }) ]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(10, 4, 10, 0)
		[ SNew(SSeparator) ]
		// Tab content
		+ SVerticalBox::Slot().FillHeight(1.0)
		[
			SAssignNew(TabSwitcher, SWidgetSwitcher)
			+ SWidgetSwitcher::Slot() [ BuildShotCreationTab() ]
			+ SWidgetSwitcher::Slot() [ BuildMasterSetupTab() ]
			+ SWidgetSwitcher::Slot() [ BuildSequenceOverviewTab() ]
		]
	];

	RebuildTree();
}

// ============================================================
// TAB 1: Shot Creation (existing functionality)
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildShotCreationTab()
{
	return SNew(SScrollBox)
		+ SScrollBox::Slot().Padding(10)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
			[ BuildPathSection() ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
			[ BuildSettingsSection() ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
			[ BuildAddShotSection() ]
			+ SVerticalBox::Slot().FillHeight(1.0).Padding(0, 0, 0, 6)
			[ BuildShotTreeSection() ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
			[ BuildOutputSection() ]
			+ SVerticalBox::Slot().AutoHeight().Padding(0, 5)
			[
				SNew(SButton).Text(LOCTEXT("Create", "Create All Pending Shots"))
				.HAlign(HAlign_Center).ContentPadding(FMargin(30, 8))
				.OnClicked(this, &SShotCreationWidget::OnCreateShotsClicked)
			]
		];
}

// ============================================================
// TAB 2: Master Setup
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildMasterSetupTab()
{
	return SNew(SScrollBox)
		+ SScrollBox::Slot().Padding(10)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 10)
			[ SNew(STextBlock).Text(LOCTEXT("MasterTitle", "Master Setup")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 16)) ]

			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
			[
				SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
					[ SNew(STextBlock).Text(LOCTEXT("MasterPaths", "Master Paths")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]
					+ SVerticalBox::Slot().AutoHeight().Padding(0, 2)
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
						[ SNew(STextBlock).Text(LOCTEXT("MLvl", "Master Level:")).MinDesiredWidth(100) ]
						+ SHorizontalBox::Slot().FillWidth(1.0)
						[ SNew(STextBlock).Text_Lambda([this]() { return FText::FromString(FMasterSequenceUtility::GetMasterLevelPath(BasePath)); }).ColorAndOpacity(FLinearColor::Gray) ]
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0, 2)
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
						[ SNew(STextBlock).Text(LOCTEXT("MSeq", "Master Sequence:")).MinDesiredWidth(100) ]
						+ SHorizontalBox::Slot().FillWidth(1.0)
						[ SNew(STextBlock).Text_Lambda([this]() { return FText::FromString(FMasterSequenceUtility::GetMasterSequencePath(BasePath)); }).ColorAndOpacity(FLinearColor::Gray) ]
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0, 2)
					[
						SNew(STextBlock)
						.Text_Lambda([this]() { return FMasterSequenceUtility::MasterExists(BasePath) ? LOCTEXT("MExists", "Status: Master exists") : LOCTEXT("MNone", "Status: Not created"); })
						.Font(FCoreStyle::GetDefaultFontStyle("Italic", 9))
						.ColorAndOpacity_Lambda([this]() { return FMasterSequenceUtility::MasterExists(BasePath) ? FSlateColor(FLinearColor(0.3f, 0.8f, 0.3f)) : FSlateColor(FLinearColor(0.8f, 0.4f, 0.2f)); })
					]
				]
			]

			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 10)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 8, 0)
				[ SNew(SButton).Text(LOCTEXT("CreateMaster", "Create Master Level + Sequence")).ContentPadding(FMargin(12, 6)).OnClicked(this, &SShotCreationWidget::OnCreateMasterClicked) ]
				+ SHorizontalBox::Slot().AutoWidth()
				[ SNew(SButton).Text(LOCTEXT("SyncMaster", "Sync Master")).ContentPadding(FMargin(12, 6)).OnClicked(this, &SShotCreationWidget::OnSyncMasterClicked) ]
			]

			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
			[
				SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
					[ SNew(STextBlock).Text(LOCTEXT("EnvLib", "Environment Library")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]
					+ SVerticalBox::Slot().AutoHeight()
					[ SAssignNew(EnvLibraryBox, SVerticalBox) ]
					+ SVerticalBox::Slot().AutoHeight().Padding(0, 6, 0, 0)
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().FillWidth(1.0)
						[ SAssignNew(NewEnvPathTextBox, SEditableTextBox).HintText(LOCTEXT("EnvHint", "/Game/Environments/ENV_Name")) ]
						+ SHorizontalBox::Slot().AutoWidth().Padding(4, 0, 0, 0)
						[ SNew(SButton).Text(LOCTEXT("AddEnv", "+ Add")).OnClicked(this, &SShotCreationWidget::OnAddEnvironmentClicked) ]
					]
				]
			]

			+ SVerticalBox::Slot().AutoHeight().Padding(0, 10, 0, 6)
			[
				SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 4)
					[ SNew(STextBlock).Text(LOCTEXT("SyncInfo", "Sync Behavior")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 11)) ]
					+ SVerticalBox::Slot().AutoHeight()
					[ SNew(STextBlock).Text(LOCTEXT("S1", "� Appends new sub-levels to Master Level (Blueprint streaming)")).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)).ColorAndOpacity(FLinearColor::Gray) ]
					+ SVerticalBox::Slot().AutoHeight()
					[ SNew(STextBlock).Text(LOCTEXT("S2", "� Appends new shot tracks to Master Sequence (at end)")).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)).ColorAndOpacity(FLinearColor::Gray) ]
					+ SVerticalBox::Slot().AutoHeight()
					[ SNew(STextBlock).Text(LOCTEXT("S3", "� Never removes or reorders existing content")).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)).ColorAndOpacity(FLinearColor::Gray) ]
					+ SVerticalBox::Slot().AutoHeight()
					[ SNew(STextBlock).Text(LOCTEXT("S4", "� Skips shots already synced (even if user deleted track)")).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)).ColorAndOpacity(FLinearColor::Gray) ]
				]
			]
		];
}

// ============================================================
// TAB 3: Sequence Overview
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildSequenceOverviewTab()
{
	return SNew(SScrollBox)
		+ SScrollBox::Slot().Padding(10)
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 10)
			[ SNew(STextBlock).Text(LOCTEXT("OverviewTitle", "Sequence Overview")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 16)) ]
			+ SVerticalBox::Slot().AutoHeight()
			[ SAssignNew(OverviewListBox, SVerticalBox) ]
		];
}

void SShotCreationWidget::RefreshOverview()
{
	if (!OverviewListBox.IsValid()) return;
	OverviewListBox->ClearChildren();

	// Refresh environment library box too
	if (EnvLibraryBox.IsValid())
	{
		EnvLibraryBox->ClearChildren();
		TArray<FEnvironmentInfo> Lib = FMasterSequenceUtility::GetEnvironmentLibrary();
		for (const auto& Env : Lib)
		{
			FString EnvName = Env.Name;
			EnvLibraryBox->AddSlot().AutoHeight().Padding(0, 2)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
				[ SNew(STextBlock).Text(FText::FromString(Env.Name)).MinDesiredWidth(120) ]
				+ SHorizontalBox::Slot().FillWidth(1.0).VAlign(VAlign_Center)
				[ SNew(STextBlock).Text(FText::FromString(Env.LevelPath)).ColorAndOpacity(FLinearColor::Gray).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)) ]
				+ SHorizontalBox::Slot().AutoWidth().Padding(4, 0, 0, 0)
				[ SNew(SButton).Text(LOCTEXT("RemEnv", "X")).ContentPadding(FMargin(4, 1)).OnClicked_Lambda([this, EnvName]() { return OnRemoveEnvironment(EnvName); }) ]
			];
		}
	}

	// Get all existing shots grouped by sequence
	TArray<FShotDefinition> AllShots = FShotCreationUtility::ScanExistingShots(BasePath);
	TMap<int32, TArray<FShotDefinition>> BySeq;
	for (const auto& S : AllShots)
	{
		BySeq.FindOrAdd(S.SequenceNumber).Add(S);
	}

	// Sort sequence numbers
	TArray<int32> SeqNums;
	BySeq.GetKeys(SeqNums);
	SeqNums.Sort();

	TArray<FEnvironmentInfo> EnvLib = FMasterSequenceUtility::GetEnvironmentLibrary();

	for (int32 SeqNum : SeqNums)
	{
		FString EnvName = FMasterSequenceUtility::GetSequenceEnvironment(SeqNum);
		FString EnvDisplay = EnvName.IsEmpty() ? TEXT("None") : EnvName;
		const TArray<FShotDefinition>& Shots = BySeq[SeqNum];

		OverviewListBox->AddSlot().AutoHeight().Padding(0, 4)
		[
			SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
			[
				SNew(SVerticalBox)
				// Sequence header with env info
				+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 4)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
					[ SNew(STextBlock).Text(FText::FromString(FString::Printf(TEXT("sq%02d"), SeqNum))).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(12, 0, 0, 0)
					[ SNew(STextBlock).Text(FText::FromString(FString::Printf(TEXT("(%d shots)"), Shots.Num()))).Font(FCoreStyle::GetDefaultFontStyle("Italic", 9)).ColorAndOpacity(FLinearColor::Gray) ]
					+ SHorizontalBox::Slot().FillWidth(1.0) [ SNew(SSpacer) ]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
					[ SNew(STextBlock).Text(FText::FromString(TEXT("ENV:"))).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)) ]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
					[
						SNew(STextBlock)
						.Text(FText::FromString(EnvDisplay))
						.Font(FCoreStyle::GetDefaultFontStyle("Bold", 10))
						.ColorAndOpacity(EnvName.IsEmpty() ? FSlateColor(FLinearColor(0.5f, 0.5f, 0.5f)) : FSlateColor(FLinearColor(0.4f, 0.8f, 0.4f)))
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
					[
						SNew(SButton).Text(LOCTEXT("Swap", "Swap"))
						.ContentPadding(FMargin(6, 2))
						.ToolTipText(LOCTEXT("SwapTip", "Swap environment for this sequence"))
						.OnClicked_Lambda([this, SeqNum]() { return OnSwapEnvironment(SeqNum); })
					]
				]
				// Shot list
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(STextBlock)
						.AutoWrapText(true)
						.Text_Lambda([Shots]()
						{
							FString Txt;
							for (const auto& S : Shots)
							{
								if (!Txt.IsEmpty()) Txt += TEXT(", ");
								Txt += FString::Printf(TEXT("sh%04d"), S.ShotNumber);
							}
							return FText::FromString(Txt);
						})
						.Font(FCoreStyle::GetDefaultFontStyle("Regular", 9))
						.ColorAndOpacity(FLinearColor::Gray)
				]
			]
		];
	}

	if (SeqNums.Num() == 0)
	{
		OverviewListBox->AddSlot().AutoHeight().Padding(0, 10)
		[
			SNew(STextBlock).Text(LOCTEXT("NoShots", "No shots found. Create shots first."))
			.ColorAndOpacity(FLinearColor::Gray)
		];
	}
}

FReply SShotCreationWidget::OnSwapEnvironment(int32 SeqNum)
{
	TArray<FEnvironmentInfo> Lib = FMasterSequenceUtility::GetEnvironmentLibrary();
	if (Lib.Num() == 0)
	{
		AppendLog(TEXT("No environments in library. Add one in Master Setup tab."));
		return FReply::Handled();
	}

	// Simple swap: cycle through available environments
	FString CurrentEnv = FMasterSequenceUtility::GetSequenceEnvironment(SeqNum);
	int32 CurrentIdx = -1;
	for (int32 i = 0; i < Lib.Num(); ++i)
	{
		if (Lib[i].Name == CurrentEnv) { CurrentIdx = i; break; }
	}
	int32 NextIdx = (CurrentIdx + 1) % Lib.Num();
	const FEnvironmentInfo& NewEnv = Lib[NextIdx];

	FString Error;
	FOnMasterLog LogDel;
	LogDel.BindLambda([this](const FString& Msg) { AppendLog(Msg); });

	bool bOK = FMasterSequenceUtility::SwapEnvironment(
		BasePath, SeqNum, CurrentEnv, NewEnv.LevelPath, static_cast<float>(FPS), LogDel, Error);

	if (!bOK)
	{
		AppendLog(FString::Printf(TEXT("Env swap failed: %s"), *Error));
	}
	else
	{
		AppendLog(FString::Printf(TEXT("sq%02d: %s -> %s"), SeqNum, *CurrentEnv, *NewEnv.Name));
	}

	RefreshOverview();
	return FReply::Handled();
}

FReply SShotCreationWidget::OnAddEnvironmentClicked()
{
	if (!NewEnvPathTextBox.IsValid()) return FReply::Handled();
	FString Path = NewEnvPathTextBox->GetText().ToString().TrimStartAndEnd();
	if (Path.IsEmpty()) return FReply::Handled();

	FString Name = FPaths::GetBaseFilename(Path);
	FMasterSequenceUtility::AddEnvironmentToLibrary(Name, Path);
	AppendLog(FString::Printf(TEXT("Added environment: %s (%s)"), *Name, *Path));
	NewEnvPathTextBox->SetText(FText::GetEmpty());
	RefreshOverview();
	return FReply::Handled();
}

FReply SShotCreationWidget::OnRemoveEnvironment(const FString& Name)
{
	FMasterSequenceUtility::RemoveEnvironmentFromLibrary(Name);
	AppendLog(FString::Printf(TEXT("Removed environment: %s"), *Name));
	RefreshOverview();
	return FReply::Handled();
}

// ============================================================
// Master actions
// ============================================================
FReply SShotCreationWidget::OnCreateMasterClicked()
{
	BasePath = BasePathTextBox.IsValid() ? BasePathTextBox->GetText().ToString() : BasePath;
	FString Error;
	FOnMasterLog LogDel;
	LogDel.BindLambda([this](const FString& Msg) { AppendLog(Msg); });

	bool bOK = FMasterSequenceUtility::CreateMaster(BasePath, TEXT(""), static_cast<float>(FPS), LogDel, Error);
	if (!bOK) AppendLog(FString::Printf(TEXT("ERROR: %s"), *Error));
	return FReply::Handled();
}

FReply SShotCreationWidget::OnSyncMasterClicked()
{
	BasePath = BasePathTextBox.IsValid() ? BasePathTextBox->GetText().ToString() : BasePath;
	FString Error;
	FOnMasterLog LogDel;
	LogDel.BindLambda([this](const FString& Msg) { AppendLog(Msg); });

	bool bOK = FMasterSequenceUtility::SyncMaster(BasePath, static_cast<float>(FPS), FrameStart, LogDel, Error);
	if (!bOK) AppendLog(FString::Printf(TEXT("ERROR: %s"), *Error));
	return FReply::Handled();
}

// ============================================================
// Path Section
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildPathSection()
{
	return SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 4)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[ SNew(STextBlock).Text(LOCTEXT("PathSettings", "Path Settings")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]
			+ SHorizontalBox::Slot().FillWidth(1.0) [ SNew(SSpacer) ]
			+ SHorizontalBox::Slot().AutoWidth()
			[ SNew(SButton).Text(LOCTEXT("Refresh", "Refresh")).OnClicked(this, &SShotCreationWidget::OnRefreshClicked) ]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 2)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
			[ SNew(STextBlock).Text(LOCTEXT("BasePath", "Base Path:")).MinDesiredWidth(80) ]
			+ SHorizontalBox::Slot().FillWidth(1.0)
			[
				SAssignNew(BasePathTextBox, SEditableTextBox).Text(FText::FromString(BasePath))
				.OnTextCommitted_Lambda([this](const FText& T, ETextCommit::Type) { BasePath = T.ToString(); SaveSettings(); })
			]
		]
	];
}

// ============================================================
// Settings Section
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildSettingsSection()
{
	return SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 4)
		[ SNew(STextBlock).Text(LOCTEXT("Settings", "Global Settings")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 2)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 8, 0)
			[ SNew(STextBlock).Text(LOCTEXT("FS", "Frame Start:")).MinDesiredWidth(80) ]
			+ SHorizontalBox::Slot().AutoWidth()
			[ SAssignNew(FrameStartSpinBox, SSpinBox<int32>).MinValue(0).MaxValue(99999).Value(FrameStart).Delta(1).SliderExponent(20.0f).MinDesiredWidth(80).OnValueChanged_Lambda([this](int32 V) { FrameStart = V; SaveSettings(); }) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(20, 0, 8, 0)
			[ SNew(STextBlock).Text(LOCTEXT("FPS", "Frame Rate:")).MinDesiredWidth(70) ]
			+ SHorizontalBox::Slot().AutoWidth()
			[ SAssignNew(FPSSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(120).Value(FPS).MinDesiredWidth(60).OnValueChanged_Lambda([this](int32 V) { FPS = V; SaveSettings(); }) ]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 6, 0, 0)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[ SNew(SCheckBox).IsChecked_Lambda([this]() { return bOverwriteExisting ? ECheckBoxState::Checked : ECheckBoxState::Unchecked; }).OnCheckStateChanged_Lambda([this](ECheckBoxState S) { bOverwriteExisting = (S == ECheckBoxState::Checked); }) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(4, 0, 0, 0)
			[ SNew(STextBlock).Text(LOCTEXT("Overwrite", "Overwrite existing shots")) ]
		]
	];
}

// ============================================================
// Add Shot Section
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildAddShotSection()
{
	return SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 6)
		[ SNew(STextBlock).Text(LOCTEXT("AddShots", "Add Shots")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]

		// Single shot
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 2)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0) [ SNew(STextBlock).Text(LOCTEXT("SQ", "SQ:")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 10, 0)
			[ SAssignNew(AddSeqSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(99).Value(AddSeqNum).SliderExponent(20.0f).MinDesiredWidth(50).OnValueChanged_Lambda([this](int32 V) { AddSeqNum = V; }) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0) [ SNew(STextBlock).Text(LOCTEXT("Shot", "Shot:")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 10, 0)
			[ SAssignNew(AddShotSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(9999).Value(AddShotNum).Delta(10).SliderExponent(20.0f).MinDesiredWidth(60).ToolTipText(LOCTEXT("ShotNumTip", "Shot number to add (increments by 10)")).OnValueChanged_Lambda([this](int32 V) { AddShotNum = V; }) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0) [ SNew(STextBlock).Text(LOCTEXT("Dur", "Duration:")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 10, 0)
			[ SAssignNew(AddDurationSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(99999).Value(AddFrameDuration).Delta(1).SliderExponent(20.0f).MinDesiredWidth(60).ToolTipText(LOCTEXT("DurTip", "Shot duration in frames")).OnValueChanged_Lambda([this](int32 V) { AddFrameDuration = V; }) ]
			+ SHorizontalBox::Slot().AutoWidth()
			[ SNew(SButton).Text(LOCTEXT("AddShot", "+ Add Shot")).OnClicked(this, &SShotCreationWidget::OnAddShotClicked) ]
		]

		// Batch
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 6, 0, 0)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0) [ SNew(STextBlock).Text(LOCTEXT("BSQ", "SQ:")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 10, 0)
			[ SAssignNew(BatchSeqSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(99).Value(BatchSeqNum).SliderExponent(20.0f).MinDesiredWidth(50).OnValueChanged_Lambda([this](int32 V) { BatchSeqNum = V; }) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0) [ SNew(STextBlock).Text(LOCTEXT("Cnt", "Count:")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 10, 0)
			[
				SAssignNew(BatchCountSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(999).Value(BatchCount).MinDesiredWidth(50).SliderExponent(20.0f)
				.ToolTipText(LOCTEXT("CountTip", "Number of shots to create in batch"))
				.OnValueChanged_Lambda([this](int32 V) { BatchCount = V; if (BatchEndSpinBox.IsValid()) BatchEndSpinBox->SetValue(BatchStart + (BatchCount - 1) * 10); })
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0) [ SNew(STextBlock).Text(LOCTEXT("BDur", "Duration:")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 10, 0)
			[ SAssignNew(BatchDurationSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(99999).Value(BatchFrameDuration).Delta(1).SliderExponent(20.0f).MinDesiredWidth(60).ToolTipText(LOCTEXT("BDurTip", "Duration per shot in frames")).OnValueChanged_Lambda([this](int32 V) { BatchFrameDuration = V; }) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0, 0, 4, 0) [ SNew(STextBlock).Text(LOCTEXT("Range", "Range:")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 2, 0)
			[
				SAssignNew(BatchStartSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(9999).Value(BatchStart).Delta(10).SliderExponent(20.0f).MinDesiredWidth(60)
				.ToolTipText(LOCTEXT("RangeStartTip", "First shot number in batch (increments by 10)"))
				.OnValueChanged_Lambda([this](int32 V) { BatchStart = V; if (BatchEndSpinBox.IsValid()) BatchEndSpinBox->SetValue(BatchStart + (BatchCount - 1) * 10); })
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(2, 0, 2, 0)
			[ SNew(STextBlock).Text(LOCTEXT("Dash", "-")) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(0, 0, 10, 0)
			[ SAssignNew(BatchEndSpinBox, SSpinBox<int32>).MinValue(1).MaxValue(9999).Value(BatchStart + (BatchCount - 1) * 10).MinDesiredWidth(60).IsEnabled(false) ]
			+ SHorizontalBox::Slot().AutoWidth()
			[ SNew(SButton).Text(LOCTEXT("BatchAdd", "+ Batch Add")).OnClicked(this, &SShotCreationWidget::OnBatchAddClicked) ]
		]
	];
}

// ============================================================
// Shot Tree
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildShotTreeSection()
{
	return SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 4)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[ SNew(STextBlock).Text(LOCTEXT("ShotStruct", "Shot Structure")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]
			+ SHorizontalBox::Slot().FillWidth(1.0) [ SNew(SSpacer) ]
			+ SHorizontalBox::Slot().AutoWidth().Padding(4, 0)
			[ SNew(SButton).Text(LOCTEXT("RemSel", "Remove Selected")).OnClicked(this, &SShotCreationWidget::OnRemoveSelectedClicked) ]
			+ SHorizontalBox::Slot().AutoWidth()
			[ SNew(SButton).Text(LOCTEXT("ClearP", "Clear Pending")).OnClicked(this, &SShotCreationWidget::OnClearPendingClicked) ]
		]
		+ SVerticalBox::Slot().FillHeight(1.0).MaxHeight(400)
		[
			SAssignNew(ShotTreeView, STreeView<TSharedPtr<FShotTreeItem>>)
			.TreeItemsSource(&TreeRoots)
			.OnGenerateRow(this, &SShotCreationWidget::OnGenerateTreeRow)
			.OnGetChildren(this, &SShotCreationWidget::OnGetTreeChildren)
			.OnContextMenuOpening(this, &SShotCreationWidget::OnContextMenuOpening)
			.SelectionMode(ESelectionMode::Multi)
		]
	];
}

// ============================================================
// Tree Row Generation
// ============================================================
TSharedRef<ITableRow> SShotCreationWidget::OnGenerateTreeRow(TSharedPtr<FShotTreeItem> Item, const TSharedRef<STableViewBase>& OwnerTable)
{
	// Ghost sequence: compact left-aligned button
	if (Item->bIsGhost && Item->bIsSequenceHeader)
	{
		FString BtnText = FString::Printf(TEXT("sq%02d  +seq"), Item->SequenceNumber);
		return SNew(STableRow<TSharedPtr<FShotTreeItem>>, OwnerTable)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(4, 2)
			[
				SNew(SButton)
				.Text(FText::FromString(BtnText))
				.ToolTipText(FText::FromString(FString::Printf(TEXT("Add sequence sq%02d with first shot sh0010"), Item->SequenceNumber)))
				.ContentPadding(FMargin(4, 2))
				.OnClicked_Lambda([this, SeqNum = Item->SequenceNumber]() { return OnAddGhostSequence(SeqNum); })
			]
		];
	}

	// Sequence header
	if (Item->bIsSequenceHeader)
	{
		int32 RealCount = 0;
		for (const auto& C : Item->Children) if (!C->bIsGhost) RealCount++;
		FString EnvName = FMasterSequenceUtility::GetSequenceEnvironment(Item->SequenceNumber);

		return SNew(STableRow<TSharedPtr<FShotTreeItem>>, OwnerTable)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(4, 4)
			[ SNew(STextBlock).Text(FText::FromString(Item->GetDisplayName())).Font(FCoreStyle::GetDefaultFontStyle("Bold", 11)) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8, 0)
			[ SNew(STextBlock).Text(FText::FromString(FString::Printf(TEXT("(%d shots)"), RealCount))).Font(FCoreStyle::GetDefaultFontStyle("Italic", 9)).ColorAndOpacity(FSlateColor(FLinearColor::Gray)) ]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8, 0)
			[
				SNew(STextBlock)
				.Text(FText::FromString(EnvName.IsEmpty() ? TEXT("") : FString::Printf(TEXT("[%s]"), *EnvName)))
				.Font(FCoreStyle::GetDefaultFontStyle("Italic", 9))
				.ColorAndOpacity(FSlateColor(FLinearColor(0.4f, 0.8f, 0.4f)))
			]
		];
	}

	// Ghost shot: compact left-aligned button
	if (Item->bIsGhost)
	{
		FString BtnText = FString::Printf(TEXT("sh%04d  +sh"), Item->ShotNumber);
		return SNew(STableRow<TSharedPtr<FShotTreeItem>>, OwnerTable)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(4, 2)
			[
				SNew(SButton)
				.Text(FText::FromString(BtnText))
				.ToolTipText(FText::FromString(FString::Printf(TEXT("Add shot sh%04d to sq%02d"), Item->ShotNumber, Item->SequenceNumber)))
				.ContentPadding(FMargin(4, 1))
				.OnClicked_Lambda([this, SeqNum = Item->SequenceNumber, ShotNum = Item->ShotNumber]() { return OnAddGhostShot(SeqNum, ShotNum); })
			]
		];
	}

	// Regular shot
	FLinearColor TextColor = Item->bExistsOnDisk ? FLinearColor(0.5f, 0.5f, 0.5f) : FLinearColor::White;
	FString StatusTag = Item->bExistsOnDisk ? TEXT("[exists]") : TEXT("[pending]");
	FLinearColor StatusColor = Item->bExistsOnDisk ? FLinearColor(0.4f, 0.6f, 0.4f) : FLinearColor(1.0f, 0.8f, 0.2f);

	return SNew(STableRow<TSharedPtr<FShotTreeItem>>, OwnerTable)
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(4, 2)
		[ SNew(STextBlock).Text(FText::FromString(FString::Printf(TEXT("sh%04d"), Item->ShotNumber))).ColorAndOpacity(FSlateColor(TextColor)) ]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8, 2)
		[ SNew(STextBlock).Text(FText::FromString(StatusTag)).Font(FCoreStyle::GetDefaultFontStyle("Italic", 9)).ColorAndOpacity(FSlateColor(StatusColor)) ]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8, 2)
		[ SNew(STextBlock).Text(FText::FromString(Item->FrameDuration > 0 ? FString::Printf(TEXT("%d frames"), Item->FrameDuration) : TEXT(""))).Font(FCoreStyle::GetDefaultFontStyle("Regular", 9)).ColorAndOpacity(FSlateColor(FLinearColor::Gray)) ]
	];
}

void SShotCreationWidget::OnGetTreeChildren(TSharedPtr<FShotTreeItem> Item, TArray<TSharedPtr<FShotTreeItem>>& OutChildren)
{
	if (Item.IsValid() && Item->bIsSequenceHeader)
		OutChildren = Item->Children;
}

// ============================================================
// Context Menu
// ============================================================
TSharedPtr<SWidget> SShotCreationWidget::OnContextMenuOpening()
{
	TArray<TSharedPtr<FShotTreeItem>> Selected = ShotTreeView->GetSelectedItems();
	if (Selected.Num() != 1 || Selected[0]->bIsSequenceHeader || Selected[0]->bIsGhost) return nullptr;

	TSharedPtr<FShotTreeItem> Sel = Selected[0];
	FMenuBuilder MenuBuilder(true, nullptr);
	MenuBuilder.AddMenuEntry(LOCTEXT("InsBef", "Insert Shot Before"), FText(), FSlateIcon(),
		FUIAction(FExecuteAction::CreateSP(this, &SShotCreationWidget::InsertShotBefore, Sel)));
	MenuBuilder.AddMenuEntry(LOCTEXT("InsAft", "Insert Shot After"), FText(), FSlateIcon(),
		FUIAction(FExecuteAction::CreateSP(this, &SShotCreationWidget::InsertShotAfter, Sel)));
	return MenuBuilder.MakeWidget();
}

int32 SShotCreationWidget::CalculateMidpoint(int32 A, int32 B) const
{
	return FMath::RoundToInt32(static_cast<float>(A + B) / 2.0f);
}

void SShotCreationWidget::InsertShotBefore(TSharedPtr<FShotTreeItem> Item)
{
	if (!Item.IsValid() || Item->bIsSequenceHeader || Item->bIsGhost) return;
	TSharedPtr<FShotTreeItem> SeqNode = FindOrCreateSequenceNode(Item->SequenceNumber);
	int32 PrevNum = 0;
	for (int32 i = 0; i < SeqNode->Children.Num(); ++i)
		if (SeqNode->Children[i] == Item) { if (i > 0 && !SeqNode->Children[i-1]->bIsGhost) PrevNum = SeqNode->Children[i-1]->ShotNumber; break; }
	int32 N = CalculateMidpoint(PrevNum, Item->ShotNumber);
	if (N == PrevNum || N == Item->ShotNumber) { AppendLog(TEXT("No room")); return; }
	if (ShotExistsInTree(Item->SequenceNumber, N)) { AppendLog(FString::Printf(TEXT("sh%04d exists"), N)); return; }
	AddPendingShot(Item->SequenceNumber, N, AddFrameDuration);
	AppendLog(FString::Printf(TEXT("Inserted sh%04d before sh%04d"), N, Item->ShotNumber));
}

void SShotCreationWidget::InsertShotAfter(TSharedPtr<FShotTreeItem> Item)
{
	if (!Item.IsValid() || Item->bIsSequenceHeader || Item->bIsGhost) return;
	TSharedPtr<FShotTreeItem> SeqNode = FindOrCreateSequenceNode(Item->SequenceNumber);
	int32 NextNum = Item->ShotNumber + 10;
	for (int32 i = 0; i < SeqNode->Children.Num(); ++i)
		if (SeqNode->Children[i] == Item) { if (i+1 < SeqNode->Children.Num() && !SeqNode->Children[i+1]->bIsGhost) NextNum = SeqNode->Children[i+1]->ShotNumber; break; }
	int32 N = CalculateMidpoint(Item->ShotNumber, NextNum);
	if (N == Item->ShotNumber || N == NextNum) { AppendLog(TEXT("No room")); return; }
	if (ShotExistsInTree(Item->SequenceNumber, N)) { AppendLog(FString::Printf(TEXT("sh%04d exists"), N)); return; }
	AddPendingShot(Item->SequenceNumber, N, AddFrameDuration);
	AppendLog(FString::Printf(TEXT("Inserted sh%04d after sh%04d"), N, Item->ShotNumber));
}

// ============================================================
// Output
// ============================================================
TSharedRef<SWidget> SShotCreationWidget::BuildOutputSection()
{
	return SNew(SBorder).BorderImage(FAppStyle::GetBrush("ToolPanel.GroupBorder")).Padding(8)
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(0, 0, 0, 4)
		[ SNew(STextBlock).Text(LOCTEXT("Output", "Output")).Font(FCoreStyle::GetDefaultFontStyle("Bold", 12)) ]
		+ SVerticalBox::Slot().MaxHeight(180)
		[
			SNew(SScrollBox)
			+ SScrollBox::Slot()
			[ SAssignNew(OutputTextBlock, STextBlock).Text(LOCTEXT("Ready", "Ready.")).Font(FCoreStyle::GetDefaultFontStyle("Mono", 9)).ColorAndOpacity(FLinearColor::Gray).AutoWrapText(true) ]
		]
	];
}

// ============================================================
// Actions
// ============================================================
FReply SShotCreationWidget::OnAddShotClicked()
{
	if (ShotExistsInTree(AddSeqNum, AddShotNum)) { AppendLog(FString::Printf(TEXT("sh%04d already in sq%02d"), AddShotNum, AddSeqNum)); return FReply::Handled(); }
	AddPendingShot(AddSeqNum, AddShotNum, AddFrameDuration);
	AppendLog(FString::Printf(TEXT("Added sq%02d_sh%04d (%d frames)"), AddSeqNum, AddShotNum, AddFrameDuration));
	AddShotNum += 10;
	if (AddShotSpinBox.IsValid()) AddShotSpinBox->SetValue(AddShotNum);
	return FReply::Handled();
}

FReply SShotCreationWidget::OnBatchAddClicked()
{
	int32 Added = 0, Skipped = 0;
	for (int32 i = 0; i < BatchCount; ++i)
	{
		const int32 ShotNum = BatchStart + i * 10;
		if (ShotExistsInTree(BatchSeqNum, ShotNum)) { Skipped++; continue; }
		AddPendingShot(BatchSeqNum, ShotNum, BatchFrameDuration);
		Added++;
	}
	AppendLog(FString::Printf(TEXT("Batch: added %d shots to sq%02d%s"), Added, BatchSeqNum,
		Skipped > 0 ? *FString::Printf(TEXT(" (%d skipped)"), Skipped) : TEXT("")));
	return FReply::Handled();
}

FReply SShotCreationWidget::OnRemoveSelectedClicked()
{
	TArray<TSharedPtr<FShotTreeItem>> Selected = ShotTreeView->GetSelectedItems();
	int32 Removed = 0;
	for (const auto& Item : Selected)
	{
		if (Item->bIsSequenceHeader || Item->bExistsOnDisk || Item->bIsGhost) continue;
		for (auto& Root : TreeRoots)
			if (Root->SequenceNumber == Item->SequenceNumber) { Root->Children.Remove(Item); Removed++; break; }
	}
	RebuildTree();
	AppendLog(FString::Printf(TEXT("Removed %d pending shot(s)"), Removed));
	return FReply::Handled();
}

FReply SShotCreationWidget::OnClearPendingClicked()
{
	for (auto& Root : TreeRoots)
		Root->Children.RemoveAll([](const TSharedPtr<FShotTreeItem>& C) { return C->bIsPendingCreation && !C->bIsGhost; });
	RebuildTree();
	AppendLog(TEXT("Cleared all pending shots"));
	return FReply::Handled();
}

FReply SShotCreationWidget::OnRefreshClicked()
{
	BasePath = BasePathTextBox->GetText().ToString();
	RebuildTree();
	AppendLog(FString::Printf(TEXT("Refreshed from: %s"), *BasePath));
	return FReply::Handled();
}

FReply SShotCreationWidget::OnAddGhostShot(int32 SeqNum, int32 ShotNum)
{
	if (ShotExistsInTree(SeqNum, ShotNum)) return FReply::Handled();
	AddPendingShot(SeqNum, ShotNum, AddFrameDuration);
	AppendLog(FString::Printf(TEXT("Added sh%04d to sq%02d"), ShotNum, SeqNum));
	return FReply::Handled();
}

FReply SShotCreationWidget::OnAddGhostSequence(int32 SeqNum)
{
	AddPendingShot(SeqNum, 10, AddFrameDuration);
	AppendLog(FString::Printf(TEXT("Created sq%02d with sh0010"), SeqNum));
	return FReply::Handled();
}

FReply SShotCreationWidget::OnCreateShotsClicked()
{
	if (bIsCreating) return FReply::Handled();

	TArray<TSharedPtr<FShotTreeItem>> Pending;
	for (const auto& Root : TreeRoots)
		for (const auto& C : Root->Children)
			if (C->bIsPendingCreation && !C->bIsGhost) Pending.Add(C);

	if (Pending.Num() == 0) { AppendLog(TEXT("No pending shots.")); return FReply::Handled(); }

	bIsCreating = true;
	OutputLog.Empty();
	BasePath = BasePathTextBox->GetText().ToString();
	SaveSettings();

	AppendLog(TEXT("========================================"));
	AppendLog(FString::Printf(TEXT("Creating %d shot(s)..."), Pending.Num()));
	AppendLog(TEXT("========================================"));

	FShotCreationParams Params;
	Params.BasePath = BasePath;
	Params.FrameStart = FrameStart;
	Params.FrameRate = static_cast<float>(FPS);
	Params.bOverwriteExisting = bOverwriteExisting;
	Params.bUseBlueprintStreaming = true;

	// Populate environment assignments per sequence
	TSet<int32> SeqNums;
	for (const auto& E : Pending) SeqNums.Add(E->SequenceNumber);
	for (int32 SN : SeqNums)
	{
		FString Env = FMasterSequenceUtility::GetSequenceEnvironment(SN);
		if (!Env.IsEmpty()) Params.SequenceEnvironments.Add(SN, Env);
	}

	for (const auto& E : Pending)
	{
		FShotDefinition D;
		D.SequenceNumber = E->SequenceNumber;
		D.ShotNumber = E->ShotNumber;
		D.FrameDuration = E->FrameDuration;
		Params.Shots.Add(D);
	}

	FOnShotCreationLog LogDelegate;
	LogDelegate.BindLambda([this](const FString& Msg) { AppendLog(Msg); });
	TArray<FShotCreationResult> Results = FShotCreationUtility::CreateShots(Params, LogDelegate);

	int32 OK = 0, Fail = 0, Skip = 0;
	for (const auto& R : Results)
	{
		if (R.bSkipped) Skip++;
		else if (R.bSuccess) OK++;
		else { Fail++; AppendLog(FString::Printf(TEXT("FAILED: %s - %s"), *R.ShotName, *R.Message)); }
	}
	AppendLog(FString::Printf(TEXT("Done! %d created, %d skipped, %d failed."), OK, Skip, Fail));

	// Mark successfully created shots as existing
	for (int32 i = 0; i < Pending.Num(); ++i)
	{
		if (i < Results.Num() && Results[i].bSuccess)
		{
			Pending[i]->bExistsOnDisk = true;
			Pending[i]->bIsPendingCreation = false;
		}
	}

	bIsCreating = false;
	RebuildTree();
	return FReply::Handled();
}

// ============================================================
// Helpers
// ============================================================
bool SShotCreationWidget::ShotExistsInTree(int32 SeqNum, int32 ShotNum) const
{
	for (const auto& R : TreeRoots)
		if (R->SequenceNumber == SeqNum)
			for (const auto& C : R->Children)
				if (C->ShotNumber == ShotNum && !C->bIsGhost) return true;
	return false;
}

TSharedPtr<FShotTreeItem> SShotCreationWidget::FindOrCreateSequenceNode(int32 SeqNum)
{
	for (auto& R : TreeRoots)
		if (R->SequenceNumber == SeqNum && !R->bIsGhost) return R;
	TSharedPtr<FShotTreeItem> N = MakeShared<FShotTreeItem>();
	N->bIsSequenceHeader = true;
	N->SequenceNumber = SeqNum;
	TreeRoots.Add(N);
	TreeRoots.Sort([](const TSharedPtr<FShotTreeItem>& A, const TSharedPtr<FShotTreeItem>& B)
	{
		if (A->bIsGhost != B->bIsGhost) return !A->bIsGhost;
		return A->SequenceNumber < B->SequenceNumber;
	});
	return N;
}

TSharedPtr<FShotTreeItem> SShotCreationWidget::FindShotInSequence(TSharedPtr<FShotTreeItem> SeqNode, int32 ShotNum) const
{
	if (!SeqNode.IsValid()) return nullptr;
	for (const auto& C : SeqNode->Children)
		if (C->ShotNumber == ShotNum) return C;
	return nullptr;
}

int32 SShotCreationWidget::GetNextShotNumber(int32 SeqNum) const
{
	int32 Highest = 0;
	for (const auto& R : TreeRoots)
		if (R->SequenceNumber == SeqNum)
			for (const auto& C : R->Children)
				if (!C->bIsGhost && C->ShotNumber > Highest) Highest = C->ShotNumber;
	int32 Next = Highest + 10;
	return ((Next + 9) / 10) * 10;
}

int32 SShotCreationWidget::GetNextSequenceNumber() const
{
	int32 Highest = 0;
	for (const auto& R : TreeRoots)
		if (!R->bIsGhost && R->SequenceNumber > Highest) Highest = R->SequenceNumber;
	return Highest + 1;
}

FLinearColor SShotCreationWidget::GetSubSequenceColor(int32 Index) const
{
	const int32 NumColors = UE_ARRAY_COUNT(GSubSeqColors);
	return GSubSeqColors[Index % NumColors];
}

void SShotCreationWidget::AddPendingShot(int32 SeqNum, int32 ShotNum, int32 Duration)
{
	TSharedPtr<FShotTreeItem> SeqNode = FindOrCreateSequenceNode(SeqNum);
	TSharedPtr<FShotTreeItem> S = MakeShared<FShotTreeItem>();
	S->SequenceNumber = SeqNum;
	S->ShotNumber = ShotNum;
	S->FrameDuration = Duration;
	S->bIsPendingCreation = true;
	SeqNode->Children.Add(S);
	RebuildTree();
}

void SShotCreationWidget::RebuildTree()
{
	// Collect pending (non-ghost) shots
	TArray<TSharedPtr<FShotTreeItem>> PendingShots;
	for (const auto& R : TreeRoots)
		for (const auto& C : R->Children)
			if (C->bIsPendingCreation && !C->bIsGhost) PendingShots.Add(C);

	TreeRoots.RemoveAll([](const TSharedPtr<FShotTreeItem>& R) { return R->bIsGhost; });
	for (auto& R : TreeRoots)
		R->Children.RemoveAll([](const TSharedPtr<FShotTreeItem>& C) { return C->bIsGhost; });
	for (auto& R : TreeRoots)
		R->Children.RemoveAll([](const TSharedPtr<FShotTreeItem>& C) { return C->bExistsOnDisk; });
	TreeRoots.RemoveAll([](const TSharedPtr<FShotTreeItem>& R) { return R->Children.Num() == 0; });

	// Scan disk
	TArray<FShotDefinition> Existing = FShotCreationUtility::ScanExistingShots(BasePath);
	for (const FShotDefinition& D : Existing)
	{
		TSharedPtr<FShotTreeItem> SeqNode = FindOrCreateSequenceNode(D.SequenceNumber);
		if (!FindShotInSequence(SeqNode, D.ShotNumber))
		{
			TSharedPtr<FShotTreeItem> S = MakeShared<FShotTreeItem>();
			S->SequenceNumber = D.SequenceNumber;
			S->ShotNumber = D.ShotNumber;
			S->FrameDuration = D.FrameDuration;
			S->bExistsOnDisk = true;
			SeqNode->Children.Add(S);
		}
	}

	// Re-add pending
	for (const auto& P : PendingShots)
	{
		TSharedPtr<FShotTreeItem> SeqNode = FindOrCreateSequenceNode(P->SequenceNumber);
		if (!FindShotInSequence(SeqNode, P->ShotNumber))
			SeqNode->Children.Add(P);
	}

	// Sort children and add ghost
	for (auto& R : TreeRoots)
	{
		if (R->bIsGhost) continue;
		R->Children.Sort([](const TSharedPtr<FShotTreeItem>& A, const TSharedPtr<FShotTreeItem>& B) { return A->ShotNumber < B->ShotNumber; });
		int32 NextShot = GetNextShotNumber(R->SequenceNumber);
		TSharedPtr<FShotTreeItem> Ghost = MakeShared<FShotTreeItem>();
		Ghost->bIsGhost = true;
		Ghost->SequenceNumber = R->SequenceNumber;
		Ghost->ShotNumber = NextShot;
		Ghost->FrameDuration = AddFrameDuration;
		R->Children.Add(Ghost);
	}

	TreeRoots.Sort([](const TSharedPtr<FShotTreeItem>& A, const TSharedPtr<FShotTreeItem>& B)
	{
		if (A->bIsGhost != B->bIsGhost) return !A->bIsGhost;
		return A->SequenceNumber < B->SequenceNumber;
	});

	// Ghost sequence
	GhostSequenceNode = MakeShared<FShotTreeItem>();
	GhostSequenceNode->bIsSequenceHeader = true;
	GhostSequenceNode->bIsGhost = true;
	GhostSequenceNode->SequenceNumber = GetNextSequenceNumber();
	TreeRoots.Add(GhostSequenceNode);

	if (ShotTreeView.IsValid())
	{
		for (const auto& R : TreeRoots)
			if (!R->bIsGhost) ShotTreeView->SetItemExpansion(R, true);
		ShotTreeView->RequestTreeRefresh();
	}
}

void SShotCreationWidget::SaveSettings()
{
	GConfig->SetString(*GConfigSection, TEXT("BasePath"), *BasePath, GEditorPerProjectIni);
	GConfig->SetInt(*GConfigSection, TEXT("FrameStart"), FrameStart, GEditorPerProjectIni);
	GConfig->SetInt(*GConfigSection, TEXT("FPS"), FPS, GEditorPerProjectIni);
	GConfig->Flush(false, GEditorPerProjectIni);
}

void SShotCreationWidget::LoadSettings()
{
	GConfig->GetString(*GConfigSection, TEXT("BasePath"), BasePath, GEditorPerProjectIni);
	GConfig->GetInt(*GConfigSection, TEXT("FrameStart"), FrameStart, GEditorPerProjectIni);
	GConfig->GetInt(*GConfigSection, TEXT("FPS"), FPS, GEditorPerProjectIni);
}

void SShotCreationWidget::AppendLog(const FString& Text)
{
	OutputLog += Text + TEXT("\n");
	if (OutputTextBlock.IsValid()) OutputTextBlock->SetText(FText::FromString(OutputLog));
}

#undef LOCTEXT_NAMESPACE
