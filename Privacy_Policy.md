# etan bot Privacy Policy

**Effective Date**: 2026-08-08
**Bot Name**: etan bot (etan bot#2688)
**Developer**: etangaming123
**Contact**:
email: me [at] etangaming [dot] xyz
discord: @etangaming123

## 1. Introduction
This Privacy Policy ("Policy") describes how etan bot ("the Bot", "we", "us", or "our") collects, uses, stores, and protects your personal information when you use our services. By using the Bot, you consent to the collection, use, and handling of your information as described in this Policy.
**If you do not agree with this Policy, you must not use the Bot.**
This policy only describes what etan bot collects, not what Discord collects.

## 2. Information We Collect

### 2.1. Technical Information
When you interact with the Bot, we only collect technical information necessary for the Bot to function properly. These may include:

- **Error Logs**: When a command fails, a traceback of the error is generated. This traceback may contain technical details about the command execution, but it does not include any personally identifiable information.

### 2.2. User-Provided Information
The Bot serves optional features that may require you to provide certain information. This information is only collected if you choose to use those features. Examples of user-provided information include:

- **Profile Information**: If you choose to use the profile editor feature, you may provide information such as your "About Me" description and social media links. This is publicly visible to other users when they view your profile through the Bot.
- **KOKO Amusement Card Linking**: If you decide to use the KOKO Amusement Card linking feature, you may provide information such as your card token.
- **Gimmicks (Drawings & Messages)**: If you choose to use the Gimmicks feature (`/etanbot-gimmicks-send`), we store the drawing code or message text, your Discord user ID (as the sender), the recipient's Discord user ID, whether you chose to send it anonymously, and a timestamp. This is used to deliver your gimmick to the recipient and to allow moderation if the content is reported. **Your Discord user ID is always retained internally, even if you choose to send a gimmick anonymously** — the anonymity setting only affects what the recipient sees, not what the Bot stores.

User provided information can be deleted at any time via the Bot commands, with the exception of Gimmicks moderation records and hashed ban records, which are retained for safety purposes (see Section 6, Data Retention).

**We do not collect any personally identifiable information such as your real names, physical addresses, or any other information that can be used to identify you personally**, unless given directly by you (such as in the case of customising your profile).
(don't do that by the way!)

## 3. How We Use Your Information
We use the information we collect for the following purposes:

- **Service Provision**: To use various services, such as the KOKO Amusement Card linking feature, and built in profiles.
- **Error Diagnosis**: To diagnose and fix issues with the Bot, using error logs to identify and resolve technical problems, such as in the case where you run a command and it fails.

**We do not use your information for any advertising, marketing, or any other commercial purposes.**

## 4. How We Store Your Information
**WARNING!!! Your information is stored as .json files on the machine running etan bot.** The machine running etan bot is not shared with any third parties, and only the developer has access to this machine.
If you are banned from using etan bot, a hash of your user ID will be stored in a .json file on the machine running etan bot, and this hash will be used to prevent you from using etan bot again. This is a hash and cannot be reversed to obtain your user ID. It is only used for the purpose of banning users from using etan bot.
Unlike ban records, information related to the Gimmicks feature (including the sender's real Discord user ID) is stored in plain, unhashed form. This is intentional: it's the only way abuse of the anonymous-sending feature can be traced back to the user responsible and acted on. This information is not made public and is only accessible to the developer/moderation team.

## 5. How We Share Your Information
**We do not share your information with any third parties.**
We may disclose information only in the following limited circumstances:

- **Legal Compliance**: If we are required to do so by law or in response to valid requests by public authorities (e.g., a court or a government agency).
- **Report Handling**: If a Gimmick you sent is reported by its recipient, details of that report (including your Discord user ID, the content, and the recipient) are sent to a private Discord channel accessible only to the developer/moderation team, for the purpose of investigating the report.

## 6. Data Retention
Various types of information are retained for different periods of time, depending on the nature of the information and the purposes for which it was collected.
Generally, we retain user-provided information until you choose to delete it via the Bot commands. Error logs are printed within the bot console and will be cleared out periodically.
Gimmicks you send remain in the recipient's inbox until they choose to dismiss them. Separately, a permanent moderation record (sender ID, recipient ID, gimmick type, and timestamp, not the drawing/message content itself) is retained indefinitely for safety purposes, and is not deleted even after the recipient dismisses the gimmick or either user deletes their other data.

## 7. Your Rights and Choices
At any point, you may:

- **Access Your Information**: Request access to the information we have about you.
- **Update Your Information**: Update or correct any information we have about you.
- **Delete Your Information**: Request that we delete any information we have about you.

We will respond to verifiable requests from users who wish to exercise their data protection rights. Please contact us with the given contact information at the top of this page.
Note: for safety reasons, the moderation record described in Section 6 (Data Retention) - sender/recipient IDs, gimmick type, and timestamps - is not subject to deletion requests, consistent with how banned-user records are retained.

## 8. Children's Privacy
The Bot is not intended for use by children under the age of digital consent in their jurisdiction. We do not knowingly collect personal information from children. If we become aware that we have collected personal information from a child, we will take steps to delete that information as soon as possible. If you become aware that a child has provided us with personal information, please contact us using the contact information provided at the top of this page, and we will take steps to permanently delete such information.

## 9. Third-Party Services
The bot may contain links to external websites or services. We are not responsible for the privacy practices or content of these third-party sites. We encourage you to review the privacy policies of any external sites you visit.
Moreover, the bot may use third-party services (such as KOKO Amusement Card linking, rngdle information) that have their own privacy policies. We recommend reviewing the privacy policies of these third-party services to understand how they handle your information.

## 10. Changes to This Privacy Policy
We may update this Privacy Policy from time to time. We will notify you of any changes via etan bot support server.. You are advised to review this Privacy Policy periodically for any changes. Changes to this Privacy Policy are effective when they are posted on this page. Your continued use of the Bot after any such change constitutes your acceptance of the updated Privacy Policy.

## 11. Contact Us
If you have any questions about this Privacy Policy, please contact us at the provided contact information at the top of this page.
