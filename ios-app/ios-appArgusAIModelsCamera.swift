//
//  Camera.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation

/// Camera model
struct Camera: Codable, Identifiable, Hashable {
    let id: String
    let name: String
    let location: String?
    let isOnline: Bool
    let lastSeen: Date?
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case location
        case isOnline = "is_online"
        case lastSeen = "last_seen"
    }
    
    var displayName: String {
        if let location = location, !location.isEmpty {
            return "\(name) (\(location))"
        }
        return name
    }
}

/// Response from cameras list endpoint
struct CamerasResponse: Codable {
    let cameras: [Camera]
}
