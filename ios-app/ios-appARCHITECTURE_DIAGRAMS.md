# ArgusAI iOS App - Architecture Diagrams

## Application Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      App Launch                             │
│                    (ArgusAIApp.swift)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─ Initialize Services
                       │  ├─ KeychainService
                       │  ├─ DiscoveryService
                       │  ├─ AuthService
                       │  └─ PushService
                       │
                       ├─ Start Local Discovery (Bonjour)
                       ├─ Request Push Permission
                       │
                       ├─ Check Authentication
                       │
          ┌────────────┴────────────┐
          │                         │
    [Not Authenticated]      [Authenticated]
          │                         │
          ▼                         ▼
   ┌─────────────┐          ┌──────────────┐
   │ PairingView │          │ EventListView│
   └─────────────┘          └──────────────┘
          │                         │
          │ Enter 6-digit code      │ Load events
          │                         │
          ▼                         ▼
   ┌─────────────────┐      ┌──────────────────┐
   │ AuthService     │      │ EventListViewModel│
   │ .verifyPairing()│      │ .loadEvents()     │
   └─────────────────┘      └──────────────────┘
          │                         │
          │ Success                 │ Tap event
          │                         │
          └────────►[Authenticated] │
                            │       │
                            │       ▼
                            │  ┌────────────────┐
                            │  │EventDetailView │
                            │  └────────────────┘
                            │       │
                            │       ▼
                            │  ┌────────────────────┐
                            │  │EventDetailViewModel│
                            │  │.loadEvent()        │
                            │  └────────────────────┘
                            │
                            ▼
                       (Continue using app)
```

## Service Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Views                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PairingView  │  │EventListView │  │EventDetailView│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────┬───────────────┬───────────────────┬───────────────┘
          │               │                   │
          │ @Environment  │                   │
          │               │                   │
┌─────────▼───────────────▼───────────────────▼───────────────┐
│                     ViewModels                              │
│  ┌────────────────┐ ┌──────────────────┐ ┌────────────────┐│
│  │PairingViewModel│ │EventListViewModel│ │EventDetailView-││
│  │                │ │                  │ │Model           ││
│  └────────────────┘ └──────────────────┘ └────────────────┘│
└─────────┬───────────────┬───────────────────┬───────────────┘
          │               │                   │
          │ Call methods  │                   │
          │               │                   │
┌─────────▼───────────────▼───────────────────▼───────────────┐
│                       Services                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              AuthService                             │   │
│  │  - verifyPairingCode()                              │   │
│  │  - refreshAccessToken()                             │   │
│  │  - signOut()                                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                             │                               │
│  ┌──────────────────────────┼────────────────────────────┐  │
│  │              APIClient   │                            │  │
│  │  - fetchEvents()         │                            │  │
│  │  - fetchEventDetail()    │                            │  │
│  │  - fetchCameras()        │                            │  │
│  │  - registerPushToken()   │                            │  │
│  └──────────────────────────┼────────────────────────────┘  │
│                             │                               │
│  ┌──────────────────────────┼────────────────────────────┐  │
│  │        DiscoveryService  │                            │  │
│  │  - startDiscovery()      │                            │  │
│  │  - baseURL (local/cloud) │                            │  │
│  └──────────────────────────┼────────────────────────────┘  │
│                             │                               │
│  ┌──────────────────────────┼────────────────────────────┐  │
│  │        KeychainService   │                            │  │
│  │  - save(token)           │                            │  │
│  │  - load(token)           │                            │  │
│  └──────────────────────────┼────────────────────────────┘  │
│                             │                               │
│  ┌──────────────────────────┼────────────────────────────┐  │
│  │         PushService      │                            │  │
│  │  - requestAuthorization()│                            │  │
│  │  - handleNotification()  │                            │  │
│  └──────────────────────────┴────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Models     │  │   Keychain   │  │   Network    │      │
│  │ - Event      │  │ - Tokens     │  │ - URLSession │      │
│  │ - Camera     │  │ - Device ID  │  │ - Bonjour    │      │
│  │ - AuthToken  │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Authentication Flow

```
┌────────────┐
│   User     │
│  Opens App │
└─────┬──────┘
      │
      ▼
┌────────────────────┐
│  Check Keychain    │
│  for stored tokens │
└─────┬──────────────┘
      │
      ├─ Found Valid Tokens ─────────────┐
      │                                   │
      ├─ No Tokens or Expired            │
      │                                   │
      ▼                                   ▼
┌──────────────┐                  ┌──────────────┐
│ Show Pairing │                  │ Show Event   │
│    View      │                  │  List View   │
└──────┬───────┘                  └──────────────┘
       │
       │ User enters 6-digit code
       │
       ▼
