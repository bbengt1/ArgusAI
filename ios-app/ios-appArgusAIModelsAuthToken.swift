//
//  AuthToken.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation

/// JWT token pair for authentication
struct AuthToken: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
    }
    
    /// Calculate when the access token expires
    var expirationDate: Date {
        Date().addingTimeInterval(TimeInterval(expiresIn))
    }
}

/// Request for pairing verification
struct PairingRequest: Codable {
    let code: String
    let deviceId: String
    let deviceName: String
    let pushToken: String?
    
    enum CodingKeys: String, CodingKey {
        case code
        case deviceId = "device_id"
        case deviceName = "device_name"
        case pushToken = "push_token"
    }
}

/// Response from pairing verification
struct PairingResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
    }
    
    var authToken: AuthToken {
        AuthToken(
            accessToken: accessToken,
            refreshToken: refreshToken,
            expiresIn: expiresIn,
            tokenType: tokenType
        )
    }
}

/// Request for token refresh
struct RefreshTokenRequest: Codable {
    let refreshToken: String
    
    enum CodingKeys: String, CodingKey {
        case refreshToken = "refresh_token"
    }
}

/// Response from token refresh
struct RefreshTokenResponse: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int
    let tokenType: String
    
    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case tokenType = "token_type"
    }
    
    var authToken: AuthToken {
        AuthToken(
            accessToken: accessToken,
            refreshToken: refreshToken,
            expiresIn: expiresIn,
            tokenType: tokenType
        )
    }
}
