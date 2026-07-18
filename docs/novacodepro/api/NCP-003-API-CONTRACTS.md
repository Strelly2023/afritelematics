# NCP-003 API Contracts

Version: 1.0

All routes are served under `/v1/novacodepro`.

Workspace routes

- `GET /workspaces`
- `POST /workspaces`
- `GET /workspaces/{workspace_id}`
- `PATCH /workspaces/{workspace_id}`
- `POST /workspaces/{workspace_id}/select`
- `GET /workspaces/{workspace_id}/members`
- `POST /workspaces/{workspace_id}/members`
- `DELETE /workspaces/{workspace_id}/members/{member_id}`
- `GET /workspaces/{workspace_id}/activity`
- `GET /workspaces/{workspace_id}/tasks`
- `GET /workspaces/{workspace_id}/approvals`
- `GET /workspaces/{workspace_id}/favorites`
- `POST /workspaces/{workspace_id}/favorites`
- `DELETE /workspaces/{workspace_id}/favorites/{favorite_id}`
- `GET /workspaces/{workspace_id}/notifications`
- `PATCH /workspaces/{workspace_id}/settings`

Project routes

- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `POST /projects/{project_id}/archive`
- `POST /projects/{project_id}/restore`
- `GET /projects/{project_id}/activity`
- `GET /projects/{project_id}/members`
- `POST /projects/{project_id}/members`
- `DELETE /projects/{project_id}/members/{member_id}`
- `GET /projects/{project_id}/milestones`
- `POST /projects/{project_id}/milestones`
- `GET /projects/{project_id}/milestones/{milestone_id}`
- `PATCH /projects/{project_id}/milestones/{milestone_id}`
- `DELETE /projects/{project_id}/milestones/{milestone_id}`
- `GET /projects/{project_id}/work-items`
- `POST /projects/{project_id}/work-items`
- `GET /projects/{project_id}/work-items/{work_item_id}`
- `PATCH /projects/{project_id}/work-items/{work_item_id}`
- `POST /projects/{project_id}/work-items/{work_item_id}/assign`
- `POST /projects/{project_id}/work-items/{work_item_id}/transition`
- `DELETE /projects/{project_id}/work-items/{work_item_id}`
- `GET /projects/{project_id}/risks`
- `POST /projects/{project_id}/risks`
- `PATCH /projects/{project_id}/risks/{risk_id}`
- `GET /projects/{project_id}/roadmap`

Request routes

- `GET /requests`
- `POST /requests`
- `GET /requests/{request_id}`
- `PATCH /requests/{request_id}`
- `POST /requests/{request_id}/submit`
- `POST /requests/{request_id}/transition`
- `POST /requests/{request_id}/archive`
- `GET /requests/{request_id}/history`
- `GET /requests/{request_id}/assignments`
- `POST /requests/{request_id}/assignments`
- `DELETE /requests/{request_id}/assignments/{assignment_id}`
- `GET /requests/{request_id}/comments`
- `POST /requests/{request_id}/comments`
- `PATCH /requests/{request_id}/comments/{comment_id}`
- `DELETE /requests/{request_id}/comments/{comment_id}`
- `GET /requests/{request_id}/attachments`
- `POST /requests/{request_id}/attachments`
- `GET /requests/{request_id}/attachments/{attachment_id}`
- `DELETE /requests/{request_id}/attachments/{attachment_id}`

Notification routes

- `GET /notifications`
- `PATCH /notifications/{notification_id}/read`
- `POST /notifications/read-all`

Contract rules

- Workspace selection is server-authoritative.
- Project creation requires an idempotency key.
- Archived projects and requests reject invalid mutations.
- Cross-tenant access is forbidden.
- Attachments must use the allowlist MIME types and are quarantined when malware scanning cannot be confirmed.
- Errors return structured payloads with `code`, `message`, and `retryable` where applicable.
