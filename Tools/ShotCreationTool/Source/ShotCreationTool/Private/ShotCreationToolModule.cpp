#include "ShotCreationToolModule.h"
#include "ShotCreationWidget.h"
#include "ToolMenus.h"
#include "LevelEditor.h"
#include "Widgets/Docking/SDockTab.h"

#define LOCTEXT_NAMESPACE "FShotCreationToolModule"

void FShotCreationToolModule::StartupModule()
{
	RegisterMenuExtensions();
}

void FShotCreationToolModule::ShutdownModule()
{
	UnregisterMenuExtensions();
}

void FShotCreationToolModule::RegisterMenuExtensions()
{
	FToolMenuOwnerScoped OwnerScoped(this);

	UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
	if (Menu)
	{
		FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
		Section.AddMenuEntry(
			"ShotCreationTool",
			LOCTEXT("ShotCreationToolLabel", "Shot Creation Tool"),
			LOCTEXT("ShotCreationToolTooltip", "Batch create cinematic shots with levels, sub-levels and sequences"),
			FSlateIcon(),
			FUIAction(FExecuteAction::CreateRaw(this, &FShotCreationToolModule::OpenShotCreationTool))
		);
	}
}

void FShotCreationToolModule::UnregisterMenuExtensions()
{
	UToolMenus::Get()->UnregisterOwner(this);
}

void FShotCreationToolModule::OpenShotCreationTool()
{
	TSharedRef<SWindow> Window = SNew(SWindow)
		.Title(LOCTEXT("WindowTitle", "Shot Creation Tool"))
		.ClientSize(FVector2D(700, 850))
		.SupportsMinimize(true)
		.SupportsMaximize(false)
		.SizingRule(ESizingRule::UserSized);

	TSharedPtr<SShotCreationWidget> Widget;
	Window->SetContent(SAssignNew(Widget, SShotCreationWidget));

	FSlateApplication::Get().AddWindow(Window);
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FShotCreationToolModule, ShotCreationTool)
