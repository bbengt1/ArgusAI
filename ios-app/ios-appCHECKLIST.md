# ArgusAI iOS App - Setup Checklist

Use this checklist to ensure you've completed all setup steps correctly.

## ☐ Phase 1: Create Xcode Project

- [ ] Open Xcode
- [ ] File > New > Project
- [ ] Select **iOS > App**
- [ ] Product Name: **ArgusAI**
- [ ] Organization Identifier: **com.argusai**
- [ ] Interface: **SwiftUI**
- [ ] Language: **Swift**
- [ ] Minimum Deployment: **iOS 17.0**
- [ ] Include Tests: **Checked ✓**
- [ ] Save in **ios-app/** directory

## ☐ Phase 2: Add Source Files

- [ ] Delete auto-generated `ContentView.swift`
- [ ] Delete auto-generated `ArgusAIApp.swift`
- [ ] Add **ArgusAIApp.swift** to project root
- [ ] Create **Models** group and add:
  - [ ] Event.swift
  - [ ] Camera.swift
  - [ ] AuthToken.swift
- [ ] Create **Services** group and add:
  - [ ] APIClient.swift
  - [ ] AuthService.swift
  - [ ] KeychainService.swift
  - [ ] PushService.swift
  - [ ] DiscoveryService.swift
- [ ] Create **ViewModels** group and add:
  - [ ] PairingViewModel.swift
  - [ ] EventListViewModel.swift
  - [ ] EventDetailViewModel.swift
- [ ] Create **Views** group and add:
  - [ ] PairingView.swift
  - [ ] EventListView.swift
  - [ ] EventDetailView.swift
  - [ ] ErrorView.swift
- [ ] Create **Resources** group and add:
  - [ ] Info.plist

## ☐ Phase 3: Add Test Files

- [ ] In **ArgusAITests** target, create **ViewModels** group:
  - [ ] PairingViewModelTests.swift
  - [ ] EventListViewModelTests.swift
- [ ] In **ArgusAITests** target, create **Services** group:
  - [ ] APIClientTests.swift

## ☐ Phase 4: Configure Project Settings

### Build Settings
- [ ] Build Settings > Info.plist File: `ArgusAI/Resources/Info.plist`
- [ ] iOS Deployment Target: **17.0**

### Signing & Capabilities
- [ ] Select **ArgusAI** target
- [ ] Go to **Signing & Capabilities** tab
- [ ] Team: Select your Apple Developer Team
- [ ] Add **Push Notifications** capability
- [ ] Add **Background Modes** capability
  - [ ] Enable **Remote notifications**

### Info.plist Verification
- [ ] Verify `NSBonjourServices` contains `_argusai._tcp`
- [ ] Verify `NSLocalNetworkUsageDescription` is present
- [ ] Verify `UIBackgroundModes` contains `remote-notification`

## ☐ Phase 5: Apple Developer Portal Setup

- [ ] Go to [developer.apple.com](https://developer.apple.com)
- [ ] Navigate to **Certificates, Identifiers & Profiles**
- [ ] Find app identifier: **com.argusai.ArgusAI**
- [ ] Enable **Push Notifications** capability
- [ ] Create APNs Key:
  - [ ] Go to **Keys** section
  - [ ] Click **+** to create new key
  - [ ] Name: "ArgusAI APNs Key"
  - [ ] Enable **Apple Push Notifications service (APNs)**
  - [ ] Register and download `.p8` file
  - [ ] Note the **Key ID**
  - [ ] Note the **Team ID**
- [ ] Store credentials securely (needed for backend)

## ☐ Phase 6: Backend Configuration

- [ ] Configure ArgusAI backend with APNs credentials:
  - [ ] Key ID (from Apple Developer Portal)
  - [ ] Team ID (from Apple Developer Portal)
  - [ ] APNs Key file (`.p8` file)
- [ ] Ensure backend is running and accessible
- [ ] Verify backend Bonjour service is enabled (`_argusai._tcp`)
- [ ] Test pairing code generation in web dashboard

## ☐ Phase 7: Optional Configuration

### Cloud Relay URL (if using cloud)
- [ ] Open `ArgusAI/Services/DiscoveryService.swift`
- [ ] Update `cloudRelayURL` to your instance:
  ```swift
  var cloudRelayURL: String = "https://your-argusai.example.com"
  ```

### Custom Bundle Identifier (if needed)
- [ ] Update project settings > General > Bundle Identifier
- [ ] Update Apple Developer Portal app identifier
- [ ] Re-enable Push Notifications capability

## ☐ Phase 8: First Build

- [ ] Connect iPhone via USB (push requires physical device)
- [ ] Select your device in Xcode toolbar
- [ ] Press **Cmd+B** to build
- [ ] Fix any build errors (check console)
- [ ] Verify all files compile successfully

## ☐ Phase 9: Run Tests

- [ ] Press **Cmd+U** to run all tests
- [ ] Verify all tests pass:
  - [ ] PairingViewModelTests (6 tests)
  - [ ] EventListViewModelTests (4 tests)
  - [ ] APIClientTests (6 tests)
- [ ] Total: **16 tests should pass**

## ☐ Phase 10: First Run on Device

- [ ] Press **Cmd+R** to run on device
- [ ] Grant permissions when prompted:
  - [ ] Allow local network access
  - [ ] Allow push notifications
- [ ] Verify app launches successfully
- [ ] Check Xcode console for discovery logs

## ☐ Phase 11: Test Pairing

- [ ] Open ArgusAI web dashboard
- [ ] Navigate to Mobile Devices section
- [ ] Generate pairing code (6 digits)
- [ ] Enter code in iOS app
- [ ] Verify successful pairing
- [ ] Check that EventListView appears

## ☐ Phase 12: Test Event Viewing

- [ ] Trigger a test event (if possible)
- [ ] Pull to refresh in event list
- [ ] Verify events load
- [ ] Tap an event
- [ ] Verify event detail loads
- [ ] Verify thumbnail displays (if available)

## ☐ Phase 13: Test Push Notifications

- [ ] Ensure app is in background or closed
- [ ] Trigger an event from backend
- [ ] Verify push notification received
- [ ] Tap notification
- [ ] Verify app opens to correct event

## ☐ Phase 14: Test Local Discovery

- [ ] Ensure iPhone and ArgusAI are on same WiFi network
- [ ] Launch app
- [ ] Check Xcode console for:
  ```
  Bonjour browser ready
  Discovered local ArgusAI at: http://x.x.x.x:xxxx
  ```
- [ ] Verify API calls use local URL

## ☐ Phase 15: Test Cloud Fallback

- [ ] Disconnect iPhone from local WiFi (use cellular)
- [ ] Launch app
- [ ] Verify app falls back to cloud relay URL
- [ ] Verify API calls still work

## ☐ Phase 16: Additional Testing

- [ ] Test sign out functionality
- [ ] Test re-authentication after sign out
- [ ] Test app launch when already authenticated
- [ ] Test network error handling (airplane mode)
- [ ] Test token refresh (wait >5 min, use app)
- [ ] Test pull-to-refresh on event list
- [ ] Test pagination (if >20 events)

## ☐ Phase 17: Code Review

- [ ] Review all files for TODOs or placeholders
- [ ] Verify all imports are necessary
- [ ] Check for any compiler warnings
- [ ] Verify code follows Swift style guidelines
- [ ] Ensure all functions have appropriate error handling

## ☐ Phase 18: Documentation Review

- [ ] Read through README.md
- [ ] Read through SETUP.md
- [ ] Read through FILE_STRUCTURE.md
- [ ] Verify all documentation is accurate
- [ ] Update any outdated information

## ☐ Phase 19: Performance Testing

- [ ] Test on older devices (if available)
- [ ] Monitor memory usage in Xcode Instruments
- [ ] Check for memory leaks
- [ ] Verify smooth scrolling in event list
- [ ] Test with large number of events (100+)

## ☐ Phase 20: Final Verification

- [ ] All 16 unit tests pass
- [ ] App builds without warnings
- [ ] App runs on physical device
- [ ] Pairing works correctly
- [ ] Events load and display
- [ ] Push notifications work
- [ ] Local discovery works
- [ ] Cloud fallback works
- [ ] Error states display properly
- [ ] Pull-to-refresh works
- [ ] Navigation works correctly

## Common Issues & Solutions

### Build Errors

**"Cannot find type in scope"**
- ✓ Verify file is added to correct target (ArgusAI, not ArgusAITests)
- ✓ Check that file is in Compile Sources in Build Phases

**"Info.plist not found"**
- ✓ Verify path in Build Settings: `ArgusAI/Resources/Info.plist`
- ✓ Ensure Info.plist is added to project (not just filesystem)

### Runtime Issues

**"Local network permission not requested"**
- ✓ Add `NSLocalNetworkUsageDescription` to Info.plist
- ✓ Add `NSBonjourServices` array with `_argusai._tcp`

**"Push notifications not working"**
- ✓ Must use physical device (not simulator)
- ✓ Verify Push Notifications capability enabled
- ✓ Check Apple Developer Portal configuration
- ✓ Verify backend has correct APNs credentials

**"Cannot discover local device"**
- ✓ Ensure same WiFi network
- ✓ Verify backend Bonjour is running
- ✓ Check firewall settings on backend
- ✓ Verify service name is `_argusai._tcp`

### Authentication Issues

**"Invalid pairing code"**
- ✓ Ensure code hasn't expired (typically 15 min)
- ✓ Verify backend is accessible
- ✓ Check network connectivity
- ✓ Verify API endpoint path is correct

**"Token refresh failed"**
- ✓ Verify backend token refresh endpoint
- ✓ Check that refresh token hasn't expired (30 days)
- ✓ Clear keychain and re-pair if needed

## Next Steps After Setup

1. **Customize**: Update icons, colors, branding
2. **Enhance**: Add video playback, settings screen
3. **Optimize**: Implement caching, offline mode
4. **Expand**: Add iPad layouts, widgets, watch app
5. **Polish**: Animations, haptics, accessibility
6. **Prepare**: App Store listing, screenshots, metadata

## Resources

- 📖 **README.md**: Architecture and overview
- 📖 **SETUP.md**: Detailed setup instructions
- 📖 **FILE_STRUCTURE.md**: Code organization
- 🔗 **mobile-api.yaml**: API specification
- 🔗 **cloud-relay-design.md**: Architecture docs

---

**Setup Complete!** ✅

Once all items are checked, you have a fully functional ArgusAI iOS app ready for development and testing.
