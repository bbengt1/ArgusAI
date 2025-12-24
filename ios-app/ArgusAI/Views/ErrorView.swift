//
//  ErrorView.swift
//  ArgusAI
//
//  Reusable error view with retry button.
//

import SwiftUI

struct ErrorView: View {
    let message: String
    let retryAction: () -> Void
    var icon: String = "exclamationmark.triangle"

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundStyle(.red)

            Text("Something went wrong")
                .font(.headline)

            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            Button("Try Again", action: retryAction)
                .buttonStyle(.borderedProminent)
        }
        .padding()
    }
}

// MARK: - Network Error View
struct NetworkErrorView: View {
    let retryAction: () -> Void

    var body: some View {
        ErrorView(
            message: "Unable to connect. Please check your internet connection and try again.",
            retryAction: retryAction,
            icon: "wifi.slash"
        )
    }
}

// MARK: - Empty State View
struct EmptyStateView: View {
    let title: String
    let message: String
    let icon: String
    var action: (() -> Void)?
    var actionTitle: String = "Refresh"

    var body: some View {
        VStack(spacing: 16) {
            Image(systemName: icon)
                .font(.system(size: 48))
                .foregroundStyle(.gray)

            Text(title)
                .font(.headline)

            Text(message)
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)

            if let action = action {
                Button(actionTitle, action: action)
                    .buttonStyle(.bordered)
            }
        }
        .padding()
    }
}

// MARK: - Loading Overlay
struct LoadingOverlay: View {
    let message: String

    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()

            VStack(spacing: 16) {
                ProgressView()
                    .scaleEffect(1.5)

                Text(message)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .padding(24)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(.regularMaterial)
            )
        }
    }
}

#Preview("Error View") {
    ErrorView(message: "Failed to load events. The server returned an error.") {
        print("Retry tapped")
    }
}

#Preview("Network Error") {
    NetworkErrorView {
        print("Retry tapped")
    }
}

#Preview("Empty State") {
    EmptyStateView(
        title: "No Events",
        message: "No events have been detected yet. Events will appear here when motion is detected.",
        icon: "bell.slash"
    )
}
