//
//  EventListViewModel.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation

@Observable
final class EventListViewModel {
    var events: [EventSummary] = []
    var cameras: [Camera] = []
    var isLoading = false
    var errorMessage: String?
    
    private var currentPage = 1
    private var hasMorePages = true
    
    /// Load initial events
    func loadEvents(authService: AuthService, discoveryService: DiscoveryService) async {
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = nil
        currentPage = 1
        
        do {
            let client = APIClient(authService: authService, discoveryService: discoveryService)
            
            // Load both events and cameras
            async let eventsResponse = client.fetchEvents(page: currentPage)
            async let camerasResponse = client.fetchCameras()
            
            let (eventsData, camerasData) = try await (eventsResponse, camerasResponse)
            
            events = eventsData.events
            cameras = camerasData
            hasMorePages = events.count < eventsData.total
            
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    /// Load more events (pagination)
    func loadMoreEvents(authService: AuthService, discoveryService: DiscoveryService) async {
        guard !isLoading && hasMorePages else { return }
        
        isLoading = true
        currentPage += 1
        
        do {
            let client = APIClient(authService: authService, discoveryService: discoveryService)
            let response = try await client.fetchEvents(page: currentPage)
            
            events.append(contentsOf: response.events)
            hasMorePages = events.count < response.total
            
        } catch {
            errorMessage = error.localizedDescription
            currentPage -= 1 // Revert page increment on error
        }
        
        isLoading = false
    }
    
    /// Get camera name for an event
    func cameraName(for event: EventSummary) -> String {
        cameras.first { $0.id == event.cameraId }?.displayName ?? "Unknown Camera"
    }
    
    /// Refresh events
    func refresh(authService: AuthService, discoveryService: DiscoveryService) async {
        await loadEvents(authService: authService, discoveryService: discoveryService)
    }
}
