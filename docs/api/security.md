# Security API Documentation

## Overview
This document describes the security-related endpoints for user authentication, authorization, and account security.

## Authentication

### Login
`POST /api/v1/auth/login`

Log in with username/email and password. Returns access and refresh tokens.

**Request Body:**
```json
{
    "username": "string",
    "password": "string"
}
```

**Response:**
```json
{
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer"
}
```

### Refresh Token
`POST /api/v1/auth/refresh`

Get new access token using refresh token.

**Request Body:**
```json
{
    "refresh_token": "string"
}
```

**Response:**
```json
{
    "access_token": "string",
    "refresh_token": "string",
    "token_type": "bearer"
}
```

### Logout
`POST /api/v1/auth/logout`

Log out and invalidate refresh token.

**Request Body:**
```json
{
    "refresh_token": "string"
}
```

**Response:**
```json
{
    "message": "Successfully logged out"
}
```

### Logout All Sessions
`POST /api/v1/auth/logout-all`

Log out from all sessions.

**Response:**
```json
{
    "message": "Successfully logged out from all sessions"
}
```

## Two-Factor Authentication (2FA)

### Set Up 2FA
`POST /api/v1/security/2fa/setup`

Initialize 2FA setup. Returns secret and QR code.

**Response:**
```json
{
    "secret": "string",
    "uri": "string",
    "qr_code": "bytes",
    "backup_codes": ["string"]
}
```

### Verify 2FA
`POST /api/v1/security/2fa/verify`

Verify and activate 2FA.

**Request Body:**
```json
{
    "code": "string"
}
```

**Response:**
```json
{
    "message": "2FA activated successfully"
}
```

### Disable 2FA
`POST /api/v1/security/2fa/disable`

Disable 2FA for account.

**Response:**
```json
{
    "message": "2FA disabled successfully"
}
```

## Password Reset

### Request Reset
`POST /api/v1/security/password/reset-request`

Request password reset email.

**Request Body:**
```json
{
    "email": "string"
}
```

**Response:**
```json
{
    "message": "If email exists, reset instructions will be sent"
}
```

### Reset Password
`POST /api/v1/security/password/reset-verify`

Reset password using token.

**Request Body:**
```json
{
    "token": "string",
    "new_password": "string"
}
```

**Response:**
```json
{
    "message": "Password reset successfully"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
    "detail": "Error message"
}
```

### 401 Unauthorized
```json
{
    "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
    "detail": "Not enough privileges"
}
```

### 422 Validation Error
```json
{
    "detail": [
        {
            "loc": ["string"],
            "msg": "string",
            "type": "string"
        }
    ]
}
```

## Security Best Practices

1. **Token Management**
   - Access tokens expire in 15 minutes
   - Refresh tokens expire in 7 days
   - Store tokens securely (HttpOnly cookies)
   - Never expose tokens in URLs or logs

2. **Password Requirements**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, and special characters
   - Checked against common passwords
   - Strength evaluated using zxcvbn

3. **Rate Limiting**
   - 5 login attempts per minute
   - 3 password reset requests per hour
   - 10 2FA verification attempts per hour

4. **Session Security**
   - Sessions expire after 24 hours
   - Invalidated on password change
   - Can be terminated remotely
   - Tracks IP and user agent

5. **2FA Security**
   - TOTP-based (RFC 6238)
   - 8 backup codes
   - QR code for easy setup
   - Required for sensitive operations
