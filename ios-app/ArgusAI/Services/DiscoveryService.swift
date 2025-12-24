//
//  DiscoveryService.swift
//  ArgusAI
//
//  Bonjour service discovery for local network access.
//

import Foundation
import Network

@Observable
final class DiscoveryService {
    static let shared = DiscoveryService()

    /// The current base URL to use for API requests
    /// Prefers local discovery, falls back to cloud relay
    var currentBaseURL: String {
        if let local = localEndpoint, isLocalAvailable {
            return local
        }
        return cloudRelayURL
    }

    /// Whether local ArgusAI was discovered
    var isLocalAvailable = false

    /// The discovered local endpoint (e.g., "http://192.168.1.100:8000")
    var localEndpoint: String?

    /// Cloud relay URL (configure this during setup)
    var cloudRelayURL: String = "https://argusai.example.com"

    private var browser: NWBrowser?
    private var isSearching = false

    private init() {}

    // MARK: - Discovery

    func startDiscovery() {
        guard !isSearching else { return }
        isSearching = true

        // Browse for ArgusAI service on local network
        let parameters = NWParameters()
        parameters.includePeerToPeer = true

        let descriptor = NWBrowser.Descriptor.bonjour(type: "_argusai._tcp", domain: "local.")
        browser = NWBrowser(for: descriptor, using: parameters)

        browser?.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                print("Bonjour browser ready")
            case .failed(let error):
                print("Bonjour browser failed: \(error)")
                self?.isSearching = false
            case .cancelled:
                print("Bonjour browser cancelled")
                self?.isSearching = false
            default:
                break
            }
        }

        browser?.browseResultsChangedHandler = { [weak self] results, changes in
            self?.handleDiscoveryResults(results)
        }

        browser?.start(queue: .main)

        // Stop searching after 10 seconds if nothing found
        DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self] in
            if self?.localEndpoint == nil {
                self?.stopDiscovery()
            }
        }
    }

    func stopDiscovery() {
        browser?.cancel()
        browser = nil
        isSearching = false
    }

    func refreshDiscovery() {
        stopDiscovery()
        localEndpoint = nil
        isLocalAvailable = false
        startDiscovery()
    }

    private func handleDiscoveryResults(_ results: Set<NWBrowser.Result>) {
        for result in results {
            switch result.endpoint {
            case .service(let name, let type, let domain, _):
                print("Found service: \(name).\(type).\(domain)")
                resolveService(result)
            default:
                break
            }
        }
    }

    private func resolveService(_ result: NWBrowser.Result) {
        let connection = NWConnection(to: result.endpoint, using: .tcp)

        connection.stateUpdateHandler = { [weak self] state in
            switch state {
            case .ready:
                // Get the resolved IP address and port
                if let path = connection.currentPath,
                   let endpoint = path.remoteEndpoint {
                    self?.extractEndpoint(from: endpoint)
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

        // Timeout after 5 seconds
        DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
            if connection.state != .ready {
                connection.cancel()
            }
        }
    }

    private func extractEndpoint(from endpoint: NWEndpoint) {
        switch endpoint {
        case .hostPort(let host, let port):
            let hostString: String
            switch host {
            case .ipv4(let address):
                hostString = "\(address)"
            case .ipv6(let address):
                hostString = "[\(address)]"
            case .name(let name, _):
                hostString = name
            @unknown default:
                return
            }

            let url = "http://\(hostString):\(port)"
            print("Resolved ArgusAI at: \(url)")

            DispatchQueue.main.async { [weak self] in
                self?.localEndpoint = url
                self?.isLocalAvailable = true
                self?.stopDiscovery()
            }

        default:
            break
        }
    }

    // MARK: - Configuration

    func configureCloudRelay(url: String) {
        cloudRelayURL = url
    }
}
