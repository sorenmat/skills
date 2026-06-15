# Buffer Publishing Reference

Use this reference when the user asks to post, schedule, queue, draft, or otherwise prepare Instagram publishing through Buffer.

## Current Docs Check

Before making live Buffer API calls, check the current Buffer developer docs at `https://developers.buffer.com`, especially:

- Authentication
- Posts & Scheduling
- Hosting Media
- Create Video Post / Create Image Post examples

The Buffer API changes over time. Prefer the current docs over examples in this skill if they differ.

## Authentication

- Use `BUFFER_API_KEY` or an equivalent secret store for account API keys.
- Send the token as `Authorization: Bearer ...` to `https://api.buffer.com`.
- Never hardcode API keys in source, prompts, post drafts, logs, screenshots, or committed files.
- OAuth is appropriate for multi-user apps; account API keys are appropriate for the user's own Buffer account automation.

## Channel Selection

Confirm the Buffer channel is an Instagram channel before scheduling. If querying channels, inspect the `service` value and choose the intended Instagram profile.

Useful fields to ask for or resolve:

- Organization ID, when listing posts or channels by organization.
- Channel ID for the connected Instagram profile.
- Instagram post type, when relevant: feed post, Story, Reel, or other currently supported Buffer/Instagram metadata.
- Desired mode: `addToQueue` or `customScheduled`.
- Scheduled time in UTC for `customScheduled`.

For Instagram-specific post types, first check the current Buffer `PostInputMetaData` reference and include only the metadata fields supported for the connected Instagram channel.

Known Instagram metadata shape from the current GraphQL schema:

```graphql
metadata: {
  instagram: {
    type: post
    shouldShareToFeed: true
  }
}
```

The `type` enum includes `post`, `reel`, `story`, and `carousel` among other network-specific values. Use `post` for a regular Instagram feed post.

## Media Requirements

Buffer does not upload binary files through the post API. Host images and videos elsewhere and pass public, direct, stable HTTPS URLs in the `assets` array.

Validate media URLs before using them:

- Open in a private browser or make an unauthenticated request.
- Confirm the URL points directly to the file, not a preview page.
- Avoid expiring signed URLs for scheduled posts.
- Keep the file reachable until Buffer publishes the post.

Video assets use a `video` entry and may include `thumbnailUrl`. Image assets use an `image` entry.

## Scheduling

For queued posts, use:

```graphql
mode: addToQueue
schedulingType: automatic
```

For exact scheduling, use:

```graphql
mode: customScheduled
schedulingType: automatic
dueAt: "2026-03-10T15:00:00.000Z"
```

Always convert the user's intended time zone to UTC and show both the user's local time and UTC before asking for approval.

## Post Mutation Shape

Use `createPost` and include both success and error branches in the response.

```graphql
mutation CreatePost {
  createPost(
    input: {
      text: "Caption text here"
      channelId: "instagram_channel_id"
      schedulingType: automatic
      mode: addToQueue
      assets: [{ video: { url: "https://example.com/video.mp4" } }]
    }
  ) {
    ... on PostActionSuccess {
      post {
        id
        text
        dueAt
        assets {
          source
        }
      }
    }
    ... on MutationError {
      message
    }
  }
}
```

## Approval Boundary

Do not create, schedule, or edit a live Buffer post until the user explicitly approves the exact target channel, caption, media URL, and schedule in the current turn. If approval is missing, provide a ready-to-run mutation or manual Buffer steps instead.
