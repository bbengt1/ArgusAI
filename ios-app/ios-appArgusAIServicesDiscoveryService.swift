//
//  DiscoveryService.swift
//  ArgusAI
//
//  Created on 2025-12-26.
//

import Foundation
import Network

/// Service for discovering local ArgusAI devices via Bonjour
@Observable
final class DiscoveryService {
    private let serviceName = "_argusai._tcp"
    private var browser: NWBrowser?
    
    var localDeviceURL: URL?
    var cloudRelayURL: String = "https://your-argusai-instance.example.com"
    var isDiscovering = false
    
    /// Current API base URL (local if found, otherwise cloud)
    var baseURL: URL {
        localDeviceURL ?? URL(string: cloudRelayURL)!
    }
    
    /// Start discovering local ArgusAI devices
    func startDiscovery() {
        guard !isDiscovering else { return }
        
        isDiscovering = true
        
        let parameters = NWParameters()
        parameters.includePeerToPeer = true
        
        browser = NWBrowser(for: .bonjour(type: serviceName, domain: nil), using: parameters)
        
        browser?.stateUpdateHandler = { [weak self] state in
            guard let self = self else { return }
            
            switch state {
            case .ready:
                print("Bonjour browser ready")
            case .failed(let error):
                print("Bonjour browser failed: \(error)")
                self.isDiscovering = false
            case .cancelled:
                self.isDiscovering = false
            default:
                break
            }
        }
        
        browser?.browseResultsChangedHandler = { [weak self] results, changes in
            guard let self = self else { return }
            
            // Take the first available result
            if let result = results.first {
                self.resolveEndpoint(result.endpoint)
            } else {
                self.localDeviceURL = nil
            }
        }
        
        browser?.start(queue: .main)
    }
    
    /// Stop discovering local devices
    func stopDiscovery() {
        browser?.cancel()
        browser = nil
        isDiscovering = false
    }
    
    /// Resolve a discovered endpoint to a URL
    private func resolveEndpoint(_ endpoint: NWEndpoint) {
        guard case .service(let name, let type, let domain, _) = endpoint else {
            return
        }
        
        // Create a connection to resolve the endpoint
        let connection = NWConnection(to: endpoint, using: .tcp)
        
        connection.stateUpdateHandler = { [weak self] state in
            guard let self = self else { return }
            
            switch state {
            case .ready:
                if let path = connection.currentPath,
                   let remoteEndpoint = path.remoteEndpoint,
                   case .hostPort(let host, let port) = remoteEndpoint {
                    
                    let hostString: String
                    switch host {
                    case .ipv4(let address):
                        hostString = address.debugDescription
                    case .ipv6(let address):
                        hostString = "[\(address.debugDescription)]"
                    case .name(let hostname, _):
                        hostString = hostname
                    @unknown default:
                        hostString = "localhost"
                    }
                    
                    // Construct URL
                    let urlString = "http://\(hostString):\(port)"
                    self.localDeviceURL = URL(string: urlString)
                    print("Discovered local ArgusAI at: \(urlString)")
                }
                connection.cancel()
                
            case .failed(let error):
                print("Connection failed: \(error)")
                connection.cancel()
                
            default:
                break
            }
        }
        
        connection.start(queue: .main)
    }
    
    deinit {
        stopDiscovery()
    }
}
