import 'package:flutter/foundation.dart' show kIsWeb;

/// Returns the backend API base URL.
/// - In production (web deployed alongside backend): uses relative path (same origin)
/// - In development (flutter dev server): uses localhost:8000
String getBackendUrl() {
  if (kIsWeb) {
    // When served from the same origin as backend, use empty string (relative URLs)
    // When running flutter dev server on :3000, backend is on :8000
    return const bool.fromEnvironment('PRODUCTION', defaultValue: false)
        ? ''  // Same origin — relative paths
        : 'http://localhost:8000';
  }
  return 'http://localhost:8000';
}

final String backendUrl = getBackendUrl();
