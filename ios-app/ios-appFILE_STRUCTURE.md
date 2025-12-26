# ArgusAI iOS App - File Structure

## Directory Layout

```
ios-app/
├── ArgusAI/
│   ├── ArgusAIApp.swift                    # ✅ Main app entry point with AppDelegate
│   │
│   ├── Models/
│   │   ├── Event.swift                     # ✅ Event models (Summary, Detail, Response)
│   │   ├── Camera.swift                    # ✅ Camera model
│   │   └── AuthToken.swift                 # ✅ Auth token models (Pairing, Refresh)
│   │
│   ├── Services/
│   │   ├── APIClient.swift                 # ✅ HTTP client with retry & token refresh
│   │   ├── AuthService.swift               # ✅ Authentication & pairing logic
│   │   ├── KeychainService.swift           # ✅ Secure credential storage
│   │   ├── PushService.swift               # ✅ APNS push notification handling
│   │   └── DiscoveryService.swift          # ✅ Bonjour local discovery
│   │
│   ├── ViewModels/
│   │   ├── PairingViewModel.swift          # ✅ Pairing screen logic
│   │   ├── EventListViewModel.swift        # ✅ Event list logic
│   │   └── EventDetailViewModel.swift      # ✅ Event detail logic
│   │
│   ├── Views/
│   │   ├── PairingView.swift               # ✅ Device pairing screen
│   │   ├── EventListView.swift             # ✅ Event list with thumbnails
│   │   ├── EventDetailView.swift           # ✅ Event detail screen
│   │   └── ErrorView.swift                 # ✅ Error state display
│   │
│   └── Resources/
│       └── Info.plist                      # ✅ App configuration
│
├── ArgusAITests/
│   ├── ViewModels/
│   │   ├── PairingViewModelTests.swift     # ✅ Tests for pairing logic
│   │   └── EventListViewModelTests.swift   # ✅ Tests for event list
│   │
│   └── Services/
│       └── APIClientTests.swift            # ✅ Tests for JSON decoding
│
├── README.md                                # 📖 Main documentation
└── SETUP.md                                 # 📖 Setup instructions (this file)
```

## File Descriptions

### Core App
- **ArgusAIApp.swift**: SwiftUI app entry point, sets up services and environment

### Models (Data Structures)
- **Event.swift**: `EventSummary`, `EventDetail`, `DetectionType`, `EventsResponse`
- **Camera.swift**: `Camera`, `CamerasResponse`
- **AuthToken.swift**: `AuthToken`, `PairingRequest`, `PairingResponse`, `RefreshTokenRequest`, `RefreshTokenResponse`

### Services (Business Logic)
- **APIClient.swift**: HTTP client with automatic token refresh, retry logic, and all API endpoints
- **AuthService.swift**: Handles pairing, token management, sign in/out
- **KeychainService.swift**: Secure storage for tokens and device ID
- **PushService.swift**: Push notification registration and handling
- **DiscoveryService.swift**: Bonjour discovery for local ArgusAI devices

### ViewModels (Presentation Logic)
- **PairingViewModel.swift**: Code validation, formatting, pairing flow
- **EventListViewModel.swift**: Event loading, pagination, camera name lookup
- **EventDetailViewModel.swift**: Event detail loading, image loading, formatting

### Views (UI)
- **PairingView.swift**: 6-digit code entry screen
- **EventListView.swift**: Scrollable list of events with pull-to-refresh
- **EventDetailView.swift**: Full event details with image
- **ErrorView.swift**: Reusable error display with retry button

### Tests
- **PairingViewModelTests.swift**: Tests code validation, filtering, formatting
- **EventListViewModelTests.swift**: Tests camera lookup, detection types
- **APIClientTests.swift**: Tests JSON decoding for all models

### Resources
- **Info.plist**: Bonjour services, local network permission, background modes

## Key Technologies Used

