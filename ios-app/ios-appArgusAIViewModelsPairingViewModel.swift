//
//  PairingViewModel.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation

@Observable
final class PairingViewModel {
    var code = ""
    var isLoading = false
    var errorMessage: String?
    
    /// Formatted code with dash separator (XXX-XXX)
    var formattedCode: String {
        let cleaned = code.filter { $0.isNumber }
        
        guard !cleaned.isEmpty else { return "" }
        
        if cleaned.count <= 3 {
            return String(cleaned)
        } else {
            let firstThree = cleaned.prefix(3)
            let remaining = cleaned.dropFirst(3).prefix(3)
            return "\(firstThree)-\(remaining)"
        }
    }
    
    /// Whether the code is valid (6 digits)
    var isCodeValid: Bool {
        let cleaned = code.filter { $0.isNumber }
        return cleaned.count == 6
    }
    
    /// Update code with new input (filters non-numeric)
    func updateCode(_ newValue: String) {
        let cleaned = newValue.filter { $0.isNumber }
        code = String(cleaned.prefix(6))
        errorMessage = nil
    }
    
    /// Verify the pairing code
    func verifyCode(authService: AuthService) async {
        guard isCodeValid else {
            errorMessage = "Please enter a 6-digit code"
            return
        }
        
        isLoading = true
        errorMessage = nil
        
        do {
            let cleanedCode = code.filter { $0.isNumber }
            try await authService.verifyPairingCode(cleanedCode)
        } catch {
            errorMessage = error.localizedDescription
        }
        
        isLoading = false
    }
}
