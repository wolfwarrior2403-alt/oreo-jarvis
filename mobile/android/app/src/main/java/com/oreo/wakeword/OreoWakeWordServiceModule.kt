package com.oreo.wakeword

import android.content.Intent
import android.os.Build
import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod

/**
 * NativeModule bridge for src/services/backgroundService.ts
 * (`NativeModules.OreoWakeWordService`). Starts/stops the foreground
 * service from JS.
 *
 * TODO: this module must be registered via a ReactPackage and added in
 * MainApplication.kt's getPackages() — that file only exists once the
 * native Android project is generated (see mobile/android/README.md).
 */
class OreoWakeWordServiceModule(reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    override fun getName(): String = "OreoWakeWordService"

    @ReactMethod
    fun start(promise: Promise) {
        try {
            val intent = Intent(reactApplicationContext, WakeWordForegroundService::class.java)
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                reactApplicationContext.startForegroundService(intent)
            } else {
                reactApplicationContext.startService(intent)
            }
            promise.resolve(null)
        } catch (e: Exception) {
            promise.reject("OREO_WAKEWORD_START_FAILED", e)
        }
    }

    @ReactMethod
    fun stop(promise: Promise) {
        try {
            val intent = Intent(reactApplicationContext, WakeWordForegroundService::class.java)
            reactApplicationContext.stopService(intent)
            promise.resolve(null)
        } catch (e: Exception) {
            promise.reject("OREO_WAKEWORD_STOP_FAILED", e)
        }
    }
}