### iOS 17+ Features
- ✅ `@Observable` macro (no more ObservableObject boilerplate)
- ✅ `@Environment` for dependency injection
- ✅ `async/await` for all network operations
- ✅ `ContentUnavailableView` for empty states
- ✅ Swift Testing framework with `@Test` and `@Suite`

### Frameworks
- ✅ **SwiftUI**: Modern declarative UI
- ✅ **Security**: Keychain for secure storage
- ✅ **Network**: Bonjour discovery with NWBrowser
- ✅ **UserNotifications**: Push notification handling
- ✅ **Foundation**: URLSession, JSONEncoder/Decoder

### Patterns
- ✅ **MVVM**: Models, Views, ViewModels
- ✅ **Service Layer**: Reusable business logic
- ✅ **Dependency Injection**: Via SwiftUI Environment
- ✅ **Error Handling**: Comprehensive with retry logic

## Lines of Code

Approximate LOC per file:

| File | Lines | Purpose |
|------|-------|---------|
| ArgusAIApp.swift | 120 | App setup & delegate |
| Event.swift | 90 | Event models |
| Camera.swift | 35 | Camera models |
| AuthToken.swift | 110 | Auth models |
| APIClient.swift | 175 | HTTP client |
| AuthService.swift | 180 | Authentication |
| KeychainService.swift | 120 | Keychain wrapper |
| PushService.swift | 80 | Push handling |
| DiscoveryService.swift | 145 | Bonjour discovery |
| PairingViewModel.swift | 65 | Pairing logic |
| EventListViewModel.swift | 75 | Event list logic |
| EventDetailViewModel.swift | 75 | Event detail logic |
| PairingView.swift | 105 | Pairing UI |
| EventListView.swift | 135 | Event list UI |
| EventDetailView.swift | 160 | Event detail UI |
| ErrorView.swift | 50 | Error UI |
| Tests | 210 | All tests |
| **Total** | **~1,930** | Complete app |

## Next Steps

1. **Read SETUP.md** for detailed Xcode project creation instructions
2. **Create Xcode project** with the settings specified
3. **Add all source files** to the appropriate targets
4. **Configure capabilities** (Push Notifications, Background Modes)
5. **Build and run** on a physical device

## Quick Start Commands

Once project is created in Xcode:

```bash
# Build
Cmd+B

# Run on device
Cmd+R

# Run tests
Cmd+U

# Clean build folder
Cmd+Shift+K
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      ArgusAIApp                         │
│  (App Entry, Service Setup, Environment Injection)      │
└─────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            │                               │
┌───────────▼──────────┐      ┌────────────▼─────────────┐
│   PairingView        │      │   EventListView          │
│   (Not Authenticated)│      │   (Authenticated)        │
└───────────┬──────────┘      └────────────┬─────────────┘
            │                               │
┌───────────▼──────────┐      ┌────────────▼─────────────┐
│  PairingViewModel    │      │  EventListViewModel      │
└───────────┬──────────┘      └────────────┬─────────────┘
            │                               │
            └───────────────┬───────────────┘
                            │
            ┌───────────────▼────────────────┐
            │         Services               │
            │  ┌─────────────────────────┐   │
            │  │   AuthService           │   │
            │  │   DiscoveryService      │   │
            │  │   APIClient             │   │
            │  │   PushService           │   │
            │  │   KeychainService       │   │
            │  └─────────────────────────┘   │
            └────────────────────────────────┘
                            │
            ┌───────────────▼────────────────┐
            │         Models                 │
            │  ┌─────────────────────────┐   │
            │  │   Event, Camera         │   │
            │  │   AuthToken             │   │
            │  └─────────────────────────┘   │
            └────────────────────────────────┘
```

## Support & Documentation

- **SETUP.md**: Detailed setup instructions
- **README.md**: Project overview and architecture
- **Code Comments**: Inline documentation in source files
- **Tests**: Examples of usage patterns

---

**All files created and ready for Xcode project setup!** ✅
