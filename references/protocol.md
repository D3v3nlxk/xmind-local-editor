# Xmind assistant: observed protocol

Static inspection of `/Applications/Xmind.app/Contents/Resources/app.asar`, package version 27.01.05085, build 202610201924. No live requests, credentials, subscriptions, or application files were modified. REA compiled runtime was unavailable; these are shell-derived static observations, not REA Evidence records.

## Network

`renderer/2145.js` module contains the Athena client. Base URL is `https://app.xmind.cn` for serviceRegion cn, otherwise `https://app.xmind.com`.

- POST `/api/athena/chatbot`: request and SSE response.
- GET `/api/athena/chatbot/models`: available models.
- `/api/athena/chat-sessions/{fileId}` and `/{sessionId}`: list/create/read/update/delete sessions, with separate clear operation.
- `/api/athena/chatbot/{sessionId}/status` and `/stop`: execution status and cancellation.
- Headers include fwt (authentication credential), X-Request-Id, X-Device-Id and X-Xmind-User-Agent. Never copy account credentials to a helper or report.
- Recognized SSE events: session, session_name, thinking_delta, text_delta, tool_start, tool_end, sub_agent_progress, compaction_start, compaction_end, error, done.

Request builder `Uo` includes message, fileId, sessionId, sheetId, sheetSwitched, selectedTopicIds, hasZoneSelection, attachments, askMode, thinkingLevel, modelId, clientStateVector, clientProtocolVersion and clientCapabilities. It sends localDocument when available; otherwise teamId. Advertised protocol version is 1; the patch handler accepts versions up to 2.

## Obtaining document context and applying results

`prepareRequest` serializes local document context before the request. The editor dependencies expose serializeDocument(document.value), deserializeDocument(content, metadata), and changeDoc. Therefore the observed local-file path sends context to the remote service; get_sheet appearing in a tool label does not prove a server callback to a local HTTP endpoint.

The tool display catalog includes get_sheet, edit_topics, create_mindmap, add_sheet, set_topic_properties, manage_relationship, fold_topics, load_skill and call_skill_function. These names are observations, not a recovered public tool schema. Xmind's load_skill is not evidence of compatibility with Codex SKILL.md.

Tool results can carry documentPatch, patchElements.full/shallow, focusSheetId, protocolVersion, rolledBack, and clientAction. Client actions advertised include rename_file, set_topic_decoration, switch_sheet and resize_zone_to_fit.

Patch application is queued. It binds to currentFileId, checks the active turn, rejects unsupported protocol versions and rolled-back results, and uses a 30-second application timeout. Tool IDs anchor undo checkpoints. Cloud document application uses applyDocumentPatchRaw and checks unresolvedIds. The local path uses document serialization/deserialization and changeDoc; topic image changes use mutable topic attributes. A Yjs-backed document adapter exports state vectors for the cloud path.

## Practical consequence

No public local agent endpoint or supported plugin interface was established by this inspection. The shipped remote protocol and internal editor functions cannot be invoked merely by writing a Codex skill. The bundled helper instead edits saved modern Xmind archives with its own deliberately small operation schema. It does not emulate Athena, forward tokens, unlock subscriptions, synchronize open documents, or claim full internal patch compatibility.

## Verification scope

A bundled modern mind_map.xmind template contains content.json, metadata.json, manifest.json, thumbnail and a legacy content.xml compatibility warning. The helper was exercised on a copy of this template for topic rename, child addition and sheet rename; unrelated ZIP payload preservation, digest mismatch and overwrite rejection were checked. This does not establish GUI rendering, arbitrary document compatibility, or live assistant behavior.
