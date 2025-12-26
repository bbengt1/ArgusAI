//
//  PushService.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation
import UserNotifications

/// Service for handling push notifications
@Observable
final class PushService: NSObject {
    private let authService: AuthService
    private let discoveryService: DiscoveryService
    
    var pushToken: String?
    var isRegistered = false
    
    init(authService: AuthService, discoveryService: DiscoveryService) {
        self.authService = authService
        self.discoveryService = discoveryService
        super.init()
    }
    
    /// Request push notification permission
    func requestAuthorization() async throws {
        let center = UNUserNotificationCenter.current()
        
        let granted = try await center.requestAuthorization(options: [.alert, .sound, .badge])
        
        if granted {
            await registerForRemoteNotifications()
        }
    }
    
    /// Register for remote notifications
    @MainActor
    private func registerForRemoteNotifications() async {
        UIApplication.shared.registerForRemoteNotifications()
    }
    
    /// Handle successful push token registration
    func didRegisterForRemoteNotifications(withDeviceToken deviceToken: Data) {
        let tokenParts = deviceToken.map { String(format: "%02.2hhx", $0) }
        let token = tokenParts.joined()
        
        pushToken = token
        
        // Send token to backend if authenticated
        if authService.isAuthenticated {
            Task {
                await sendTokenToBackend(token)
            }
        }
    }
    
    /// Handle push token registration failure
    func didFailToRegisterForRemoteNotifications(withError error: Error) {
        print("Failed to register for push notifications: \(error)")
    }
    
    /// Send push token to backend
    private func sendTokenToBackend(_ token: String) async {
        do {
            let client = APIClient(authService: authService, discoveryService: discoveryService)
            try await client.registerPushToken(token)
            isRegistered = true
            print("Successfully registered push token with backend")
        } catch {
            print("Failed to register push token with backend: \(error)")
        }
    }
    
    /// Handle received push notification
    func handleNotification(_ userInfo: [AnyHashable: Any]) -> String? {
        // Extract event ID from notification payload
        if let eventId = userInfo["event_id"] as? String {
            return eventId
        }
        return nil
    }
}
