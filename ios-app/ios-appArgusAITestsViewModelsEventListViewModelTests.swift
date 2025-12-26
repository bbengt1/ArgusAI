//
//  EventListViewModelTests.swift
//  ArgusAITests
//
//  Created on 2025-12-26.
//

import Testing
import Foundation
@testable import ArgusAI

@Suite("Event List View Model Tests")
struct EventListViewModelTests {
    
    @Test("Camera name lookup returns correct name")
    func testCameraNameLookup() {
        let viewModel = EventListViewModel()
        
        // Setup test data
        viewModel.cameras = [
            Camera(id: "cam1", name: "Front Door", location: "Entry", isOnline: true, lastSeen: Date()),
            Camera(id: "cam2", name: "Backyard", location: "Garden", isOnline: true, lastSeen: Date())
        ]
        
        let event = EventSummary(
            id: "event1",
            cameraId: "cam1",
            timestamp: Date(),
            aiDescription: "Test event",
            thumbnailPath: nil,
            detectionType: .motion
        )
        
        let cameraName = viewModel.cameraName(for: event)
        
        #expect(cameraName == "Front Door (Entry)")
    }
    
    @Test("Camera name returns Unknown for missing camera")
    func testCameraNameUnknown() {
        let viewModel = EventListViewModel()
        
        viewModel.cameras = [
            Camera(id: "cam1", name: "Front Door", location: nil, isOnline: true, lastSeen: Date())
        ]
        
        let event = EventSummary(
            id: "event1",
            cameraId: "cam2",
            timestamp: Date(),
            aiDescription: "Test event",
            thumbnailPath: nil,
            detectionType: .motion
        )
        
        let cameraName = viewModel.cameraName(for: event)
        
        #expect(cameraName == "Unknown Camera")
    }
    
    @Test("Detection type display names")
    func testDetectionTypeDisplayNames() {
        #expect(DetectionType.motion.displayName == "Motion")
        #expect(DetectionType.person.displayName == "Person")
        #expect(DetectionType.vehicle.displayName == "Vehicle")
        #expect(DetectionType.animal.displayName == "Animal")
        #expect(DetectionType.package.displayName == "Package")
        #expect(DetectionType.unknown.displayName == "Unknown")
    }
    
    @Test("Detection type icon names")
    func testDetectionTypeIcons() {
        #expect(DetectionType.motion.iconName == "waveform.path.ecg")
        #expect(DetectionType.person.iconName == "person.fill")
        #expect(DetectionType.vehicle.iconName == "car.fill")
        #expect(DetectionType.animal.iconName == "pawprint.fill")
        #expect(DetectionType.package.iconName == "shippingbox.fill")
        #expect(DetectionType.unknown.iconName == "questionmark.circle.fill")
    }
}
