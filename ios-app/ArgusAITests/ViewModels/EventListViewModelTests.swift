//
//  EventListViewModelTests.swift
//  ArgusAITests
//
//  Unit tests for EventListViewModel.
//

import XCTest
@testable import ArgusAI

final class EventListViewModelTests: XCTestCase {

    var viewModel: EventListViewModel!

    override func setUp() {
        super.setUp()
        viewModel = EventListViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: - Initial State Tests

    func testInitialStateIsEmpty() {
        XCTAssertTrue(viewModel.events.isEmpty)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertFalse(viewModel.hasMore)
    }

    // MARK: - Event Summary Model Tests

    func testEventSummaryEquality() {
        let id = UUID()
        let cameraId = UUID()
        let date = Date()

        let event1 = EventSummary(
            id: id,
            cameraId: cameraId,
            cameraName: "Front Door",
            timestamp: date,
            description: "Person detected",
            smartDetectionType: .person,
            confidence: 95,
            hasThumbnail: true
        )

        let event2 = EventSummary(
            id: id,
            cameraId: cameraId,
            cameraName: "Front Door",
            timestamp: date,
            description: "Person detected",
            smartDetectionType: .person,
            confidence: 95,
            hasThumbnail: true
        )

        XCTAssertEqual(event1, event2)
    }

    func testEventSummaryIdentifiable() {
        let event = EventSummary(
            id: UUID(),
            cameraId: UUID(),
            cameraName: "Front Door",
            timestamp: Date(),
            description: "Person detected",
            smartDetectionType: .person,
            confidence: 95,
            hasThumbnail: true
        )

        XCTAssertNotNil(event.id)
    }

    // MARK: - Smart Detection Type Tests

    func testSmartDetectionTypeDisplayNames() {
        XCTAssertEqual(SmartDetectionType.person.displayName, "Person")
        XCTAssertEqual(SmartDetectionType.vehicle.displayName, "Vehicle")
        XCTAssertEqual(SmartDetectionType.package.displayName, "Package")
        XCTAssertEqual(SmartDetectionType.animal.displayName, "Animal")
        XCTAssertEqual(SmartDetectionType.motion.displayName, "Motion")
    }

    func testSmartDetectionTypeIconNames() {
        XCTAssertEqual(SmartDetectionType.person.iconName, "person.fill")
        XCTAssertEqual(SmartDetectionType.vehicle.iconName, "car.fill")
        XCTAssertEqual(SmartDetectionType.package.iconName, "shippingbox.fill")
        XCTAssertEqual(SmartDetectionType.animal.iconName, "pawprint.fill")
        XCTAssertEqual(SmartDetectionType.motion.iconName, "waveform")
    }

    // MARK: - Analysis Mode Tests

    func testAnalysisModeDisplayNames() {
        XCTAssertEqual(AnalysisMode.singleFrame.displayName, "Single Frame")
        XCTAssertEqual(AnalysisMode.multiFrame.displayName, "Multi-Frame")
        XCTAssertEqual(AnalysisMode.videoNative.displayName, "Video Native")
    }
}
