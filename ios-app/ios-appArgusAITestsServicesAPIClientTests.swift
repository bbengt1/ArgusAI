//
//  APIClientTests.swift
//  ArgusAITests
//
//  Created on 2025-12-26.
//

import Testing
import Foundation
@testable import ArgusAI

@Suite("API Client Tests")
struct APIClientTests {
    
    @Test("EventSummary decodes from JSON")
    func testEventSummaryDecoding() throws {
        let json = """
        {
            "id": "evt_123",
            "camera_id": "cam_456",
            "timestamp": "2025-12-26T10:30:00Z",
            "ai_description": "Person detected at front door",
            "thumbnail_path": "/thumbnails/evt_123.jpg",
            "detection_type": "person"
        }
        """
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        let data = json.data(using: .utf8)!
        let event = try decoder.decode(EventSummary.self, from: data)
        
        #expect(event.id == "evt_123")
        #expect(event.cameraId == "cam_456")
        #expect(event.aiDescription == "Person detected at front door")
        #expect(event.detectionType == .person)
    }
    
    @Test("EventDetail decodes with optional fields")
    func testEventDetailDecoding() throws {
        let json = """
        {
            "id": "evt_123",
            "camera_id": "cam_456",
            "timestamp": "2025-12-26T10:30:00Z",
            "ai_description": "Person detected",
            "thumbnail_path": "/thumbnails/evt_123.jpg",
            "video_path": "/videos/evt_123.mp4",
            "detection_type": "person",
            "confidence": 0.95,
            "metadata": {
                "duration": "5s",
                "frame_count": "150"
            }
        }
        """
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        let data = json.data(using: .utf8)!
        let event = try decoder.decode(EventDetail.self, from: data)
        
        #expect(event.confidence == 0.95)
        #expect(event.metadata?["duration"] == "5s")
    }
    
    @Test("Camera decodes with display name")
    func testCameraDecoding() throws {
        let json = """
        {
            "id": "cam_123",
            "name": "Front Door",
            "location": "Entry",
            "is_online": true,
            "last_seen": "2025-12-26T10:30:00Z"
        }
        """
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        let data = json.data(using: .utf8)!
        let camera = try decoder.decode(Camera.self, from: data)
        
        #expect(camera.name == "Front Door")
        #expect(camera.displayName == "Front Door (Entry)")
    }
    
    @Test("Camera display name without location")
    func testCameraDisplayNameWithoutLocation() throws {
        let json = """
        {
            "id": "cam_123",
            "name": "Front Door",
            "location": null,
            "is_online": true,
            "last_seen": null
        }
        """
        
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        
        let data = json.data(using: .utf8)!
        let camera = try decoder.decode(Camera.self, from: data)
        
        #expect(camera.displayName == "Front Door")
    }
    
    @Test("AuthToken calculates expiration date")
    func testAuthTokenExpiration() {
        let token = AuthToken(
            accessToken: "test_token",
            refreshToken: "test_refresh",
            expiresIn: 3600,
            tokenType: "Bearer"
        )
        
        let expectedExpiration = Date().addingTimeInterval(3600)
        let timeDifference = abs(token.expirationDate.timeIntervalSince(expectedExpiration))
        
        #expect(timeDifference < 1.0) // Within 1 second
    }
}
