# 🚀 Quick Start Guide

**Get the ArgusAI iOS app running in under 30 minutes!**

## TL;DR

1. Create Xcode project (iOS App, SwiftUI, iOS 17+)
2. Add all source files from `ArgusAI/` and `ArgusAITests/`
3. Enable Push Notifications and Background Modes capabilities
4. Set up APNs key in Apple Developer Portal
5. Build and run on iPhone
6. Pair with 6-digit code from web dashboard

## Step-by-Step (30 Minutes)

### 1. Create Xcode Project (5 min)

```
Xcode > File > New > Project
├── Template: iOS > App
├── Product Name: ArgusAI
├── Team: Your Developer Team
├── Organization ID: com.argusai
├── Interface: SwiftUI
├── Language: Swift
├── Minimum Deployment: iOS 17.0
└── Include Tests: ✓
```

### 2. Add Source Files (10 min)

Delete generated files:
- ❌ `ContentView.swift`
- ❌ `ArgusAIApp.swift`

Add these folders (drag & drop into Xcode):
- ✅ `ArgusAI/ArgusAIApp.swift`
- ✅ `ArgusAI/Models/` (3 files)
- ✅ `ArgusAI/Services/` (5 files)
- ✅ `ArgusAI/ViewModels/` (3 files)
- ✅ `ArgusAI/Views/` (4 files)
- ✅ `ArgusAI/Resources/Info.plist`

Add test files:
- ✅ `ArgusAITests/ViewModels/` (2 files)
- ✅ `ArgusAITests/Services/` (1 file)

### 3. Configure Project (5 min)

**Build Settings:**
- Info.plist File: `ArgusAI/Resources/Info.plist`
- iOS Deployment Target: `17.0`

**Signing & Capabilities:**
- Team: Select your team
- Add capability: **Push Notifications**
- Add capability: **Background Modes**
  - Enable: **Remote notifications**

### 4. Apple Developer Setup (5 min)

Go to [developer.apple.com](https://developer.apple.com):
1. Certificates, Identifiers & Profiles
2. Keys > **+** (Create new key)
3. Name: "ArgusAI APNs"
4. Enable: **Apple Push Notifications service (APNs)**
5. Register and download `.p8` file
6. **Save**: Key ID, Team ID, and `.p8` file

### 5. Test Build (2 min)

```bash
# In Xcode:
Cmd+B          # Build (should succeed)
Cmd+U          # Run tests (16 should pass)
```

### 6. Run on Device (3 min)

1. Connect iPhone via USB
2. Select device in Xcode
3. **Cmd+R** to run
4. Grant permissions:
   - ✅ Allow local network access
   - ✅ Allow push notifications

### 7. First Pairing (2 min)

1. Start ArgusAI backend
2. Open web dashboard
3. Mobile Devices > Generate Code
4. Enter 6-digit code in app
5. See events list ✅

## File Checklist

Your project should look like:

```
ArgusAI/
├── ArgusAIApp.swift ✓
├── Models/
│   ├── Event.swift ✓
│   ├── Camera.swift ✓
│   └── AuthToken.swift ✓
├── Services/
│   ├── APIClient.swift ✓
│   ├── AuthService.swift ✓
│   ├── KeychainService.swift ✓
│   ├── PushService.swift ✓
│   └── DiscoveryService.swift ✓
├── ViewModels/
│   ├── PairingViewModel.swift ✓
│   ├── EventListViewModel.swift ✓
│   └── EventDetailViewModel.swift ✓
├── Views/
│   ├── PairingView.swift ✓
│   ├── EventListView.swift ✓
│   ├── EventDetailView.swift ✓
│   └── ErrorView.swift ✓
└── Resources/
    └── Info.plist ✓

ArgusAITests/
├── ViewModels/
│   ├── PairingViewModelTests.swift ✓
│   └── EventListViewModelTests.swift ✓
└── Services/
    └── APIClientTests.swift ✓
```

**Total: 19 source files + 3 test files + 1 config = 23 files**

## Common Quick Fixes

### Build Fails

```
Error: Cannot find type 'XXX' in scope
Fix: Verify file is added to ArgusAI target (not just project)
How: Select file > File Inspector > Target Membership > ArgusAI ✓
```

```
Error: Info.plist not found
Fix: Set path in Build Settings
How: Build Settings > Search "Info.plist" > Set to "ArgusAI/Resources/Info.plist"
```

### Runtime Issues

```
Issue: App doesn't request local network permission
Fix: Verify Info.plist has NSLocalNetworkUsageDescription
Check: ArgusAI/Resources/Info.plist line 10-12
```

```
Issue: Push notifications don't work
Fix: Must use physical device (simulator doesn't support push)
```

```
Issue: Can't discover local device
Fix: Ensure iPhone and ArgusAI on same WiFi network
```

## Verification Tests

Run these to confirm everything works:

### Build Tests
```
✓ Cmd+B builds without errors
✓ Cmd+U runs 16 tests, all pass
✓ No compiler warnings
```

### Runtime Tests
```
✓ App launches on device
✓ Pairing screen appears
✓ Can enter 6-digit code
✓ Successful pairing shows event list
✓ Can view event details
✓ Pull-to-refresh works
✓ Sign out returns to pairing
```

### Permission Tests
```
✓ Local network permission requested
✓ Push notification permission requested
✓ Both permissions granted
```

## Next Steps

### Customize
1. Update `cloudRelayURL` in `DiscoveryService.swift`
2. Configure backend with APNs credentials
3. Test push notifications

### Enhance
1. Add app icon and launch screen
2. Customize colors and branding
3. Add video playback

### Deploy
1. Create App Store listing
2. Add screenshots
3. Submit for review

## Need Help?

📖 **Detailed Guide**: Read `SETUP.md`  
📋 **Full Checklist**: See `CHECKLIST.md`  
🏗️ **Architecture**: Read `FILE_STRUCTURE.md`  
📊 **Overview**: See `PROJECT_SUMMARY.md`  

## Troubleshooting Decision Tree

```
Can't build?
├─> File not found → Check target membership
├─> Type not found → Add missing file
└─> Info.plist → Check Build Settings path

Builds but crashes?
├─> Permission denied → Check Info.plist
├─> Network error → Check backend running
└─> Auth error → Verify pairing code

Works but no push?
├─> Simulator → Use physical device
├─> No prompt → Enable in Settings
└─> Not receiving → Check backend APNs setup

Can't discover local device?
├─> Different network → Use same WiFi
├─> Bonjour off → Enable on backend
└─> Firewall → Check network settings
```

## Success! 🎉

You should now have:
- ✅ Working iOS app
- ✅ Successful device pairing
- ✅ Loading events from backend
- ✅ Push notifications configured
- ✅ Local discovery working

## Resources

- **README.md**: Original project specification
- **SETUP.md**: Detailed setup instructions  
- **CHECKLIST.md**: Complete setup checklist
- **FILE_STRUCTURE.md**: Code organization guide
- **PROJECT_SUMMARY.md**: Project overview

---

**Time to First Run: ~30 minutes** ⏱️  
**Lines of Code: ~2,140** 📝  
**Test Coverage: 16 tests** ✅  
**iOS Version: 17.0+** 📱  

Happy coding! 🚀