┌────────────────────────────────────────┐
│ POST /api/v1/mobile/auth/verify        │
│ Body: {                                │
│   code: "123456",                      │
│   device_id: "uuid",                   │
│   device_name: "John's iPhone"         │
│ }                                      │
└──────┬─────────────────────────────────┘
       │
       ├─ Success (200) ──────────────────┐
       │                                   │
       ├─ Error (401/400) ────────────────┤
       │                                   │
       ▼                                   │
┌──────────────────┐                      │
│ Show Error       │                      │
│ "Invalid Code"   │                      │
└──────────────────┘                      │
                                          │
       ┌──────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Response: {                              │
│   access_token: "jwt...",                │
│   refresh_token: "jwt...",               │
│   expires_in: 3600,                      │
│   token_type: "Bearer"                   │
│ }                                        │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│ Store in Keychain:                       │
│  - access_token                          │
│  - refresh_token                         │
│  - expiration_date                       │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────┐
│ Navigate to      │
│ Event List View  │
└──────────────────┘
```

## API Request Flow with Token Refresh

```
┌────────────┐
│   View     │
│ calls API  │
└─────┬──────┘
      │
      ▼
┌────────────────────┐
│  ViewModel calls   │
│  APIClient method  │
└─────┬──────────────┘
      │
      ▼
┌─────────────────────────────────┐
│  APIClient checks token expiry  │
│  (expires_in < 300 seconds)     │
└─────┬───────────────────────────┘
      │
      ├─ Token Valid ───────────────────┐
      │                                  │
      ├─ Token Expiring Soon            │
      │                                  │
      ▼                                  │
┌────────────────────────────────────┐  │
│ AuthService.refreshAccessToken()   │  │
│                                    │  │
│ POST /api/v1/mobile/auth/refresh   │  │
│ Body: {                            │  │
│   refresh_token: "current_token"   │  │
│ }                                  │  │
└────────┬───────────────────────────┘  │
         │                               │
         ├─ Success ────────────────────┐│
         │                              ││
         ├─ Failed (401) ───────────┐   ││
         │                          │   ││
         ▼                          │   ││
    ┌─────────────────┐             │   ││
    │ Store new tokens│             │   ││
    │ in Keychain     │             │   ││
    └─────────┬───────┘             │   ││
              │                     │   ││
              │◄────────────────────┘   ││
              │                         ││
              │◄────────────────────────┘│
              │                          │
              ▼                          │
┌─────────────────────────────────────┐  │
│ Make API request with Authorization │  │
│ Header: "Bearer <access_token>"     │  │
└─────────┬───────────────────────────┘  │
          │                              │
          ├─ 200 OK ─────────────────────┤
          │                              │
          ├─ 401 Unauthorized            │
          │   (retry once with refresh)  │
          │                              │
          ├─ 404/500 Other Error         │
          │                              │
          ▼                              │
    ┌─────────────┐                      │
    │   Return    │                      │
    │   Result    │                      │
    └─────────────┘                      │
                                         │
         ┌───────────────────────────────┘
         │ Refresh failed
         ▼
    ┌─────────────┐
    │  Sign Out   │
    │  Clear      │
    │  Keychain   │
    └─────────────┘
         │
         ▼
    ┌─────────────┐
    │  Show       │
    │ Pairing     │
    │  View       │
    └─────────────┘
```

## Local Discovery Flow

```
┌──────────────┐
│  App Launch  │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────┐
│ DiscoveryService.startDiscovery()  │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ NWBrowser searches for:            │
│ Service: _argusai._tcp.local       │
│ Include Peer-to-Peer: true         │
└──────┬─────────────────────────────┘
       │
       ├─ Device Found ─────────────┐
       │                            │
       ├─ No Device Found           │
       │                            │
       ▼                            │
┌──────────────────┐                │
│ Use Cloud Relay  │                │
│ cloudRelayURL    │                │
└──────────────────┘                │
                                    │
       ┌────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ Resolve endpoint to IP:Port        │
│ Example: 192.168.1.100:8080        │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ Set localDeviceURL                 │
│ http://192.168.1.100:8080          │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ All API calls use:                 │
│ discoveryService.baseURL           │
│ (returns localDeviceURL if found,  │
│  otherwise cloudRelayURL)          │
└────────────────────────────────────┘
       │
       ▼
   Benefits:
   ✓ Low latency (local network)
   ✓ Works without internet
   ✓ More secure (no cloud)
   ✓ Automatic fallback
```

## Push Notification Flow

```
┌──────────────┐
│  App Launch  │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────┐
│ PushService.requestAuthorization() │
└──────┬─────────────────────────────┘
       │
       ├─ User Grants Permission ────┐
       │                             │
       ├─ User Denies ────────────┐  │
       │                          │  │
       ▼                          │  │
   (No push)                      │  │
                                  │  │
       ┌──────────────────────────┘  │
       │                             │
       ▼                             │
