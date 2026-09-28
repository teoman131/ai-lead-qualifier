# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-09-28
### Added
- **Multi-Tenant Dynamic Routing**: Support for `?chat_id=` and `&company_name=` query parameters in webhooks.
- Multi-client architecture allowing a single backend instance to serve multiple independent businesses.

## [1.3.0] - 2026-09-26
### Added
- **1-Tap Messaging Direct Actions**: Inline keyboard buttons for WhatsApp (`wa.me`), Telegram (`t.me`), and Gmail compose.
- Built-in interactive Tailwind CSS demo sandbox at `/demo`.
- Automated phone number sanitization to international E.164 digits-only format.

## [1.2.0] - 2026-09-25
### Added
- Universal webhook catcher endpoint `/api/v1/webhook/form` supporting Tilda, WordPress, and standard HTML forms.
- Background asynchronous dispatch pipeline to Google Sheets CRM webhooks.

## [1.0.0] - 2026-09-24
### Initial Release
- Core FastAPI microservice architecture.
- BANT heuristic scoring engine (Budget, Authority, Need, Timeline).
- Personalized sales outreach draft generation.
- Production Telegram Bot API alert formatting.
