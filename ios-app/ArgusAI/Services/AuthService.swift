//
//  AuthService.swift
//  ArgusAI
//
//  Authentication and pairing service.
//

import Foundation
import UIKit

@Observable
final class AuthService {
    private let keychain = KeychainService.shared
    private let session: URLSession

    var isAuthenticated: Bool {
        keychain.accessToken != nil
    }

    var deviceName: String? {
        keychain.deviceName
    }

    var deviceId: String {
        if let existing = keychain.deviceId {
            return existing
        }
        let newId = UUID().uuidString
        keychain.deviceId = newId
        return newId
    }

    init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)
    }

    // MARK: - Pairing Flow

    /// Generate a pairing code from the backend
    func generatePairingCode() async throws -> PairResponse {
        let request = PairRequest(
            deviceId: deviceId,
            deviceName: UIDevice.current.name,
            deviceModel: UIDevice.current.model
        )

        let baseURL = DiscoveryService.shared.currentBaseURL
        guard let url = URL(string: "\(baseURL)/api/v1/mobile/auth/pair") else {
            throw AuthError.invalidURL
        }

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode == 201 || httpResponse.statusCode == 200 {
            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .iso8601
            return try decoder.decode(PairResponse.self, from: data)
        } else if httpResponse.statusCode == 429 {
            throw AuthError.rateLimited
        } else {
            let error = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw AuthError.serverError(error?.detail ?? "Unknown error")
        }
    }

    /// Verify a pairing code and receive tokens
    func verifyPairingCode(_ code: String) async throws {
        let request = VerifyRequest(pairingCode: code, deviceId: deviceId)

        let baseURL = DiscoveryService.shared.currentBaseURL
        guard let url = URL(string: "\(baseURL)/api/v1/mobile/auth/verify") else {
            throw AuthError.invalidURL
        }

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode == 200 {
            let decoder = JSONDecoder()
            let tokens = try decoder.decode(TokenResponse.self, from: data)

            // Store tokens in Keychain
            keychain.storeTokens(
                accessToken: tokens.accessToken,
                refreshToken: tokens.refreshToken,
                expiresIn: tokens.expiresIn
            )
            keychain.deviceName = UIDevice.current.name

        } else if httpResponse.statusCode == 401 || httpResponse.statusCode == 400 {
            let error = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw AuthError.invalidCode(error?.detail ?? "Invalid or expired pairing code")
        } else if httpResponse.statusCode == 429 {
            throw AuthError.rateLimited
        } else {
            let error = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw AuthError.serverError(error?.detail ?? "Unknown error")
        }
    }

    // MARK: - Token Refresh

    func refreshTokenIfNeeded() async throws {
        guard keychain.needsRefresh else { return }
        guard let refreshToken = keychain.refreshToken else {
            throw AuthError.notAuthenticated
        }

        try await refreshToken(with: refreshToken)
    }

    func refreshToken(with token: String) async throws {
        let request = RefreshRequest(refreshToken: token)

        let baseURL = DiscoveryService.shared.currentBaseURL
        guard let url = URL(string: "\(baseURL)/api/v1/mobile/auth/refresh") else {
            throw AuthError.invalidURL
        }

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await session.data(for: urlRequest)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode == 200 {
            let decoder = JSONDecoder()
            let tokens = try decoder.decode(TokenResponse.self, from: data)

            // Store new tokens (rotation)
            keychain.storeTokens(
                accessToken: tokens.accessToken,
                refreshToken: tokens.refreshToken,
                expiresIn: tokens.expiresIn
            )
        } else if httpResponse.statusCode == 401 {
            // Refresh token expired, need to re-authenticate
            keychain.clearAll()
            throw AuthError.sessionExpired
        } else {
            let error = try? JSONDecoder().decode(ErrorResponse.self, from: data)
            throw AuthError.serverError(error?.detail ?? "Token refresh failed")
        }
    }

    // MARK: - Logout

    func logout() {
        keychain.clearAll()
    }

    // MARK: - Access Token for Requests

    var accessToken: String? {
        keychain.accessToken
    }
}

// MARK: - Auth Errors
enum AuthError: LocalizedError {
    case invalidURL
    case invalidResponse
    case invalidCode(String)
    case serverError(String)
    case rateLimited
    case notAuthenticated
    case sessionExpired
    case networkError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL"
        case .invalidResponse:
            return "Invalid server response"
        case .invalidCode(let message):
            return message
        case .serverError(let message):
            return message
        case .rateLimited:
            return "Too many requests. Please wait and try again."
        case .notAuthenticated:
            return "Not authenticated"
        case .sessionExpired:
            return "Session expired. Please pair again."
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        }
    }
}
