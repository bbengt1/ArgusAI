//
//  Event.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation

/// Summary of a security event for list display
struct EventSummary: Codable, Identifiable, Hashable {
    let id: String
    let cameraId: String
    let timestamp: Date
    let aiDescription: String
    let thumbnailPath: String?
    let detectionType: DetectionType
    
    enum CodingKeys: String, CodingKey {
        case id
        case cameraId = "camera_id"
        case timestamp
        case aiDescription = "ai_description"
        case thumbnailPath = "thumbnail_path"
        case detectionType = "detection_type"
    }
}

/// Detailed event information
struct EventDetail: Codable, Identifiable {
    let id: String
    let cameraId: String
    let timestamp: Date
    let aiDescription: String
    let thumbnailPath: String?
    let videoPath: String?
    let detectionType: DetectionType
    let confidence: Double?
    let metadata: [String: String]?
    
    enum CodingKeys: String, CodingKey {
        case id
        case cameraId = "camera_id"
        case timestamp
        case aiDescription = "ai_description"
        case thumbnailPath = "thumbnail_path"
        case videoPath = "video_path"
        case detectionType = "detection_type"
        case confidence
        case metadata
    }
}

/// Type of detection
enum DetectionType: String, Codable {
    case motion
    case person
    case vehicle
    case animal
    case package
    case unknown
    
    var displayName: String {
        switch self {
        case .motion: return "Motion"
        case .person: return "Person"
        case .vehicle: return "Vehicle"
        case .animal: return "Animal"
        case .package: return "Package"
        case .unknown: return "Unknown"
        }
    }
    
    var iconName: String {
        switch self {
        case .motion: return "waveform.path.ecg"
        case .person: return "person.fill"
        case .vehicle: return "car.fill"
        case .animal: return "pawprint.fill"
        case .package: return "shippingbox.fill"
        case .unknown: return "questionmark.circle.fill"
        }
    }
}

/// Response from events list endpoint
struct EventsResponse: Codable {
    let events: [EventSummary]
    let total: Int
    let page: Int
    let pageSize: Int
    
    enum CodingKeys: String, CodingKey {
        case events
        case total
        case page
        case pageSize = "page_size"
    }
}
