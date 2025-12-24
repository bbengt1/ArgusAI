//
//  Camera.swift
//  ArgusAI
//
//  Camera model matching the mobile API schema.
//

import Foundation

// MARK: - Camera Summary
struct Camera: Codable, Identifiable, Equatable {
    let id: UUID
    let name: String
    let isEnabled: Bool
    let isOnline: Bool
    let sourceType: String
    let lastEventAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case isEnabled = "is_enabled"
        case isOnline = "is_online"
        case sourceType = "source_type"
        case lastEventAt = "last_event_at"
    }
}

// MARK: - Camera List Response
struct CameraListResponse: Codable {
    let cameras: [Camera]
}
