package com.novatech.novaid.personal

import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.google.android.play.core.integrity.IntegrityManagerFactory
import com.google.android.play.core.integrity.IntegrityTokenRequest

class NovaIDIntegrityModule(context: ReactApplicationContext) :
  ReactContextBaseJavaModule(context) {
  override fun getName() = "NovaIDIntegrity"

  @ReactMethod
  fun requestToken(nonce: String, cloudProjectNumber: String?, promise: Promise) {
    if (nonce.length < 16) {
      promise.reject("INVALID_NONCE", "Integrity nonce is invalid")
      return
    }
    val builder = IntegrityTokenRequest.builder().setNonce(nonce)
    cloudProjectNumber?.toLongOrNull()?.let(builder::setCloudProjectNumber)
    IntegrityManagerFactory.create(reactApplicationContext)
      .requestIntegrityToken(builder.build())
      .addOnSuccessListener { response -> promise.resolve(response.token()) }
      .addOnFailureListener { error ->
        promise.reject("PLAY_INTEGRITY_FAILED", error.message, error)
      }
  }
}
