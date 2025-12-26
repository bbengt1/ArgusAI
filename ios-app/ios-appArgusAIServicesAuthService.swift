//
//  AuthService.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation
import UIKit

/// Service for handling authentication and pairing
@Observable
final class AuthService {
    private let keychainService: KeychainService
    private let discoveryService: DiscoveryService
    
    private let accessTokenKey = "argusai.accessToken"
    private let refreshTokenKey = "argusai.refreshToken"
    private let tokenExpirationKey = "argusai.tokenExpiration"
    
    var isAuthenticated = false
    var currentToken: AuthToken?
    
    init(keychainService: KeychainService, discoveryService: DiscoveryService) {
        self.keychainService = keychainService
        self.discoveryService = discoveryService
        
        // Check if we have stored tokens
        loadStoredTokens()
    }
    
    /// Load tokens from keychain on app launch
    private func loadStoredTokens() {
        do {
            let accessToken = try keychainService.load(key: accessTokenKey)
            let refreshToken = try keychainService.load(key: refreshTokenKey)
            
            // Check expiration
            if let expirationString = try? keychainService.load(key: tokenExpirationKey),
               let expirationTime = TimeInterval(expirationString) {
                let expirationDate = Date(timeIntervalSince1970: expirationTime)
                let expiresIn = Int(expirationDate.timeIntervalSinceNow)
                
                currentToken = AuthToken(
                    accessToken: accessToken,
                    refreshToken: refreshToken,
                    expiresIn: max(0, expiresIn),
                    tokenType: "Bearer"
                )
                
                isAuthenticated = true
            }
        } catch {
            // No stored tokens or failed to load
            isAuthenticated = false
        }
    }
    
    /// Verify pairing code and get tokens
    func verifyPairingCode(_ code: String) async throws {
        let deviceId = await getDeviceID()
        let deviceName = await UIDevice.current.name
        
        let request = PairingRequest(
            code: code,
            deviceId: deviceId,
            deviceName: deviceName,
            pushToken: nil // Will be set later when push token is available
        )
        
        let url = discoveryService.baseURL.appendingPathComponent("/api/v1/mobile/auth/verify")
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        let (data, response) = try await URLSession.shared.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            throw AuthError.invalidCode
        }
        
        let pairingResponse = try JSONDecoder().decode(PairingResponse.self, from: data)
        let token = pairingResponse.authToken
        
        // Store tokens in keychain
        try saveTokens(token)
        
        currentToken = token
        isAuthenticated = true
    }
    
    /// Refresh the access token
    func refreshAccessToken() async throws {
        guard let currentToken = currentToken else {
            throw AuthError.noRefreshToken
        }
        
        let request = RefreshTokenRequest(refreshToken: currentToken.refreshToken)
        let url = discoveryService.baseURL.appendingPathComponent("/api/v1/mobile/auth/refresh")
        
        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.httpBody = try JSONEncoder().encode(request)
        
        let (data, response) = try await URLSession.shared.data(for: urlRequest)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            // Token refresh failed, log out
            signOut()
            throw AuthError.refreshFailed
        }
        
        let refreshResponse = try JSONDecoder().decode(RefreshTokenResponse.self, from: data)
        let newToken = refreshResponse.authToken
        
        // Store new tokens
        try saveTokens(newToken)
        
        self.currentToken = newToken
    }
    
    /// Save tokens to keychain
    private func saveTokens(_ token: AuthToken) throws {
        try keychainService.save(token.accessToken, forKey: accessTokenKey)
        try keychainService.save(token.refreshToken, forKey: refreshTokenKey)
        
        let expirationTime = token.expirationDate.timeIntervalSince1970
        try keychainService.save(String(expirationTime), forKey: tokenExpirationKey)
    }
    
    /// Sign out and clear stored credentials
    func signOut() {
        try? keychainService.delete(accessTokenKey)
        try? keychainService.delete(refreshTokenKey)
        try? keychainService.delete(tokenExpirationKey)
        
        currentToken = nil
        isAuthenticated = false
    }
    
    /// Get or create device ID
    private func getDeviceID() async -> String {
        let deviceIDKey = "argusai.deviceID"
        
        if let existingID = try? keychainService.load(key: deviceIDKey) {
            return existingID
        }
        
        // Generate new device ID
        let newID = UUID().uuidString
        try? keychainService.save(newID, forKey: deviceIDKey)
        return newID
    }
}

enum AuthError: LocalizedError {
    case invalidCode
    case invalidResponse
    case noRefreshToken
    case refreshFailed
    
    var errorDescription: String? {
        switch self {
        case .invalidCode:
            return "Invalid pairing code. Please check and try again."
        case .invalidResponse:
            return "Invalid response from server."
        case .noRefreshToken:
            return "No refresh token available."
        case .refreshFailed:
            return "Failed to refresh token. Please sign in again."
        }
    }
}
