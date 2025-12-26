# ArgusAI iOS App - Setup Instructions

## Project Structure Created

All source files have been created in the `ios-app/ArgusAI/` directory:

- ✅ **Models**: Event.swift, Camera.swift, AuthToken.swift
- ✅ **Services**: APIClient.swift, AuthService.swift, KeychainService.swift, PushService.swift, DiscoveryService.swift
- ✅ **ViewModels**: PairingViewModel.swift, EventListViewModel.swift, EventDetailViewModel.swift
- ✅ **Views**: PairingView.swift, EventListView.swift, EventDetailView.swift, ErrorView.swift
- ✅ **App**: ArgusAIApp.swift
- ✅ **Tests**: PairingViewModelTests.swift, EventListViewModelTests.swift, APIClientTests.swift
- ✅ **Resources**: Info.plist

## Next Steps: Creating the Xcode Project

Since the source files are ready, you now need to create the Xcode project:

### 1. Create New Xcode Project

1. Open **Xcode**
2. Select **File > New > Project**
3. Choose **iOS > App**
4. Configure:
   - **Product Name**: `ArgusAI`
   - **Team**: Your Apple Developer Team
   - **Organization Identifier**: `com.argusai`
   - **Interface**: **SwiftUI**
   - **Language**: **Swift**
   - **Minimum Deployment**: **iOS 17.0**
   - **Storage**: Core Data ❌ (unchecked)
   - **Testing**: Include Tests ✅ (checked)

5. Save the project in the `ios-app/` directory (replace the generated files with the ones we created)

### 2. Add Source Files to Xcode

1. Delete the auto-generated files:
   - `ContentView.swift` (we have our own views)
   - `ArgusAIApp.swift` (we have our own)

2. Drag and drop the following folders into your Xcode project:
   - `ArgusAI/Models/`
   - `ArgusAI/Services/`
   - `ArgusAI/ViewModels/`
   - `ArgusAI/Views/`
   - `ArgusAI/ArgusAIApp.swift`
   - `ArgusAI/Resources/Info.plist`

3. For the Tests target, add:
   - `ArgusAITests/ViewModels/`
   - `ArgusAITests/Services/`

4. Make sure files are added to the correct targets:
   - Source files → **ArgusAI** target
   - Test files → **ArgusAITests** target

### 3. Configure Project Settings

#### A. Enable Capabilities

1. Select your project in the navigator
2. Select the **ArgusAI** target
3. Go to **Signing & Capabilities** tab
4. Click **+ Capability** and add:
   - **Push Notifications**
   - **Background Modes** (enable "Remote notifications")

#### B. Update Info.plist

The Info.plist in `Resources/` is already configured with:
- Bonjour services (`_argusai._tcp`)
- Local network usage description
- Background modes for push notifications

Make sure Xcode is using this Info.plist:
1. Go to **Build Settings**
2. Search for "Info.plist File"
3. Set to: `ArgusAI/Resources/Info.plist`

#### C. Set Minimum Deployment Target

1. In project settings, set **iOS Deployment Target** to **17.0**

### 4. Configure Push Notifications in Apple Developer Portal

