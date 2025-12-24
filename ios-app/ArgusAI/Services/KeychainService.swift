//
//  KeychainService.swift
//  ArgusAI
//
//  Secure credential storage using iOS Keychain.
//

import Foundation
import Security

final class KeychainService {
    static let shared = KeychainService()

    private let serviceName = "com.argusai.mobile"

    private enum Keys {
        static let accessToken = "access_token"
        static let refreshToken = "refresh_token"
        static let deviceId = "device_id"
        static let deviceName = "device_name"
        static let tokenExpiresAt = "token_expires_at"
    }

    private init() {}

    // MARK: - Access Token

    var accessToken: String? {
        get { retrieve(key: Keys.accessToken) }
        set {
            if let value = newValue {
                save(key: Keys.accessToken, value: value)
            } else {
                delete(key: Keys.accessToken)
            }
        }
    }

    // MARK: - Refresh Token

    var refreshToken: String? {
        get { retrieve(key: Keys.refreshToken) }
        set {
            if let value = newValue {
                save(key: Keys.refreshToken, value: value)
            } else {
                delete(key: Keys.refreshToken)
            }
        }
    }

    // MARK: - Device ID

    var deviceId: String? {
        get { retrieve(key: Keys.deviceId) }
        set {
            if let value = newValue {
                save(key: Keys.deviceId, value: value)
            } else {
                delete(key: Keys.deviceId)
            }
        }
    }

    // MARK: - Device Name

    var deviceName: String? {
        get { retrieve(key: Keys.deviceName) }
        set {
            if let value = newValue {
                save(key: Keys.deviceName, value: value)
            } else {
                delete(key: Keys.deviceName)
            }
        }
    }

    // MARK: - Token Expiration

    var tokenExpiresAt: Date? {
        get {
            guard let string = retrieve(key: Keys.tokenExpiresAt),
                  let interval = TimeInterval(string) else { return nil }
            return Date(timeIntervalSince1970: interval)
        }
        set {
            if let date = newValue {
                save(key: Keys.tokenExpiresAt, value: String(date.timeIntervalSince1970))
            } else {
                delete(key: Keys.tokenExpiresAt)
            }
        }
    }

    // MARK: - Store Tokens

    func storeTokens(accessToken: String, refreshToken: String, expiresIn: Int) {
        self.accessToken = accessToken
        self.refreshToken = refreshToken
        self.tokenExpiresAt = Date().addingTimeInterval(TimeInterval(expiresIn))
    }

    // MARK: - Clear All

    func clearAll() {
        accessToken = nil
        refreshToken = nil
        deviceId = nil
        deviceName = nil
        tokenExpiresAt = nil
    }

    // MARK: - Token Validity

    var isTokenValid: Bool {
        guard accessToken != nil,
              let expiresAt = tokenExpiresAt else { return false }
        // Consider token invalid if less than 5 minutes remaining
        return expiresAt.timeIntervalSinceNow > 300
    }

    var needsRefresh: Bool {
        guard let expiresAt = tokenExpiresAt else { return true }
        // Refresh if less than 5 minutes remaining
        return expiresAt.timeIntervalSinceNow < 300
    }

    // MARK: - Private Keychain Operations

    private func save(key: String, value: String) {
        guard let data = value.data(using: .utf8) else { return }

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]

        // Delete existing item first
        SecItemDelete(query as CFDictionary)

        // Add new item
        let status = SecItemAdd(query as CFDictionary, nil)
        if status != errSecSuccess {
            print("Keychain save error for \(key): \(status)")
        }
    }

    private func retrieve(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)

        guard status == errSecSuccess,
              let data = result as? Data,
              let string = String(data: data, encoding: .utf8) else {
            return nil
        }

        return string
    }

    private func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: serviceName,
            kSecAttrAccount as String: key
        ]

        SecItemDelete(query as CFDictionary)
    }
}
