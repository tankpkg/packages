# EAS Build, Submit, and Update

Sources: Expo EAS Documentation (2025-2026), Expo blog (EAS Workflows), React Native deployment guides

Covers: EAS Build profiles and eas.json configuration, development builds, EAS Submit for app stores, EAS Update for OTA delivery, code signing, CI/CD workflows, and Expo Go vs development builds.

## EAS Build

EAS Build compiles native binaries in the cloud. Configure build profiles in `eas.json` at the project root.

### eas.json Configuration

```json
{
  "cli": {
    "version": ">= 15.0.0",
    "appVersionSource": "remote"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "channel": "development",
      "ios": {
        "simulator": true
      }
    },
    "preview": {
      "distribution": "internal",
      "channel": "preview",
      "android": {
        "buildType": "apk"
      }
    },
    "production": {
      "channel": "production",
      "autoIncrement": true
    }
  },
  "submit": {
    "production": {
      "ios": {
        "ascAppId": "1234567890",
        "appleTeamId": "XXXXXXXXXX"
      },
      "android": {
        "serviceAccountKeyPath": "./google-services.json",
        "track": "internal"
      }
    }
  }
}
```

### Build Profiles

| Profile | Purpose | Distribution | Command |
|---------|---------|-------------|---------|
| `development` | Local dev with dev client | Internal / simulator | `eas build -p ios --profile development` |
| `preview` | QA testing, stakeholder review | Internal (ad hoc) | `eas build -p all --profile preview` |
| `production` | App store submission | Store | `eas build -p all --profile production` |

### Build Commands

```bash
# Build for iOS simulator (development)
eas build -p ios --profile development

# Build for both platforms (production)
eas build -p all --profile production

# Build locally instead of cloud
eas build -p android --local

# View build status
eas build:list

# View build logs
eas build:view <BUILD_ID>
```

### Custom Native Code

Add native dependencies through config plugins without ejecting:

```json
{
  "expo": {
    "plugins": [
      ["expo-camera", { "cameraPermission": "Allow camera access for scanning" }],
      ["expo-location", { "locationAlwaysAndWhenInUsePermission": "Allow location" }],
      "./plugins/my-custom-plugin.js"
    ]
  }
}
```

Config plugins modify native project files during `npx expo prebuild`. Write custom plugins for native configuration:

```javascript
// plugins/my-custom-plugin.js
const { withAndroidManifest, withInfoPlist } = require('expo/config-plugins');

module.exports = function myPlugin(config, props) {
  config = withInfoPlist(config, (config) => {
    config.modResults.NSCameraUsageDescription = props.cameraMessage;
    return config;
  });

  config = withAndroidManifest(config, (config) => {
    const mainApp = config.modResults.manifest.application[0];
    mainApp.$['android:largeHeap'] = 'true';
    return config;
  });

  return config;
};
```

## Development Builds vs Expo Go

| Feature | Expo Go | Development Build |
|---------|---------|-------------------|
| Custom native code | Not supported | Fully supported |
| Config plugins | Not supported | Fully supported |
| Third-party native SDKs | Limited | Any SDK |
| Setup time | Instant (download app) | Requires build (~5-15 min) |
| New Architecture | Always enabled | Configurable |
| Push notification testing | Limited | Full support |
| Deep link testing | Limited | Full support |

Use Expo Go for learning and prototyping. Switch to development builds when adding native dependencies or config plugins.

### Creating a Development Build

```bash
# Install expo-dev-client
npx expo install expo-dev-client

# Build for device
eas build --profile development --platform ios

# Build for simulator
eas build --profile development --platform ios --local

# Start dev server
npx expo start --dev-client
```

## EAS Submit

Automate app store submissions directly from EAS builds.

### iOS App Store

```bash
# Submit latest production build
eas submit -p ios --latest --profile production

# Submit specific build
eas submit -p ios --id <BUILD_ID>

# Submit local binary
eas submit -p ios --path ./build/app.ipa
```

Prerequisites for iOS:
- Apple Developer account ($99/year)
- App Store Connect app ID configured
- ASC API key or Apple ID credentials in Expo account

### Google Play Store

```bash
# Submit to internal track
eas submit -p android --latest --profile production

# Submit to production track
eas submit -p android --latest --track production
```

Prerequisites for Android:
- Google Play Console account ($25 one-time)
- Service account JSON key with API access
- App created in Google Play Console

### Submission Tracks (Android)

| Track | Purpose | Review |
|-------|---------|--------|
| `internal` | Internal testers (up to 100) | No review |
| `alpha` | Closed testing | No review |
| `beta` | Open testing | Optional review |
| `production` | Public release | Full review |

## EAS Update (OTA)

Push JavaScript and asset changes without rebuilding native binaries. Updates bypass app store review.

### Setup

```bash
# Configure project for updates
eas update:configure

# This adds to app.json:
# "updates": { "url": "https://u.expo.dev/<PROJECT_ID>" }
# "runtimeVersion": { "policy": "appVersion" }
```

