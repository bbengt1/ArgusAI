//
//  ArgusAIApp.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import SwiftUI

@main
struct ArgusAIApp: App {
    @State private var keychainService = KeychainService()
    @State private var discoveryService = DiscoveryService()
    @State private var authService: AuthService
    @State private var pushService: PushService
    
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    init() {
        let keychain = KeychainService()
        let discovery = DiscoveryService()
        let auth = AuthService(keychainService: keychain, discoveryService: discovery)
        let push = PushService(authService: auth, discoveryService: discovery)
        
        _keychainService = State(initialValue: keychain)
        _discoveryService = State(initialValue: discovery)
        _authService = State(initialValue: auth)
        _pushService = State(initialValue: push)
    }
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(keychainService)
                .environment(discoveryService)
                .environment(authService)
                .environment(pushService)
                .onAppear {
                    appDelegate.pushService = pushService
                    
                    // Start local device discovery
                    discoveryService.startDiscovery()
                    
                    // Request push notification permission
                    Task {
                        try? await pushService.requestAuthorization()
                    }
                }
        }
    }
}

struct ContentView: View {
    @Environment(AuthService.self) private var authService
    
    var body: some View {
        if authService.isAuthenticated {
            EventListView()
        } else {
            PairingView()
        }
    }
}

// MARK: - App Delegate for Push Notifications

class AppDelegate: NSObject, UIApplicationDelegate {
    var pushService: PushService?
    
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        return true
    }
    
    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        pushService?.didRegisterForRemoteNotifications(withDeviceToken: deviceToken)
    }
    
    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        pushService?.didFailToRegisterForRemoteNotifications(withError: error)
    }
    
    func application(
        _ application: UIApplication,
        didReceiveRemoteNotification userInfo: [AnyHashable: Any],
        fetchCompletionHandler completionHandler: @escaping (UIBackgroundFetchResult) -> Void
    ) {
        if let eventId = pushService?.handleNotification(userInfo) {
            print("Received push notification for event: \(eventId)")
            completionHandler(.newData)
        } else {
            completionHandler(.noData)
        }
    }
}