┌────────────────────────────┐       │
│ registerForRemoteNotifications()   │
└──────┬─────────────────────┘       │
       │                             │
       ▼                             │
┌────────────────────────────────────┤
│ iOS provides device token          │
│ (64-character hex string)          │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ PushService.didRegisterForRemote-  │
│   NotificationsWithDeviceToken()   │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ POST /api/v1/mobile/push/register  │
│ Body: {                            │
│   push_token: "hex_token...",      │
│   platform: "ios"                  │
│ }                                  │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ Backend stores token for device    │
└────────────────────────────────────┘

─────────── When Event Occurs ──────────

┌────────────────────────────────────┐
│ ArgusAI detects event (motion,     │
│ person, etc.)                      │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ Backend sends push to APNs         │
│ Payload: {                         │
│   aps: {                           │
│     alert: {                       │
│       title: "Motion Detected",    │
│       body: "Front Door Camera"    │
│     }                              │
│   },                               │
│   event_id: "evt_123"              │
│ }                                  │
└──────┬─────────────────────────────┘
       │
       ▼
┌────────────────────────────────────┐
│ APNs delivers to device            │
└──────┬─────────────────────────────┘
       │
       ├─ App in Foreground ──────────┐
       │                              │
       ├─ App in Background ──────────┤
       │                              │
       ├─ App Closed ─────────────────┤
       │                              │
       ▼                              │
┌──────────────────────────┐          │
│ System shows notification│          │
│ on Lock Screen / Banner  │          │
└──────┬───────────────────┘          │
       │                              │
       │ User taps notification       │
       │                              │
       ▼                              │
┌────────────────────────────────────┐│
│ App opens/resumes                  ││
└──────┬─────────────────────────────┘│
       │                              │
       ▼                              │
┌────────────────────────────────────┐│
│ PushService.handleNotification()   ││
│ Extracts event_id from payload     ││
└──────┬─────────────────────────────┘│
       │                              │
       ▼                              │
┌────────────────────────────────────┐│
│ Navigate to EventDetailView        ││
│ with event_id                      ││
└────────────────────────────────────┘│
                                      │
       ┌──────────────────────────────┘
       │
       ▼
┌────────────────────────────┐
│ Show event detail          │
│ Load thumbnail, AI         │
│ description, etc.          │
└────────────────────────────┘
```

## Data Flow: Viewing Events

```
┌──────────────┐
│ EventListView│
│  appears     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│ EventListViewModel.loadEvents()  │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ APIClient.fetchEvents()          │
│ APIClient.fetchCameras()         │
│ (async parallel)                 │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ GET /api/v1/mobile/events        │
│ ?page=1&page_size=20             │
│                                  │
│ GET /api/v1/mobile/cameras       │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ Response: EventsResponse         │
│ {                                │
│   events: [...],                 │
│   total: 42,                     │
│   page: 1,                       │
│   page_size: 20                  │
│ }                                │
│                                  │
│ Response: CamerasResponse        │
│ {                                │
│   cameras: [...]                 │
│ }                                │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ ViewModel updates properties:    │
│  - events = [...]               │
│  - cameras = [...]              │
│  - isLoading = false            │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ SwiftUI automatically updates UI │
│ (@Observable triggers refresh)   │
└──────┬───────────────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ List displays:                   │
│  - Event thumbnails              │
│  - Detection type icons          │
│  - AI descriptions               │
│  - Camera names                  │
│  - Timestamps                    │
└──────┬───────────────────────────┘
       │
       │ User taps event
       │
       ▼
┌──────────────────────────────────┐
│ Navigate to EventDetailView      │
│ Pass eventId                     │
└──────────────────────────────────┘
```

## Error Handling

```
┌────────────────┐
│  API Request   │
└────────┬───────┘
         │
         ▼
    Try to execute
         │
         ├─ Network Error ──────────┐
         │                          │
         ├─ 401 Unauthorized ───────┤
         │                          │
         ├─ 404 Not Found ──────────┤
         │                          │
         ├─ 500 Server Error ───────┤
         │                          │
         ├─ Decode Error ───────────┤
         │                          │
         ▼                          │
    [Success Path]                  │
                                    │
       ┌────────────────────────────┘
       │
       ▼
┌──────────────────┐
│ Throw APIError   │
│ with description │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│ Catch in ViewModel       │
│ errorMessage = error     │
│   .localizedDescription  │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ SwiftUI shows ErrorView  │
│ with message and retry   │
└────────┬─────────────────┘
         │
         │ User taps retry
         │
         ▼
┌──────────────────────────┐
│ Call ViewModel method    │
│ again (retry)            │
└──────────────────────────┘
```

---

These diagrams show the complete architecture and data flow of the ArgusAI iOS app. Use them as reference when implementing features or debugging issues.
