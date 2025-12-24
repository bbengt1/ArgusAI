//
//  PushService.swift
//  ArgusAI
//
//  Push notification service for APNS integration.
//

import Foundation
import UserNotifications
import UIKit

@Observable
final class PushService: NSObject {
    static let shared = PushService()

    var deviceToken: String?
    var lastError: String?
    var isRegistered = false

    private let session: URLSession

    override init() {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        self.session = URLSession(configuration: config)
        super.init()

        UNUserNotificationCenter.current().delegate = self
    }

    // MARK: - Token Handling

    func didRegisterForRemoteNotifications(deviceToken: Data) {
        let token = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        self.deviceToken = token
        print("APNS Device Token: \(token)")

        // Register with backend
        Task {
            await registerWithBackend()
        }
    }

    func didFailToRegisterForRemoteNotifications(error: Error) {
        self.lastError = error.localizedDescription
        print("Failed to register for push notifications: \(error.localizedDescription)")
    }

    // MARK: - Backend Registration

    private func registerWithBackend() async {
        guard let token = deviceToken else { return }
        guard let accessToken = KeychainService.shared.accessToken,
              let deviceId = KeychainService.shared.deviceId else {
            print("Cannot register push: not authenticated")
            return
        }

        let request = PushRegisterRequest(deviceToken: token, deviceId: deviceId)

        let baseURL = DiscoveryService.shared.currentBaseURL
        guard let url = URL(string: "\(baseURL)/api/v1/mobile/push/register") else {
            lastError = "Invalid URL"
            return
        }

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        urlRequest.httpBody = try? JSONEncoder().encode(request)

        do {
            let (_, response) = try await session.data(for: urlRequest)

            if let httpResponse = response as? HTTPURLResponse,
               httpResponse.statusCode == 200 || httpResponse.statusCode == 201 {
                isRegistered = true
                lastError = nil
                print("Successfully registered for push notifications")
            } else {
                lastError = "Failed to register push"
            }
        } catch {
            lastError = error.localizedDescription
            print("Push registration error: \(error.localizedDescription)")
        }
    }

    // MARK: - Handle Notification Tap

    func handleNotificationTap(eventId: String?) {
        guard let eventId = eventId,
              let uuid = UUID(uuidString: eventId) else { return }

        // Post notification to navigate to event
        NotificationCenter.default.post(
            name: .navigateToEvent,
            object: nil,
            userInfo: ["eventId": uuid]
        )
    }
}

// MARK: - UNUserNotificationCenterDelegate
extension PushService: UNUserNotificationCenterDelegate {
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        // Show notification even when app is in foreground
        completionHandler([.banner, .sound, .badge])
    }

    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo

        // Extract event ID from payload
        if let eventId = userInfo["event_id"] as? String {
            handleNotificationTap(eventId: eventId)
        }

        completionHandler()
    }
}

// MARK: - Notification Name
extension Notification.Name {
    static let navigateToEvent = Notification.Name("navigateToEvent")
}
