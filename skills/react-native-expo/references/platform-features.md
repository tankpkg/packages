# Platform Features

Sources: Expo SDK documentation (2025-2026), Apple Developer documentation, Android Developer documentation, expo-notifications docs, React Native deep linking guide

Covers: push notifications (expo-notifications with FCM/APNs), deep linking and universal links, biometric authentication, camera and media handling, file system operations, splash screen configuration, and app icon setup.

## Push Notifications

### expo-notifications Setup

```bash
npx expo install expo-notifications expo-device expo-constants
```

Configure in `app.json`:

```json
{
  "expo": {
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/notification-icon.png",
          "color": "#ffffff",
          "sounds": ["./assets/notification-sound.wav"],
          "android": {
            "useNextNotificationsApi": true
          }
        }
      ]
    ],
    "android": {
      "googleServicesFile": "./google-services.json"
    },
    "ios": {
      "bundleIdentifier": "com.example.myapp"
    }
  }
}
```

### Registration and Token

```typescript
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

async function registerForPushNotifications(): Promise<string | null> {
  if (!Device.isDevice) {
    console.warn('Push notifications require a physical device');
    return null;
  }

  // Check existing permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    return null;
  }

  // Android: create notification channel
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'Default',
      importance: Notifications.AndroidImportance.MAX,
      vibrationPattern: [0, 250, 250, 250],
    });
  }

  // Get Expo push token
  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const token = await Notifications.getExpoPushTokenAsync({ projectId });
  return token.data;
}
```

### Handling Notifications

```typescript
import { useEffect, useRef } from 'react';
import * as Notifications from 'expo-notifications';
import { router } from 'expo-router';

export function useNotificationHandlers() {
  const notificationListener = useRef<Notifications.EventSubscription>();
  const responseListener = useRef<Notifications.EventSubscription>();

  useEffect(() => {
    // Notification received while app is foregrounded
    notificationListener.current =
      Notifications.addNotificationReceivedListener((notification) => {
        const data = notification.request.content.data;
        console.log('Received:', data);
      });

    // User tapped on notification
    responseListener.current =
      Notifications.addNotificationResponseReceivedListener((response) => {
        const data = response.notification.request.content.data;
        if (data.screen) {
          router.push(data.screen as string);
        }
      });

    return () => {
      notificationListener.current?.remove();
      responseListener.current?.remove();
    };
  }, []);
}
```

### Sending from Server (Expo Push API)

```typescript
// Server-side (Node.js)
async function sendPushNotification(expoPushToken: string) {
  const message = {
    to: expoPushToken,
    sound: 'default',
    title: 'New Message',
    body: 'You have a new message from Alice',
    data: { screen: '/chat/123' },
    badge: 1,
    categoryId: 'message',
  };

  await fetch('https://exp.host/--/api/v2/push/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(message),
  });
}
```

### Notification Architecture

| Component | iOS | Android |
|-----------|-----|---------|
| Push service | APNs (Apple Push Notification service) | FCM (Firebase Cloud Messaging) |
| Token type | Expo push token (wraps both) | Expo push token (wraps both) |
| Background delivery | Silent notifications via `content-available` | Data messages via FCM |
| Channels | Not applicable | Required (Android 8+) |
| Rich media | Notification Service Extension | BigPictureStyle, BigTextStyle |

## Deep Linking

### URL Scheme (Development)

Configure a custom URL scheme in `app.json`:

```json
{
  "expo": {
    "scheme": "myapp"
  }
}
```

Links like `myapp://users/123` map to `app/users/[id].tsx` automatically with Expo Router.

### Universal Links (Production)

#### iOS Associated Domains

```json
{
  "expo": {
    "ios": {
      "associatedDomains": ["applinks:example.com"]
    }
  }
}
```

Host the Apple App Site Association file at `https://example.com/.well-known/apple-app-site-association`:

```json
{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appID": "TEAM_ID.com.example.myapp",
        "paths": ["/users/*", "/posts/*", "/invite/*"]
      }
    ]
  }
}
```

#### Android App Links

```json
{
  "expo": {
    "android": {
      "intentFilters": [
        {
          "action": "VIEW",
          "autoVerify": true,
          "data": [
            {
              "scheme": "https",
              "host": "example.com",
              "pathPrefix": "/users"
            }
          ],
          "category": ["BROWSABLE", "DEFAULT"]
        }
      ]
    }
  }
}
```

Host Digital Asset Links at `https://example.com/.well-known/assetlinks.json`:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.example.myapp",
    "sha256_cert_fingerprints": ["SHA256_FINGERPRINT"]
  }
}]
```

### Handling Incoming Links

Expo Router handles deep links automatically. For manual handling:

```typescript
import * as Linking from 'expo-linking';
import { useEffect } from 'react';

