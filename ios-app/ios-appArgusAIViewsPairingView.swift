//
//  PairingView.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import SwiftUI

struct PairingView: View {
    @Environment(AuthService.self) private var authService
    @State private var viewModel = PairingViewModel()
    @FocusState private var isCodeFieldFocused: Bool
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 32) {
                // Header
                VStack(spacing: 16) {
                    Image(systemName: "shield.checkered")
                        .font(.system(size: 80))
                        .foregroundStyle(.blue)
                    
                    Text("Welcome to ArgusAI")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    
                    Text("Enter the 6-digit pairing code from your ArgusAI web dashboard")
                        .font(.body)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal)
                }
                
                // Code input
                VStack(spacing: 16) {
                    TextField("000-000", text: $viewModel.code)
                        .font(.system(size: 48, weight: .medium, design: .rounded))
                        .multilineTextAlignment(.center)
                        .keyboardType(.numberPad)
                        .focused($isCodeFieldFocused)
                        .onChange(of: viewModel.code) { _, newValue in
                            viewModel.updateCode(newValue)
                        }
                        .padding()
                        .background(Color(.secondarySystemBackground))
                        .cornerRadius(12)
                        .padding(.horizontal)
                    
                    if let error = viewModel.errorMessage {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                    }
                }
                
                // Pair button
                Button(action: {
                    isCodeFieldFocused = false
                    Task {
                        await viewModel.verifyCode(authService: authService)
                    }
                }) {
                    HStack {
                        if viewModel.isLoading {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Text("Pair Device")
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(viewModel.isCodeValid ? Color.blue : Color.gray)
                    .foregroundStyle(.white)
                    .cornerRadius(12)
                    .padding(.horizontal)
                }
                .disabled(!viewModel.isCodeValid || viewModel.isLoading)
                
                Spacer()
            }
            .padding(.top, 60)
            .navigationTitle("Pair Device")
            .navigationBarTitleDisplayMode(.inline)
            .onAppear {
                isCodeFieldFocused = true
            }
        }
    }
}

#Preview {
    PairingView()
        .environment(AuthService(
            keychainService: KeychainService(),
            discoveryService: DiscoveryService()
        ))
}
