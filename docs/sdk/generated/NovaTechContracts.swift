// Generated from afritech/platform_contracts/platform.yaml. Do not hand-edit.
import Foundation

public enum NovaTechVersion {
    public static let platform = "2.0.0"
    public static let contract = "2.0.0"
    public static let schema = "1.0.0"
    public static let api = "1.0.0"
    public static let replay = "1.0.0"
    public static let evidence = "1.0.0"
    public static let signature = "1.0.0"
}

public struct GovernedRequest<Payload: Codable>: Codable {
    public let requestId: String
    public let operation: String
    public let tenantId: String
    public let actorId: String
    public let idempotencyKey: String
    public let contractVersion: String
    public let schemaVersion: String
    public let payload: Payload
}
