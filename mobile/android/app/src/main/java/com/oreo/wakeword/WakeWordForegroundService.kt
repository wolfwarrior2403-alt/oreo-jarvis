package com.oreo.wakeword

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat

/**
 * Foreground service scaffold for always-listening wake-word detection
 * (section 4.3) — keeps the app "alive" so Porcupine can keep detecting
 * "Oreo" with the screen off / phone locked, which a plain background JS
 * timer cannot do on Android.
 *
 * STATUS: stub. What's implemented: the service shell, a persistent
 * notification (required by Android for any foreground service), and
 * START_STICKY so the OS restarts it if killed. What's NOT implemented yet
 * (left as clearly marked TODOs, tracked in mobile/README.md):
 *   1. Actually running PorcupineManager natively in this service (right
 *      now wake-word detection runs in JS via
 *      src/services/wakeword.ts, which only works while the JS engine is
 *      alive — i.e. while the app is foregrounded). Running Porcupine
 *      natively here, then bridging detections back to JS via a
 *      NativeEventEmitter, is the real fix for locked-phone detection.
 *   2. The NativeModule bridge (OreoWakeWordServiceModule) that
 *      src/services/backgroundService.ts calls into — see that file in the
 *      same package for the stub bridge and what it still needs.
 *   3. Registering this service + its package in MainApplication.kt, which
 *      only exists once the native Android project has been generated
 *      (see mobile/android/README.md).
 */
class WakeWordForegroundService : Service() {

    companion object {
        const val CHANNEL_ID = "oreo_wakeword_channel"
        const val NOTIFICATION_ID = 1001
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        startForeground(NOTIFICATION_ID, buildNotification())
        // TODO: initialize native PorcupineManager here and start it.
        return START_STICKY
    }

    override fun onDestroy() {
        // TODO: stop/delete the native PorcupineManager instance here.
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun buildNotification(): Notification {
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Oreo is listening")
            .setContentText("Say \"Oreo\" to start a conversation.")
            .setOngoing(true)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Oreo wake word",
                NotificationManager.IMPORTANCE_LOW,
            )
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }
}