1. Go to [Apple Developer Portal](https://developer.apple.com)
2. Navigate to **Certificates, Identifiers & Profiles**
3. Select your app's Bundle ID (com.argusai.ArgusAI)
4. Enable **Push Notifications** capability
5. Create an **Apple Push Notification service (APNs) Key**:
   - Go to **Keys** section
   - Create new key with APNs enabled
   - Download the `.p8` key file
   - Note the **Key ID** and **Team ID**
6. Configure your ArgusAI backend with these APNs credentials

### 5. Configure Cloud Relay (Optional)

If you want to use a cloud relay instead of local-only:

1. Open `ArgusAI/Services/DiscoveryService.swift`
2. Update line with `cloudRelayURL`:
   ```swift
   var cloudRelayURL: String = "https://your-argusai-instance.example.com"
   ```

### 6. Build and Run

#### For Simulator (Limited Functionality)
- Push notifications **will not work** in simulator
- Local discovery may have limitations
- Good for UI development and testing

#### For Physical Device (Recommended)
1. Connect your iPhone via USB
2. Select your device in Xcode toolbar
3. Click **Run** (Cmd+R)
4. First run will prompt for:
   - Local network permission (for Bonjour discovery)
   - Push notification permission

### 7. Testing the App

1. **Start your ArgusAI backend** (must be running for pairing)
2. **Get a pairing code**:
   - Open ArgusAI web dashboard
   - Go to Mobile Devices section
   - Generate a 6-digit pairing code
3. **Launch the app** on your device
4. **Enter the pairing code**
5. **View events** from your cameras

### 8. Running Tests

- Press **Cmd+U** to run all tests
- Or use **Test Navigator** (Cmd+6) to run specific tests

## Project Features

✅ **Device Pairing**: 6-digit code entry with validation
✅ **Authentication**: JWT tokens stored securely in Keychain
✅ **Token Refresh**: Automatic refresh before expiration
✅ **Local Discovery**: Bonjour discovery of local ArgusAI devices
✅ **Cloud Fallback**: Falls back to cloud relay if local not found
✅ **Event List**: Browse security events with thumbnails
✅ **Event Detail**: View full event information and images
✅ **Push Notifications**: Receive alerts for new events
✅ **Error Handling**: Comprehensive error states with retry
✅ **Modern iOS 17**: Uses @Observable, async/await, SwiftUI

## Troubleshooting

### Build Errors

**"Cannot find type 'XXX' in scope"**
- Make sure all files are added to the **ArgusAI** target
- Check that files are in the correct groups/folders

**"Info.plist not found"**
- Verify Info.plist path in Build Settings
- Should be: `ArgusAI/Resources/Info.plist`

### Runtime Issues

**"Local network permission not requested"**
- Ensure `NSLocalNetworkUsageDescription` is in Info.plist
- Ensure `NSBonjourServices` includes `_argusai._tcp`

**"Push notifications not working"**
- Push requires physical device (not simulator)
- Verify Push Notifications capability is enabled
- Check Apple Developer Portal configuration

**"Authentication fails"**
- Ensure backend is running and accessible
- Check that pairing code is valid (not expired)
- Verify network connectivity

### Network Issues

**"Cannot connect to local device"**
- Ensure iPhone and ArgusAI are on same WiFi network
- Check that Bonjour is enabled on backend
- Verify `_argusai._tcp` service is advertising

**"Cloud relay not working"**
- Update `cloudRelayURL` in DiscoveryService.swift
- Verify cloud relay is properly configured
- Check SSL/TLS certificate if using HTTPS

## Architecture Highlights

### iOS 17+ Features Used

- **@Observable macro**: For automatic UI updates without ObservableObject
- **Swift Concurrency**: async/await throughout, no completion handlers
- **Modern SwiftUI**: ContentUnavailableView, refreshable, task modifiers
- **Environment DI**: Clean dependency injection via environment
- **Swift Testing**: New Testing framework with @Test and @Suite macros

### Security

- **Keychain Storage**: Tokens stored securely in iOS Keychain
- **Token Rotation**: Refresh tokens are rotated on each use
- **Automatic Refresh**: Tokens refreshed 5 minutes before expiration
- **Retry Logic**: Automatic retry with token refresh on 401 errors

### Network Architecture

1. **Discovery Phase**: App searches for local device via Bonjour
2. **Local-First**: If found, all API calls go to local device
3. **Cloud Fallback**: If not found, uses cloud relay URL
4. **Dynamic Switching**: Can switch between local and cloud as needed

## Additional Resources

- **README.md**: Main project documentation
- **mobile-api.yaml**: Complete API specification
- **cloud-relay-design.md**: Architecture documentation

## Support

For issues or questions:
1. Check that all setup steps were completed
2. Verify backend is running and accessible
3. Review Xcode console for error messages
4. Test with a physical device for full functionality

---

**Created**: 2025-12-26  
**iOS Version**: 17.0+  
**Xcode Version**: 15.0+
