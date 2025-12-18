# HomeKit Troubleshooting Guide

This guide helps resolve common HomeKit discovery and pairing issues with ArgusAI.

## Quick Diagnostics

ArgusAI includes a built-in connectivity test accessible from **Settings > HomeKit > Diagnostics > Test Discovery**. This test checks:

- **mDNS Visibility**: Whether the HomeKit bridge is discoverable via Bonjour/Avahi
- **Port Accessibility**: Whether the HAP server port (default 51826) is reachable
- **Firewall Issues**: Detects common network configuration problems
- **Troubleshooting Hints**: Provides specific recommendations based on test results

## Common Issues

### 1. Bridge Not Appearing in Apple Home App

**Symptoms:**
- HomeKit shows as "Running" in ArgusAI but doesn't appear in Home app
- "Add Accessory" scan finds nothing

**Causes & Solutions:**

#### mDNS/Bonjour Not Working

The Home app uses mDNS (Bonjour on macOS/iOS, Avahi on Linux) to discover accessories.

**Linux (Ubuntu/Debian):**
```bash
# Install Avahi
sudo apt install avahi-daemon

# Check if Avahi is running
systemctl status avahi-daemon

# Start if not running
sudo systemctl enable --now avahi-daemon
```

**Docker:**
If running ArgusAI in Docker, mDNS requires host network mode:
```yaml
services:
  argusai:
    network_mode: host
```

Or explicitly expose mDNS multicast:
```yaml
services:
  argusai:
    ports:
      - "51826:51826"
    # mDNS multicast must be allowed through host
```

#### Firewall Blocking mDNS

mDNS uses UDP multicast on port 5353 (address 224.0.0.251).

**Linux (UFW):**
```bash
# Allow mDNS
sudo ufw allow 5353/udp
```

**Linux (firewalld):**
```bash
# Allow mDNS
sudo firewall-cmd --permanent --add-service=mdns
sudo firewall-cmd --reload
```

**macOS:**
mDNS (Bonjour) is typically allowed by default. Check System Preferences > Security & Privacy > Firewall if issues persist.

### 2. "Unable to Add Accessory" After Scanning Code

**Symptoms:**
- Bridge appears in Home app
- Pairing code is entered or QR scanned
- Pairing fails with "Unable to Add Accessory"

**Causes & Solutions:**

#### HAP Port Blocked

The HAP server port (default 51826) must be accessible.

```bash
# Check if port is open and listening
netstat -tlnp | grep 51826
# or
ss -tlnp | grep 51826
```

**Open the port:**
```bash
# UFW
sudo ufw allow 51826/tcp

# firewalld
sudo firewall-cmd --permanent --add-port=51826/tcp
sudo firewall-cmd --reload
```

#### Bind Address Set to Localhost

If `bind_address` is set to `127.0.0.1`, the server only accepts local connections.

**Check in ArgusAI:**
1. Go to Settings > HomeKit > Diagnostics
2. Look at "Network Binding" - should show `0.0.0.0:51826`

**Fix:** The connectivity test will flag this. Update your HomeKit configuration to use `0.0.0.0` as the bind address.

#### Previous Pairing Data Conflicts

If you've previously paired and reset, stale pairing data may cause issues.

**Solution:**
1. Go to Settings > HomeKit
2. Click "Reset Pairing"
3. Remove ArgusAI from Apple Home app (if present)
4. Re-pair with the new code

### 3. Accessories Show "No Response"

**Symptoms:**
- Bridge paired successfully
- Sensors show "No Response" in Home app

**Causes & Solutions:**

#### HomeKit Bridge Stopped

Check if the bridge is still running:
1. Go to Settings > HomeKit
2. Verify status shows "Running" (green badge)

If stopped, toggle "Enable HomeKit" off and back on.

#### Network Change

If the server's IP changed, Home app may lose connection.

**Solution:**
Reset the HomeKit pairing and re-add to Home app.

#### Docker Container Network Mode

If using bridge network mode in Docker, the container IP may not be reachable from iOS devices.

**Solution:** Use `network_mode: host` or ensure proper port forwarding.

### 4. Events Not Triggering in Home App

**Symptoms:**
- Bridge running and paired
- Motion detected in ArgusAI
- Home app automations don't trigger

**Causes & Solutions:**

#### Check Last Event Delivery

1. Go to Settings > HomeKit > Diagnostics
2. Look at "Last Event Delivery" section
3. Verify events show "Delivered" status

#### Home App Automation Settings

Ensure automations are properly configured in Apple Home app:
1. Open Home app > Automations
2. Verify triggers are set for ArgusAI sensors
3. Check if automations are enabled

#### Connected Clients

Check "Connected Clients" in diagnostics. If 0 when Home app should be connected:
1. Force-quit Home app on iOS
2. Re-open and wait for connection
3. Check diagnostics again

## Network Configuration Reference

### Required Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 51826 | TCP | HAP server (configurable) |
| 5353 | UDP | mDNS discovery (Bonjour/Avahi) |

### mDNS Multicast

mDNS uses multicast address `224.0.0.251` on port 5353. This must be allowed through any firewalls between ArgusAI and iOS devices.

### Recommended Bind Address

Use `0.0.0.0` to bind to all interfaces, or specify a specific network interface IP if you want to restrict access.

## Getting Additional Help

### Diagnostic Logs

1. Go to Settings > HomeKit > Diagnostics
2. Review recent logs for errors
3. Filter by category: lifecycle, pairing, event, network, mdns

### Log Levels

- **Debug**: Detailed operational info
- **Info**: Normal operations
- **Warning**: Potential issues (yellow)
- **Error**: Failures (red)

### Collecting Debug Information

When reporting issues, include:
1. Connectivity test results
2. Recent diagnostic logs (filtered by errors/warnings)
3. Your deployment method (native, Docker, etc.)
4. Operating system and version
5. Network configuration (VM, Docker network mode, etc.)

## Quick Checklist

Before seeking help, verify:

- [ ] HomeKit is enabled and running (green "Running" badge)
- [ ] Avahi/Bonjour daemon is running
- [ ] Port 51826 (TCP) is open in firewall
- [ ] Port 5353 (UDP/mDNS) is allowed
- [ ] Bind address is `0.0.0.0` (not `127.0.0.1`)
- [ ] iOS device is on same network as ArgusAI
- [ ] "Test Discovery" shows all green checks