function useDeepLink() {
  useEffect(() => {
    // Handle link that opened the app
    Linking.getInitialURL().then((url) => {
      if (url) handleDeepLink(url);
    });

    // Handle links while app is running
    const subscription = Linking.addEventListener('url', ({ url }) => {
      handleDeepLink(url);
    });

    return () => subscription.remove();
  }, []);
}
```

## Biometric Authentication

```bash
npx expo install expo-local-authentication
```

```typescript
import * as LocalAuthentication from 'expo-local-authentication';

async function authenticateWithBiometrics(): Promise<boolean> {
  // Check hardware support
  const compatible = await LocalAuthentication.hasHardwareAsync();
  if (!compatible) return false;

  // Check enrolled biometrics
  const enrolled = await LocalAuthentication.isEnrolledAsync();
  if (!enrolled) return false;

  // Check available types
  const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
  // types: FINGERPRINT, FACIAL_RECOGNITION, IRIS

  // Authenticate
  const result = await LocalAuthentication.authenticateAsync({
    promptMessage: 'Verify your identity',
    cancelLabel: 'Cancel',
    disableDeviceFallback: false,  // Allow PIN/pattern fallback
    fallbackLabel: 'Use passcode',
  });

  return result.success;
}
```

## Camera and Media

### expo-image (Display)

```bash
npx expo install expo-image
```

```typescript
import { Image } from 'expo-image';

function Avatar({ uri }: { uri: string }) {
  return (
    <Image
      source={{ uri }}
      style={{ width: 80, height: 80, borderRadius: 40 }}
      contentFit="cover"
      placeholder={{ blurhash: 'L6PZfSi_.AyE_3t7t7R**0o#DgR4' }}
      transition={200}
      cachePolicy="memory-disk"
    />
  );
}
```

`expo-image` advantages over `<Image>`:
- Disk and memory caching built-in
- BlurHash/ThumbHash placeholders
- Animated transitions
- SVG support
- Better performance (native image loading)

### expo-camera

```typescript
import { CameraView, useCameraPermissions } from 'expo-camera';

function Scanner() {
  const [permission, requestPermission] = useCameraPermissions();

  if (!permission?.granted) {
    return <Button title="Grant Camera" onPress={requestPermission} />;
  }

  return (
    <CameraView
      style={{ flex: 1 }}
      facing="back"
      barcodeScannerSettings={{ barcodeTypes: ['qr', 'ean13'] }}
      onBarcodeScanned={({ data }) => console.log('Scanned:', data)}
    />
  );
}
```

### expo-image-picker

```typescript
import * as ImagePicker from 'expo-image-picker';

async function pickImage() {
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ['images'],
    allowsEditing: true,
    aspect: [1, 1],
    quality: 0.8,
  });

  if (!result.canceled) {
    return result.assets[0].uri;
  }
  return null;
}
```

## Splash Screen

```json
{
  "expo": {
    "splash": {
      "image": "./assets/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#ffffff",
      "dark": {
        "image": "./assets/splash-dark.png",
        "backgroundColor": "#000000"
      }
    }
  }
}
```

Control splash screen programmatically:

```typescript
import * as SplashScreen from 'expo-splash-screen';

SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    async function prepare() {
      await loadFonts();
      await loadInitialData();
      setReady(true);
      await SplashScreen.hideAsync();
    }
    prepare();
  }, []);

  if (!ready) return null;
  return <Stack />;
}
```

## App Icons

Configure in `app.json` with `icon` (1024x1024 PNG) at root level. Add `ios.icon.dark` and `ios.icon.tinted` for iOS dark mode icons. Use `android.adaptiveIcon` with `foregroundImage`, `backgroundImage`, and `monochromeImage` for Android adaptive icons.

| Platform | Size | Format | Notes |
|----------|------|--------|-------|
| iOS | 1024x1024 | PNG (no alpha) | Single image, system generates sizes |
| Android adaptive | 108x108dp foreground | PNG with alpha | Foreground on background layer |
| Expo | 1024x1024 | PNG | Used as base for both platforms |

## File System

Use `expo-file-system` for file operations. Key APIs: `readAsStringAsync`, `writeAsStringAsync`, `downloadAsync`, `getInfoAsync`.

| Directory | Purpose | Persists |
|-----------|---------|----------|
| `FileSystem.documentDirectory` | User data, app files | Yes (backed up) |
| `FileSystem.cacheDirectory` | Temporary files, downloads | No (OS may clear) |
| `FileSystem.bundleDirectory` | Read-only bundled assets | Yes (read-only) |
