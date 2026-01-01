# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive error handling and logging throughout backend
- Async storage operations with aiofiles for better performance
- Rate limiting with slowapi (10 requests/minute default)
- Pydantic Settings for configuration validation
- HTTP connection pooling and HTTP/2 support
- Request cancellation and abort controllers in frontend
- React.memo optimizations for all components
- Proper error boundaries and user feedback
- Health check endpoint with detailed status
- Input validation and sanitization
- Structured logging with configurable levels
- Simple caching for title generation
- Retry functionality for failed requests

### Changed
- Replaced synchronous file I/O with async operations
- Migrated from complex useState to useReducer pattern
- Improved CORS configuration to be more restrictive
- Enhanced API client with proper timeout handling
- Optimized OpenRouter client with connection pooling
- Refactored state management to prevent mutations
- Added environment-based configuration

### Fixed
- Broad exception handling replaced with specific error types
- Memory leaks in streaming implementation
- Direct state mutations causing unnecessary re-renders
- Missing error boundaries and user feedback
- Security vulnerabilities in input validation
- Performance bottlenecks in file operations
- Resource leaks in HTTP clients

### Security
- Added conversation ID validation to prevent directory traversal
- Implemented proper input sanitization and validation
- Enhanced CORS configuration
- Added rate limiting to prevent abuse
- Improved error message sanitization

### Performance
- Added HTTP connection pooling with keep-alive
- Implemented async file operations
- Added React.memo and useCallback optimizations
- Reduced unnecessary re-renders
- Added simple caching layer
- Improved parallel query handling

## [1.0.0] - Previous Release
- Initial LLM Council implementation
- Basic 3-stage council process
- JSON file storage
- React frontend with streaming