### Channels and Branches

| Concept | Purpose | Example |
|---------|---------|---------|
| Channel | Linked to build profiles | `production`, `preview` |
| Branch | Target for updates | `main`, `staging` |
| Runtime version | Compatibility gate | `1.0.0` (must match build) |

A channel points to a branch. A build checks its channel for updates. Updates are only applied if the runtime version matches.

### Publishing Updates

```bash
# Send update to production channel
eas update --channel production --message "Fix login button"

# Send update to specific branch
eas update --branch main --message "Fix login button"

# Send platform-specific update
eas update --channel production --platform ios

# List recent updates
eas update:list

# Rollback (republish previous update)
eas update:rollback --channel production
```

### Runtime Version Policies

```json
{
  "expo": {
    "runtimeVersion": {
      "policy": "appVersion"
    }
  }
}
```

| Policy | Behavior | When to Use |
|--------|----------|-------------|
| `appVersion` | Uses `version` from app.json | Simple apps, infrequent native changes |
| `nativeVersion` | Uses `ios.buildNumber` / `android.versionCode` | Precise native tracking |
| `fingerprint` | Hash of native project files | Maximum safety, auto-detects native changes |
| Custom string | Manual version string | Full manual control |

### Forcing Immediate Updates

By default, updates apply on the second launch. Force immediate updates with the Updates API:

```typescript
import * as Updates from 'expo-updates';

async function checkForUpdates() {
  if (__DEV__) return; // Skip in development

  const update = await Updates.checkForUpdateAsync();
  if (update.isAvailable) {
    await Updates.fetchUpdateAsync();
    await Updates.reloadAsync(); // Restart app with new update
  }
}
```

### Update Limitations

OTA updates can change:
- JavaScript/TypeScript code
- Static assets (images, fonts)
- Styles and layouts

OTA updates cannot change:
- Native modules (Swift, Kotlin, Objective-C, Java)
- Native SDK versions
- App permissions
- App binary configuration

When native code changes, create a new build with `eas build`.

## Code Signing

### iOS

EAS Build manages provisioning profiles and certificates automatically:

```bash
# Let EAS manage signing
eas credentials

# Configure in eas.json for manual control
{
  "build": {
    "production": {
      "ios": {
        "credentialsSource": "remote"  // or "local"
      }
    }
  }
}
```

| Credential | Purpose | Managed by EAS? |
|-----------|---------|-----------------|
| Distribution certificate | Sign app for store | Yes (recommended) |
| Provisioning profile | Link cert to app ID | Yes (recommended) |
| Push notification key | APNs authentication | Yes |
| ASC API key | Automated submission | Configure once |

### Android

```bash
# Generate keystore (EAS manages by default)
eas credentials --platform android

# Use existing keystore
{
  "build": {
    "production": {
      "android": {
        "credentialsSource": "local",
        "releaseChannel": "production"
      }
    }
  }
}
```

Store the upload keystore securely. Losing it means inability to update the app on Google Play.

## CI/CD with EAS Workflows

### Automated Build + Submit on Tag

```yaml
# .eas/workflows/production-release.yml
name: Production Release

on:
  push:
    tags: ['v*']

jobs:
  build_ios:
    name: Build iOS
    type: build
    params:
      platform: ios
      profile: production

  build_android:
    name: Build Android
    type: build
    params:
      platform: android
      profile: production

  submit_ios:
    name: Submit iOS
    needs: [build_ios]
    type: submit
    params:
      platform: ios
      profile: production

  submit_android:
    name: Submit Android
    needs: [build_android]
    type: submit
    params:
      platform: android
      profile: production
```

### Automated OTA on Push to Main

```yaml
# .eas/workflows/send-updates.yml
name: Send Updates

on:
  push:
    branches: ['main']

jobs:
  send_updates:
    name: Send OTA Update
    type: update
    params:
      channel: production
```

### GitHub Actions Alternative

Use `expo/expo-github-action@v8` with `eas-version: latest` and `EXPO_TOKEN` secret. Run `eas build --platform all --non-interactive --profile production` after `npm ci`.

## EAS Metadata

Manage app store listings with `eas metadata:pull` and `eas metadata:push`. Store configuration in `store.config.json` with per-locale title, subtitle, description, and keywords.

## Common Mistakes

| Mistake | Problem | Fix |
|---------|---------|-----|
| OTA update with native change | Update silently fails or crashes | Check runtime version; build new binary for native changes |
| Missing channel in eas.json | Updates never reach builds | Add `channel` to every build profile |
| Expo Go for production testing | Missing native modules, wrong behavior | Use development builds for anything beyond prototyping |
| Manual version bumps | Version conflicts, missed increments | Use `autoIncrement: true` in production profile |
| Losing Android keystore | Cannot update app on Play Store | Back up keystore; use EAS managed credentials |
| No runtime version policy | Incompatible updates sent to old builds | Set `runtimeVersion.policy` to `fingerprint` for safety |
