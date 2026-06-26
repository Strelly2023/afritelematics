// Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit.
package novatech.contracts

object VersionVector {
    const val platform = "2.0.0"
    const val contract = "2.0.0"
    const val schema = "1.0.0"
    const val api = "1.0.0"
    const val replay = "1.0.0"
    const val evidence = "1.0.0"
    const val signature = "1.0.0"
}

data class GovernedRequest<T>(
    val requestId: String,
    val operation: String,
    val tenantId: String,
    val actorId: String,
    val idempotencyKey: String,
    val payload: T,
    val contractVersion: String = VersionVector.contract,
    val schemaVersion: String = VersionVector.schema,
)
