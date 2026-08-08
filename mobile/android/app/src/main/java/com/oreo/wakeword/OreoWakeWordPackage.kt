package com.oreo.wakeword

import com.facebook.react.ReactPackage
import com.facebook.react.bridge.NativeModule
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.uimanager.ViewManager

/**
 * Registers OreoWakeWordServiceModule with React Native.
 * TODO: add `.addPackage(OreoWakeWordPackage())` in MainApplication.kt's
 * getPackages() once the native project exists (see ../../../../../README.md).
 */
class OreoWakeWordPackage : ReactPackage {
    override fun createNativeModules(reactContext: ReactApplicationContext): List<NativeModule> {
        return listOf(OreoWakeWordServiceModule(reactContext))
    }

    override fun createViewManagers(reactContext: ReactApplicationContext): List<ViewManager<*, *>> {
        return emptyList()
    }
}
