#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

class FShotCreationToolModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;

private:
	void RegisterMenuExtensions();
	void UnregisterMenuExtensions();
	void OpenShotCreationTool();
};
