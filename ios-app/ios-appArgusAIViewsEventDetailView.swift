//
//  EventDetailView.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import SwiftUI

struct EventDetailView: View {
    let eventId: String
    
    @Environment(AuthService.self) private var authService
    @Environment(DiscoveryService.self) private var discoveryService
    @State private var viewModel = EventDetailViewModel()
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                if viewModel.isLoading {
                    ProgressView("Loading event...")
                        .frame(maxWidth: .infinity)
                        .padding(.top, 100)
                } else if let error = viewModel.errorMessage {
                    ErrorView(
                        title: "Failed to Load Event",
                        message: error,
                        retryAction: {
                            Task {
                                await viewModel.loadEvent(
                                    id: eventId,
                                    authService: authService,
                                    discoveryService: discoveryService
                                )
                            }
                        }
                    )
                } else if let event = viewModel.eventDetail {
                    eventDetailContent(event: event)
                }
            }
            .padding()
        }
        .navigationTitle("Event Detail")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.loadEvent(
                id: eventId,
                authService: authService,
                discoveryService: discoveryService
            )
        }
    }
    
    @ViewBuilder
    private func eventDetailContent(event: EventDetail) -> some View {
        // Thumbnail
        if let image = viewModel.thumbnailImage {
            Image(uiImage: image)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(maxWidth: .infinity)
                .cornerRadius(12)
        } else {
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.systemGray5))
                .frame(height: 250)
                .overlay {
                    Image(systemName: event.detectionType.iconName)
                        .font(.system(size: 60))
                        .foregroundStyle(.secondary)
                }
        }
        
        // Detection type badge
        HStack {
            Image(systemName: event.detectionType.iconName)
            Text(event.detectionType.displayName)
        }
        .font(.headline)
        .padding(.horizontal, 12)
        .padding(.vertical, 6)
        .background(Color.blue.opacity(0.1))
        .foregroundStyle(.blue)
        .cornerRadius(8)
        
        // AI Description
        VStack(alignment: .leading, spacing: 8) {
            Text("Description")
                .font(.headline)
            
            Text(event.aiDescription)
                .font(.body)
                .foregroundStyle(.secondary)
        }
        
        Divider()
        
        // Details
        VStack(alignment: .leading, spacing: 12) {
            Text("Details")
                .font(.headline)
            
            DetailRow(label: "Camera", value: viewModel.camera?.displayName ?? "Unknown")
            DetailRow(label: "Time", value: viewModel.formattedTimestamp)
            
            if let confidence = event.confidence {
                DetailRow(label: "Confidence", value: viewModel.confidenceString)
            }
        }
        
        // Metadata
        if let metadata = event.metadata, !metadata.isEmpty {
            Divider()
            
            VStack(alignment: .leading, spacing: 12) {
                Text("Additional Info")
                    .font(.headline)
                
                ForEach(Array(metadata.keys.sorted()), id: \.self) { key in
                    DetailRow(label: key, value: metadata[key] ?? "")
                }
            }
        }
    }
}

struct DetailRow: View {
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Text(label)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            
            Spacer()
            
            Text(value)
                .font(.subheadline)
        }
    }
}

#Preview {
    NavigationStack {
        EventDetailView(eventId: "test-event-id")
            .environment(AuthService(
                keychainService: KeychainService(),
                discoveryService: DiscoveryService()
            ))
            .environment(DiscoveryService())
    }
}
