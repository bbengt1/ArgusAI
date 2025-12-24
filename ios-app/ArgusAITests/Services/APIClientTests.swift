//
//  APIClientTests.swift
//  ArgusAITests
//
//  Unit tests for APIClient and response parsing.
//

import XCTest
@testable import ArgusAI

final class APIClientTests: XCTestCase {

    // MARK: - Event Parsing Tests

    func testEventSummaryDecoding() throws {
        let json = """
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "camera_id": "550e8400-e29b-41d4-a716-446655440001",
            "camera_name": "Front Door",
            "timestamp": "2025-12-24T10:30:00Z",
            "description": "Person walking toward front door",
            "smart_detection_type": "person",
            "confidence": 95,
            "has_thumbnail": true
        }
        """

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let event = try decoder.decode(EventSummary.self, from: json.data(using: .utf8)!)

        XCTAssertEqual(event.id.uuidString.lowercased(), "550e8400-e29b-41d4-a716-446655440000")
        XCTAssertEqual(event.cameraName, "Front Door")
        XCTAssertEqual(event.description, "Person walking toward front door")
        XCTAssertEqual(event.smartDetectionType, .person)
        XCTAssertEqual(event.confidence, 95)
        XCTAssertEqual(event.hasThumbnail, true)
    }

    func testEventListResponseDecoding() throws {
        let json = """
        {
            "events": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "camera_id": "550e8400-e29b-41d4-a716-446655440001",
                    "camera_name": "Front Door",
                    "timestamp": "2025-12-24T10:30:00Z",
                    "description": "Person detected",
                    "smart_detection_type": "person",
                    "confidence": 95,
                    "has_thumbnail": true
                }
            ],
            "total_count": 100,
            "has_more": true,
            "next_offset": 20
        }
        """

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let response = try decoder.decode(EventListResponse.self, from: json.data(using: .utf8)!)

        XCTAssertEqual(response.events.count, 1)
        XCTAssertEqual(response.totalCount, 100)
        XCTAssertEqual(response.hasMore, true)
        XCTAssertEqual(response.nextOffset, 20)
    }

    func testEventDetailDecoding() throws {
        let json = """
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "camera_id": "550e8400-e29b-41d4-a716-446655440001",
            "camera_name": "Front Door",
            "timestamp": "2025-12-24T10:30:00Z",
            "description": "Person walking toward front door",
            "smart_detection_type": "person",
            "confidence": 95,
            "objects_detected": ["person", "backpack"],
            "is_doorbell_ring": false,
            "source_type": "protect",
            "provider_used": "openai",
            "analysis_mode": "multi_frame",
            "thumbnail_url": "/api/v1/mobile/events/550e8400-e29b-41d4-a716-446655440000/thumbnail",
            "created_at": "2025-12-24T10:30:05Z"
        }
        """

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let event = try decoder.decode(EventDetail.self, from: json.data(using: .utf8)!)

        XCTAssertEqual(event.cameraName, "Front Door")
        XCTAssertEqual(event.objectsDetected, ["person", "backpack"])
        XCTAssertEqual(event.isDoorbellRing, false)
        XCTAssertEqual(event.sourceType, "protect")
        XCTAssertEqual(event.providerUsed, "openai")
        XCTAssertEqual(event.analysisMode, .multiFrame)
    }

    // MARK: - Camera Parsing Tests

    func testCameraDecoding() throws {
        let json = """
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Front Door Camera",
            "is_enabled": true,
            "is_online": true,
            "source_type": "protect",
            "last_event_at": "2025-12-24T10:30:00Z"
        }
        """

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let camera = try decoder.decode(Camera.self, from: json.data(using: .utf8)!)

        XCTAssertEqual(camera.name, "Front Door Camera")
        XCTAssertEqual(camera.isEnabled, true)
        XCTAssertEqual(camera.isOnline, true)
        XCTAssertEqual(camera.sourceType, "protect")
    }

    func testCameraListResponseDecoding() throws {
        let json = """
        {
            "cameras": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "name": "Front Door",
                    "is_enabled": true,
                    "is_online": true,
                    "source_type": "protect"
                },
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "Backyard",
                    "is_enabled": true,
                    "is_online": false,
                    "source_type": "rtsp"
                }
            ]
        }
        """

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let response = try decoder.decode(CameraListResponse.self, from: json.data(using: .utf8)!)

        XCTAssertEqual(response.cameras.count, 2)
        XCTAssertEqual(response.cameras[0].name, "Front Door")
        XCTAssertEqual(response.cameras[1].isOnline, false)
    }

    // MARK: - Auth Token Parsing Tests

    func testTokenResponseDecoding() throws {
        let json = """
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        """

        let response = try JSONDecoder().decode(TokenResponse.self, from: json.data(using: .utf8)!)

        XCTAssertFalse(response.accessToken.isEmpty)
        XCTAssertFalse(response.refreshToken.isEmpty)
        XCTAssertEqual(response.tokenType, "Bearer")
        XCTAssertEqual(response.expiresIn, 3600)
    }

    func testPairResponseDecoding() throws {
        let json = """
        {
            "pairing_code": "847291",
            "expires_at": "2025-12-24T12:35:00Z"
        }
        """

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let response = try decoder.decode(PairResponse.self, from: json.data(using: .utf8)!)

        XCTAssertEqual(response.pairingCode, "847291")
        XCTAssertNotNil(response.expiresAt)
    }

    // MARK: - Error Response Tests

    func testErrorResponseDecoding() throws {
        let json = """
        {
            "detail": "Invalid or expired pairing code"
        }
        """

        let response = try JSONDecoder().decode(ErrorResponse.self, from: json.data(using: .utf8)!)

        XCTAssertEqual(response.detail, "Invalid or expired pairing code")
    }

    // MARK: - API Error Tests

    func testAPIErrorDescriptions() {
        XCTAssertEqual(APIError.notAuthenticated.errorDescription, "Not authenticated. Please pair your device.")
        XCTAssertEqual(APIError.sessionExpired.errorDescription, "Session expired. Please pair again.")
        XCTAssertEqual(APIError.notFound.errorDescription, "Resource not found")
        XCTAssertEqual(APIError.rateLimited.errorDescription, "Too many requests. Please wait and try again.")
        XCTAssertEqual(APIError.serverError(500).errorDescription, "Server error (500). Please try again later.")
    }
}
