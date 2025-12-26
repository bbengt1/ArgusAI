//
//  EventDetailViewModel.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation
import UIKit

@Observable
final class EventDetailViewModel {
    var eventDetail: EventDetail?
    var camera: Camera?
    var thumbnailImage: UIImage?
    var isLoading = false
    var errorMessage: String?
    
    /// Load event detail and thumbnail
    func loadEvent(id: String, authService: AuthService, discoveryService: DiscoveryService) async {
        guard !isLoading else { return }
        
        isLoading = true
        errorMessage = nil
        
        do {
            let client = APIClient(authService: authService, discoveryService: discoveryService)
            
            // Load event detail
            let detail = try await client.fetchEventDetail(id: id)
            eventDetail = detail
            
            // Load camera info
            let cameras = try await client.fetchCameras()
            camera = cameras.first { $0.id == detail.cameraId }
            
            // Load thumbnail
            if detail.thumbnailPath != nil {
                let thumbnailData = try await client.fetchEventThumbnail(id: id)
                thumbnailImage = UIImage(data: thumbnailData)
            }
            
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
    
    /// Format timestamp for display
    var formattedTimestamp: String {
        guard let detail = eventDetail else { return "" }
        
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: detail.timestamp)
    }
    
    /// Confidence percentage string
    var confidenceString: String {
        guard let confidence = eventDetail?.confidence else { return "N/A" }
        return String(format: "%.0f%%", confidence * 100)
    }
}
