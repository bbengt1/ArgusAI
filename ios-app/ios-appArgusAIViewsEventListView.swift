//
//  EventListView.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import SwiftUI

struct EventListView: View {
    @Environment(AuthService.self) private var authService
    @Environment(DiscoveryService.self) private var discoveryService
    @State private var viewModel = EventListViewModel()
    
    var body: some View {
        NavigationStack {
            Group {
                if viewModel.isLoading && viewModel.events.isEmpty {
                    ProgressView("Loading events...")
                } else if let error = viewModel.errorMessage {
                    ErrorView(
                        title: "Failed to Load Events",
                        message: error,
                        retryAction: {
                            Task {
                                await viewModel.refresh(
                                    authService: authService,
                                    discoveryService: discoveryService
                                )
                            }
                        }
                    )
                } else if viewModel.events.isEmpty {
                    ContentUnavailableView(
                        "No Events",
                        systemImage: "video.slash",
                        description: Text("No security events have been detected yet.")
                    )
                } else {
                    eventsList
                }
            }
            .navigationTitle("Security Events")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button(action: {
                        authService.signOut()
                    }) {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                    }
                }
            }
            .refreshable {
                await viewModel.refresh(
                    authService: authService,
                    discoveryService: discoveryService
                )
            }
            .task {
                await viewModel.loadEvents(
                    authService: authService,
                    discoveryService: discoveryService
                )
            }
        }
    }
    
    private var eventsList: some View {
        List {
            ForEach(viewModel.events) { event in
                NavigationLink(destination: EventDetailView(eventId: event.id)) {
                    EventRowView(event: event, cameraName: viewModel.cameraName(for: event))
                }
            }
            
            // Load more indicator
            if viewModel.isLoading {
                HStack {
                    Spacer()
                    ProgressView()
                    Spacer()
                }
                .listRowBackground(Color.clear)
            }
        }
        .listStyle(.plain)
    }
}

struct EventRowView: View {
    let event: EventSummary
    let cameraName: String
    
    var body: some View {
        HStack(spacing: 12) {
            // Thumbnail placeholder
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(.systemGray5))
                .frame(width: 80, height: 60)
                .overlay {
                    Image(systemName: event.detectionType.iconName)
                        .foregroundStyle(.secondary)
                }
            
            // Event info
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Image(systemName: event.detectionType.iconName)
                        .foregroundStyle(.blue)
                        .font(.caption)
                    
                    Text(event.detectionType.displayName)
                        .font(.headline)
                }
                
                Text(event.aiDescription)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
                
                HStack {
                    Text(cameraName)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    
                    Spacer()
                    
                    Text(event.timestamp, style: .relative)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    EventListView()
        .environment(AuthService(
            keychainService: KeychainService(),
            discoveryService: DiscoveryService()
        ))
        .environment(DiscoveryService())
}
