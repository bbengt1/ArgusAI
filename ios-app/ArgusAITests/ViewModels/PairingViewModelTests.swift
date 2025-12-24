//
//  PairingViewModelTests.swift
//  ArgusAITests
//
//  Unit tests for PairingViewModel.
//

import XCTest
@testable import ArgusAI

final class PairingViewModelTests: XCTestCase {

    var viewModel: PairingViewModel!

    override func setUp() {
        super.setUp()
        viewModel = PairingViewModel()
    }

    override func tearDown() {
        viewModel = nil
        super.tearDown()
    }

    // MARK: - Code Validation Tests

    func testEmptyCodeIsNotComplete() {
        viewModel.code = ""
        XCTAssertFalse(viewModel.isCodeComplete)
    }

    func testPartialCodeIsNotComplete() {
        viewModel.code = "123"
        XCTAssertFalse(viewModel.isCodeComplete)
    }

    func testFullCodeIsComplete() {
        viewModel.code = "123456"
        XCTAssertTrue(viewModel.isCodeComplete)
    }

    func testCodeLimitedToSixDigits() {
        viewModel.code = "1234567890"
        XCTAssertEqual(viewModel.code, "123456")
    }

    func testNonNumericCharactersFiltered() {
        viewModel.code = "12ab34cd"
        XCTAssertEqual(viewModel.code, "1234")
    }

    func testDigitAtIndexReturnsCorrectDigit() {
        viewModel.code = "847291"

        XCTAssertEqual(viewModel.digit(at: 0), "8")
        XCTAssertEqual(viewModel.digit(at: 1), "4")
        XCTAssertEqual(viewModel.digit(at: 2), "7")
        XCTAssertEqual(viewModel.digit(at: 3), "2")
        XCTAssertEqual(viewModel.digit(at: 4), "9")
        XCTAssertEqual(viewModel.digit(at: 5), "1")
    }

    func testDigitAtIndexOutOfBoundsReturnsNil() {
        viewModel.code = "123"

        XCTAssertNil(viewModel.digit(at: 3))
        XCTAssertNil(viewModel.digit(at: 5))
    }

    func testTypingClearsErrorMessage() {
        viewModel.errorMessage = "Invalid code"
        viewModel.code = "1"

        XCTAssertNil(viewModel.errorMessage)
    }

    func testInitialState() {
        XCTAssertEqual(viewModel.code, "")
        XCTAssertFalse(viewModel.isCodeFieldFocused)
        XCTAssertFalse(viewModel.isLoading)
        XCTAssertNil(viewModel.errorMessage)
        XCTAssertFalse(viewModel.isCodeComplete)
    }

    // MARK: - Edge Cases

    func testCodeWithSpacesFiltered() {
        viewModel.code = "1 2 3 4 5 6"
        XCTAssertEqual(viewModel.code, "123456")
    }

    func testCodeWithSpecialCharactersFiltered() {
        viewModel.code = "!@#$%^123456"
        XCTAssertEqual(viewModel.code, "123456")
    }

    func testCodeWithMixedContentFiltered() {
        viewModel.code = "a1b2c3d4e5f6g"
        XCTAssertEqual(viewModel.code, "123456")
    }
}
