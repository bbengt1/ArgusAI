//
//  APIClient.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation
import UIKit

/// HTTP client with automatic token refresh and retry logic
final class APIClient {
    private let authService: AuthService
    private let discoveryService: DiscoveryService
    private let session: URLSession
    private let decoder: JSONDecoder
    
    init(authService: AuthService, discoveryService: DiscoveryService, session: URLSession = .shared) {
        self.authService = authService
        self.discoveryService = discoveryService
        self.session = session
        
        self.decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
    }
    
    // MARK: - Events
    
    func fetchEvents(page: Int = 1, pageSize: Int = 20) async throws -> EventsResponse {
        let url = discoveryService.baseURL
            .appendingPathComponent("/api/v1/mobile/events")
            .appending(queryItems: [
                URLQueryItem(name: "page", value: String(page)),
                URLQueryItem(name: "page_size", value: String(pageSize))
            ])
        
        let request = try await authorizedRequest(for: url)
        let data = try await performRequest(request)
        return try decoder.decode(EventsResponse.self, from: data)
    }
    
    func fetchEventDetail(id: String) async throws -> EventDetail {
        let url = discoveryService.baseURL
            .appendingPathComponent("/api/v1/mobile/events/\(id)")
        
        let request = try await authorizedRequest(for: url)
        let data = try await performRequest(request)
        return try decoder.decode(EventDetail.self, from: data)
    }
    
    func fetchEventThumbnail(id: String) async throws -> Data {
        let url = discoveryService.baseURL
            .appendingPathComponent("/api/v1/mobile/events/\(id)/thumbnail")
        
        let request = try await authorizedRequest(for: url)
        return try await performRequest(request)
    }
    
    // MARK: - Cameras
    
    func fetchCameras() async throws -> [Camera] {
        let url = discoveryService.baseURL
            .appendingPathComponent("/api/v1/mobile/cameras")
        
        let request = try await authorizedRequest(for: url)
        let data = try await performRequest(request)
        let response = try decoder.decode(CamerasResponse.self, from: data)
        return response.cameras
    }
    
    // MARK: - Push Notifications
    
    func registerPushToken(_ token: String) async throws {
        let url = discoveryService.baseURL
            .appendingPathComponent("/api/v1/mobile/push/register")
        
        var request = try await authorizedRequest(for: url, method: "POST")
        
        let body: [String: Any] = ["push_token": token, "platform": "ios"]
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        _ = try await performRequest(request)
    }
    
    // MARK: - Request Handling
    
    private func authorizedRequest(for url: URL, method: String = "GET") async throws -> URLRequest {
        guard let token = authService.currentToken else {
            throw APIError.unauthorized
        }
        
        // Check if token needs refresh (refresh 5 minutes before expiry)
        if token.expiresIn < 300 {
            try await authService.refreshAccessToken()
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        
        if let currentToken = authService.currentToken {
            request.setValue("Bearer \(currentToken.accessToken)", forHTTPHeaderField: "Authorization")
        }
        
        return request
    }
    
    private func performRequest(_ request: URLRequest, retryCount: Int = 0) async throws -> Data {
        do {
            let (data, response) = try await session.data(for: request)
            
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.invalidResponse
            }
            
            switch httpResponse.statusCode {
            case 200...299:
                return data
                
            case 401:
                // Unauthorized - try to refresh token and retry once
                if retryCount == 0 {
                    try await authService.refreshAccessToken()
                    
                    // Recreate request with new token
                    var newRequest = request
                    if let token = authService.currentToken {
                        newRequest.setValue("Bearer \(token.accessToken)", forHTTPHeaderField: "Authorization")
                    }
                    
                    return try await performRequest(newRequest, retryCount: retryCount + 1)
                }
                throw APIError.unauthorized
                
            case 404:
                throw APIError.notFound
                
            case 500...599:
                throw APIError.serverError(httpResponse.statusCode)
                
            default:
                throw APIError.unknown(httpResponse.statusCode)
            }
            
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }
}

enum APIError: LocalizedError {
    case unauthorized
    case notFound
    case invalidResponse
    case serverError(Int)
    case networkError(Error)
    case unknown(Int)
    
    var errorDescription: String? {
        switch self {
        case .unauthorized:
            return "You are not authorized. Please sign in again."
        case .notFound:
            return "The requested resource was not found."
        case .invalidResponse:
            return "Invalid response from server."
        case .serverError(let code):
            return "Server error: \(code)"
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .unknown(let code):
            return "Unknown error: \(code)"
        }
    }
}
