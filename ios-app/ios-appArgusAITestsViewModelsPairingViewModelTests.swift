//
//  PairingViewModelTests.swift
//  ArgusAITests
//
//  Created on 2025-12-26.
//

import Testing
@testable import ArgusAI

@Suite("Pairing View Model Tests")
struct PairingViewModelTests {
    
    @Test("Code validation filters non-numeric characters")
    func testCodeValidation() {
        let viewModel = PairingViewModel()
        
        viewModel.updateCode("123abc456")
        
        #expect(viewModel.code == "123456")
    }
    
    @Test("Code is limited to 6 digits")
    func testCodeLimit() {
        let viewModel = PairingViewModel()
        
        viewModel.updateCode("123456789")
        
        #expect(viewModel.code == "123456")
    }
    
    @Test("Formatted code includes dash separator")
    func testFormattedCode() {
        let viewModel = PairingViewModel()
        
        viewModel.updateCode("123456")
        
        #expect(viewModel.formattedCode == "123-456")
    }
    
    @Test("Formatted code handles partial input")
    func testFormattedCodePartial() {
        let viewModel = PairingViewModel()
        
        viewModel.updateCode("123")
        #expect(viewModel.formattedCode == "123")
        
        viewModel.updateCode("1234")
        #expect(viewModel.formattedCode == "123-4")
    }
    
    @Test("Code validity check")
    func testCodeValidity() {
        let viewModel = PairingViewModel()
        
        viewModel.updateCode("12345")
        #expect(!viewModel.isCodeValid)
        
        viewModel.updateCode("123456")
        #expect(viewModel.isCodeValid)
    }
    
    @Test("Error message is cleared when code is updated")
    func testErrorMessageCleared() {
        let viewModel = PairingViewModel()
        viewModel.errorMessage = "Test error"
        
        viewModel.updateCode("1")
        
        #expect(viewModel.errorMessage == nil)
    }
}
